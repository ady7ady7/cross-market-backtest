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
    size: float  # Position size in units
    initial_size: float  # Original size before partial exits

    # Risk management
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    risk_amount: float = 0.0  # Dollar amount risked
    point_value: float = 1.0  # Dollar value per 1 point of price movement

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
        """Calculate unrealized P&L using point value system"""
        if not self.is_open:
            return 0.0

        # Get point value from position metadata (stored during position creation)
        point_value = getattr(self, 'point_value', 1.0)

        if self.side == PositionSide.LONG:
            price_change_points = self.current_price - self.entry_price
        else:
            price_change_points = self.entry_price - self.current_price

        return price_change_points * point_value * self.size

    @property
    def realized_pnl(self) -> float:
        """Calculate realized P&L using point value system"""
        if self.is_open:
            return 0.0

        # Get point value from position metadata
        point_value = getattr(self, 'point_value', 1.0)

        if self.side == PositionSide.LONG:
            price_change_points = self.exit_price - self.entry_price
        else:
            price_change_points = self.entry_price - self.exit_price

        pnl = price_change_points * point_value * self.initial_size

        # Add partial exits P&L (already calculated with point value when partial exit occurred)
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

        # Calculate P&L for this partial exit using point value
        if self.side == PositionSide.LONG:
            price_change_points = exit_price - self.entry_price
        else:
            price_change_points = self.entry_price - exit_price

        pnl = price_change_points * self.point_value * exit_size

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

    def __init__(self, initial_capital: float, max_total_risk_percent: float = 6.0,
                 point_value: float = 1.0, use_compounding: bool = False):
        """
        Initialize position manager.

        Args:
            initial_capital: Starting account balance
            max_total_risk_percent: Maximum % of capital at risk across all open positions
            point_value: Dollar value per 1 point of price movement (default 1.0 for micro contracts)
            use_compounding: If True, use current capital for risk calc; if False, use initial capital
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.max_total_risk_percent = max_total_risk_percent
        self.point_value = point_value
        self.use_compounding = use_compounding

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
        Calculate position size based on risk parameters using point value system.

        Formula: position_size = risk_amount / (risk_in_points * point_value)

        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            config: Position configuration
            side: Position side (LONG/SHORT)

        Returns:
            Tuple of (position_size, risk_amount)
        """
        # Calculate risk in points
        if side == PositionSide.LONG:
            risk_in_points = entry_price - stop_loss
        else:
            risk_in_points = stop_loss - entry_price

        if risk_in_points <= 0:
            raise ValueError(f"Invalid stop loss: no risk defined (Entry={entry_price}, SL={stop_loss}, Side={side})")

        # Use initial capital if not compounding, current capital if compounding
        capital_for_risk = self.current_capital if self.use_compounding else self.initial_capital

        # Calculate dollar risk amount
        risk_amount = capital_for_risk * (config.risk_percent / 100)

        # Calculate position size using point value
        # position_size = risk_$ / (risk_points * $_per_point)
        position_size = risk_amount / (risk_in_points * self.point_value)

        # Debug: Log first 3 positions to verify sizing
        if self._next_position_id <= 3:
            print(f"   Position sizing: Risk ${risk_amount:.2f} over {risk_in_points:.2f} points")
            print(f"   Point value: ${self.point_value}, Position size: {position_size:.4f} units")

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
            if stop_loss is None:
                # Fallback to 1% if price is not set
                stop_loss = entry_price * 0.99 if side == PositionSide.LONG else entry_price * 1.01
        else:
            # For time-based or condition-based, use a default % for sizing
            stop_loss = entry_price * 0.99 if side == PositionSide.LONG else entry_price * 1.01

        # Validate stop loss
        if stop_loss is None:
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
            risk_amount=risk_amount,
            point_value=self.point_value
        )

        # Debug: Log first 3 positions
        if self._next_position_id <= 3:
            print(f"   Opened position #{self._next_position_id}: {side.value} {size:.4f} units @ {entry_price:.2f}")
            print(f"   SL: {stop_loss:.2f}, TP: {take_profit:.2f if take_profit else 'None'}, Risk: ${risk_amount:.2f}")

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