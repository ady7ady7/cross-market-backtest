"""
Position management with support for multiple SL/TP types.

Supports:
- Time-based SL/TP
- Percentage-based SL/TP
- Condition-based SL/TP
- R:R-based TP
- Partial position closing
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Callable
from datetime import datetime
from enum import Enum


class PositionSide(Enum):
    """Position direction"""
    LONG = "long"
    SHORT = "short"


class ExitType(Enum):
    """Exit reason types"""
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"
    TIME_BASED = "time_based"
    CONDITION_BASED = "condition_based"
    MANUAL = "manual"


@dataclass
class PositionConfig:
    """Configuration for position management"""
    # Risk per trade (% of account)
    risk_percent: float = 1.0

    # Stop Loss configurations
    sl_type: str = 'percent'  # 'percent', 'time', 'condition', 'price'
    sl_percent: Optional[float] = None  # e.g., 1.0 for 1%
    sl_price: Optional[float] = None  # Specific price level for SL
    sl_time_bars: Optional[int] = None  # Exit after N bars
    sl_condition: Optional[Callable] = None  # Custom exit condition

    # Take Profit configurations
    tp_type: str = 'rr'  # 'percent', 'rr', 'time', 'condition'
    tp_percent: Optional[float] = None  # e.g., 2.0 for 2%
    tp_rr_ratio: Optional[float] = None  # Risk:Reward ratio (e.g., 2.0 for 1:2)

    # Partial exits (list of tuples: (size_fraction, rr_ratio or price))
    partial_exits: List[tuple] = field(default_factory=list)  # e.g., [(0.5, 2.0), (0.5, 3.0)]


@dataclass
class Position:
    """
    Represents a single trading position.
    """
    # Identification
    id: str
    strategy_name: str

    # Entry details
    entry_time: datetime
    entry_price: float
    side: PositionSide
    size: float  # Position size in base currency
    initial_size: float  # Original size before partial exits

    # Risk management
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_amount: float = 0.0  # Dollar amount risked

    # Exit details
    exit_time: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_type: Optional[ExitType] = None

    # Tracking
    bars_held: int = 0
    current_price: float = 0.0
    highest_price: float = 0.0  # For longs
    lowest_price: float = float('inf')  # For shorts

    # Partial exits tracking
    partial_exit_history: List[Dict] = field(default_factory=list)

    def __post_init__(self):
        self.highest_price = self.entry_price
        self.lowest_price = self.entry_price
        self.current_price = self.entry_price

    @property
    def is_open(self) -> bool:
        """Check if position is still open"""
        return self.exit_time is None and self.size > 0

    @property
    def unrealized_pnl(self) -> float:
        """Calculate unrealized P&L"""
        if not self.is_open:
            return 0.0

        if self.side == PositionSide.LONG:
            return (self.current_price - self.entry_price) * self.size
        else:
            return (self.entry_price - self.current_price) * self.size

    @property
    def realized_pnl(self) -> float:
        """Calculate realized P&L"""
        if self.is_open:
            return 0.0

        if self.side == PositionSide.LONG:
            pnl = (self.exit_price - self.entry_price) * self.initial_size
        else:
            pnl = (self.entry_price - self.exit_price) * self.initial_size

        # Add partial exits P&L
        for exit_record in self.partial_exit_history:
            pnl += exit_record['pnl']

        return pnl

    @property
    def r_multiple(self) -> float:
        """Calculate R-multiple (P&L / Risk)"""
        if self.risk_amount == 0:
            return 0.0
        return self.realized_pnl / self.risk_amount

    def update_price(self, price: float):
        """Update current price and tracking metrics"""
        self.current_price = price
        self.highest_price = max(self.highest_price, price)
        self.lowest_price = min(self.lowest_price, price)

    def close(self, exit_time: datetime, exit_price: float, exit_type: ExitType):
        """Close the position"""
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.exit_type = exit_type

    def partial_close(self, exit_time: datetime, exit_price: float,
                     size_fraction: float, reason: str) -> float:
        """
        Close partial position.

        Args:
            exit_time: Exit timestamp
            exit_price: Exit price
            size_fraction: Fraction of position to close (0-1)
            reason: Reason for partial close

        Returns:
            P&L from partial exit
        """
        if size_fraction <= 0 or size_fraction > 1:
            raise ValueError("size_fraction must be between 0 and 1")

        exit_size = self.size * size_fraction
        self.size -= exit_size

        # Calculate P&L for this partial exit
        if self.side == PositionSide.LONG:
            pnl = (exit_price - self.entry_price) * exit_size
        else:
            pnl = (self.entry_price - exit_price) * exit_size

        # Record partial exit
        self.partial_exit_history.append({
            'time': exit_time,
            'price': exit_price,
            'size': exit_size,
            'pnl': pnl,
            'reason': reason
        })

        return pnl


class PositionManager:
    """
    Manages multiple positions with risk controls.
    """

    def __init__(self, initial_capital: float, max_total_risk_percent: float = 6.0):
        """
        Initialize position manager.

        Args:
            initial_capital: Starting account balance
            max_total_risk_percent: Maximum % of capital at risk across all open positions
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_total_risk_percent = max_total_risk_percent

        self.open_positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []

        self._next_position_id = 1

    @property
    def total_risk_amount(self) -> float:
        """Calculate total risk amount across all open positions"""
        return sum(pos.risk_amount for pos in self.open_positions.values())

    @property
    def total_risk_percent(self) -> float:
        """Calculate total risk as % of current capital"""
        return (self.total_risk_amount / self.current_capital) * 100

    @property
    def can_open_position(self) -> bool:
        """Check if we can open a new position without exceeding max risk"""
        return self.total_risk_percent < self.max_total_risk_percent

    def calculate_position_size(self, entry_price: float, stop_loss: float,
                               config: PositionConfig, side: PositionSide) -> tuple:
        """
        Calculate position size based on risk parameters.

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            config: Position configuration
            side: Position side (LONG/SHORT)

        Returns:
            Tuple of (position_size, risk_amount)
        """
        # Calculate risk per unit
        if side == PositionSide.LONG:
            risk_per_unit = entry_price - stop_loss
        else:
            risk_per_unit = stop_loss - entry_price

        if risk_per_unit <= 0:
            raise ValueError("Invalid stop loss: no risk defined")

        # Calculate dollar risk amount
        risk_amount = self.current_capital * (config.risk_percent / 100)

        # Calculate position size
        position_size = risk_amount / risk_per_unit

        return position_size, risk_amount

    def open_position(self, strategy_name: str, entry_time: datetime,
                     entry_price: float, side: PositionSide,
                     config: PositionConfig) -> Optional[Position]:
        """
        Open a new position.

        Returns:
            Position object or None if cannot open (risk limits)
        """
        # Check risk limits
        if not self.can_open_position:
            return None

        # Calculate stop loss
        if config.sl_type == 'percent':
            if side == PositionSide.LONG:
                stop_loss = entry_price * (1 - config.sl_percent / 100)
            else:
                stop_loss = entry_price * (1 + config.sl_percent / 100)
        elif config.sl_type == 'price':
            # Use specific price level for stop loss
            stop_loss = config.sl_price
        else:
            # For time-based or condition-based, use a default % for sizing
            stop_loss = entry_price * 0.99 if side == PositionSide.LONG else entry_price * 1.01

        # Calculate position size
        size, risk_amount = self.calculate_position_size(entry_price, stop_loss, config, side)

        # Calculate take profit
        take_profit = None
        if config.tp_type == 'percent':
            if side == PositionSide.LONG:
                take_profit = entry_price * (1 + config.tp_percent / 100)
            else:
                take_profit = entry_price * (1 - config.tp_percent / 100)
        elif config.tp_type == 'rr':
            risk = abs(entry_price - stop_loss)
            if side == PositionSide.LONG:
                take_profit = entry_price + (risk * config.tp_rr_ratio)
            else:
                take_profit = entry_price - (risk * config.tp_rr_ratio)

        # Create position
        position = Position(
            id=f"pos_{self._next_position_id}",
            strategy_name=strategy_name,
            entry_time=entry_time,
            entry_price=entry_price,
            side=side,
            size=size,
            initial_size=size,
            stop_loss=stop_loss,
            take_profit=take_profit,
            risk_amount=risk_amount
        )

        self._next_position_id += 1
        self.open_positions[position.id] = position

        return position

    def close_position(self, position_id: str, exit_time: datetime,
                      exit_price: float, exit_type: ExitType):
        """Close a position and update capital"""
        if position_id not in self.open_positions:
            return

        position = self.open_positions[position_id]
        position.close(exit_time, exit_price, exit_type)

        # Update capital
        self.current_capital += position.realized_pnl

        # Move to closed positions
        self.closed_positions.append(position)
        del self.open_positions[position_id]

    def update_positions(self, current_time: datetime, current_price: float):
        """Update all open positions with current price"""
        for position in self.open_positions.values():
            position.update_price(current_price)
            position.bars_held += 1

    def get_strategy_positions(self, strategy_name: str) -> List[Position]:
        """Get all positions (open and closed) for a specific strategy"""
        strategy_positions = []

        # Add open positions
        strategy_positions.extend([
            pos for pos in self.open_positions.values()
            if pos.strategy_name == strategy_name
        ])

        # Add closed positions
        strategy_positions.extend([
            pos for pos in self.closed_positions
            if pos.strategy_name == strategy_name
        ])

        return strategy_positions