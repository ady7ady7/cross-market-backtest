"""
Main backtesting engine that orchestrates the entire backtest process.

Coordinates data alignment, strategy execution, position management,
and performance tracking.
"""

from typing import Dict, List, Optional
import pandas as pd
from datetime import datetime

from .data_alignment import MultiTimeframeAligner
from .strategy import BaseStrategy, MultiStrategyComposer, StrategySignal
from .position import PositionManager, PositionSide, ExitType
from .performance import PerformanceTracker, PerformanceMetrics


class BacktestEngine:
    """
    Main backtesting engine for executing trading strategies.

    Supports:
    - Multi-timeframe strategies
    - Multiple concurrent strategies
    - Complex position management
    - Real-time performance tracking
    """

    def __init__(self, initial_capital: float = 10000.0,
                 max_total_risk_percent: float = 6.0):
        """
        Initialize backtest engine.

        Args:
            initial_capital: Starting capital
            max_total_risk_percent: Maximum % at risk across all positions
        """
        self.initial_capital = initial_capital
        self.max_total_risk_percent = max_total_risk_percent

        # Components
        self.position_manager: Optional[PositionManager] = None
        self.performance_tracker: Optional[PerformanceTracker] = None
        self.data_aligner: Optional[MultiTimeframeAligner] = None
        self.strategy_composer: Optional[MultiStrategyComposer] = None

        # Data
        self.aligned_data: Optional[pd.DataFrame] = None

        # Results
        self.trade_history: List[Dict] = []

    def run(self, strategies: List[BaseStrategy],
            data_dict: Dict[str, pd.DataFrame],
            start_date: Optional[datetime] = None,
            end_date: Optional[datetime] = None) -> Dict:
        """
        Run backtest with given strategies and data.

        Args:
            strategies: List of strategy instances to test
            data_dict: Dictionary mapping timeframe to DataFrame
            start_date: Optional start date for backtest
            end_date: Optional end date for backtest

        Returns:
            Dictionary with results including metrics, trades, equity curve
        """
        # Initialize components
        self._initialize(strategies)

        # Align multi-timeframe data
        print("Aligning multi-timeframe data...")
        self.aligned_data = self.data_aligner.align_data(data_dict)

        # Filter date range if specified
        if start_date:
            self.aligned_data = self.aligned_data[
                self.aligned_data['timestamp'] >= start_date
            ]
        if end_date:
            self.aligned_data = self.aligned_data[
                self.aligned_data['timestamp'] <= end_date
            ]

        print(f"Running backtest on {len(self.aligned_data)} bars...")

        # Run backtest loop
        self._run_backtest_loop()

        # Calculate final metrics
        print("Calculating performance metrics...")
        results = self._compile_results()

        return results

    def _initialize(self, strategies: List[BaseStrategy]):
        """Initialize all engine components"""
        self.strategy_composer = MultiStrategyComposer(strategies)

        # Get all timeframes needed
        all_timeframes = self.strategy_composer.get_all_timeframes()
        self.data_aligner = MultiTimeframeAligner(all_timeframes)

        # Initialize position and performance tracking
        self.position_manager = PositionManager(
            self.initial_capital,
            self.max_total_risk_percent
        )
        self.performance_tracker = PerformanceTracker(self.initial_capital)

        self.trade_history = []

    def _run_backtest_loop(self):
        """Main backtest loop iterating through each bar"""
        base_timeframe = self.data_aligner.base_timeframe

        for idx, row in self.aligned_data.iterrows():
            timestamp = row['timestamp']
            current_price = row['close']

            # Update all open positions with current price
            self.position_manager.update_positions(timestamp, current_price)

            # Check for exits (SL/TP and strategy conditions)
            self._check_exits(timestamp, current_price)

            # Generate new signals
            signals = self.strategy_composer.generate_all_signals(
                self.aligned_data,
                timestamp
            )

            # Process signals and open positions
            self._process_signals(signals, timestamp, current_price)

            # Update performance tracking
            open_pnl = sum(
                pos.unrealized_pnl
                for pos in self.position_manager.open_positions.values()
            )
            self.performance_tracker.update(
                timestamp,
                self.position_manager.current_capital,
                open_pnl
            )

    def _check_exits(self, timestamp: datetime, current_price: float):
        """Check all positions for exit conditions"""
        positions_to_close = []

        for pos_id, position in self.position_manager.open_positions.items():
            should_exit = False
            exit_type = None

            # Check stop loss
            if position.stop_loss:
                if position.side == PositionSide.LONG:
                    if current_price <= position.stop_loss:
                        should_exit = True
                        exit_type = ExitType.STOP_LOSS
                else:  # SHORT
                    if current_price >= position.stop_loss:
                        should_exit = True
                        exit_type = ExitType.STOP_LOSS

            # Check take profit
            if not should_exit and position.take_profit:
                if position.side == PositionSide.LONG:
                    if current_price >= position.take_profit:
                        should_exit = True
                        exit_type = ExitType.TAKE_PROFIT
                else:  # SHORT
                    if current_price <= position.take_profit:
                        should_exit = True
                        exit_type = ExitType.TAKE_PROFIT

            # Check strategy-specific exit conditions
            if not should_exit:
                strategy = self._get_strategy_by_name(position.strategy_name)
                if strategy and strategy.should_exit(position, self.aligned_data, timestamp):
                    should_exit = True
                    exit_type = ExitType.CONDITION_BASED

            if should_exit:
                positions_to_close.append((pos_id, exit_type))

        # Close positions
        for pos_id, exit_type in positions_to_close:
            self._close_position(pos_id, timestamp, current_price, exit_type)

    def _process_signals(self, signals: Dict[str, StrategySignal],
                        timestamp: datetime, current_price: float):
        """Process trading signals and open positions"""
        for strategy_name, signal in signals.items():
            # Check if strategy already has an open position
            existing_positions = [
                pos for pos in self.position_manager.open_positions.values()
                if pos.strategy_name == strategy_name
            ]

            if existing_positions:
                # Strategy already has a position, skip signal
                continue

            # Get strategy config
            strategy = self._get_strategy_by_name(strategy_name)
            if not strategy:
                continue

            # Try to open position
            position = self.position_manager.open_position(
                strategy_name=strategy_name,
                entry_time=timestamp,
                entry_price=current_price,
                side=signal.side,
                config=strategy.position_config
            )

            if position:
                # Record trade entry
                self.trade_history.append({
                    'timestamp': timestamp,
                    'strategy': strategy_name,
                    'action': 'ENTRY',
                    'side': signal.side.value,
                    'price': current_price,
                    'size': position.size,
                    'position_id': position.id
                })

    def _close_position(self, position_id: str, timestamp: datetime,
                       exit_price: float, exit_type: ExitType):
        """Close a position and record the trade"""
        position = self.position_manager.open_positions.get(position_id)
        if not position:
            return

        # Close position
        self.position_manager.close_position(
            position_id,
            timestamp,
            exit_price,
            exit_type
        )

        # Record trade exit
        self.trade_history.append({
            'timestamp': timestamp,
            'strategy': position.strategy_name,
            'action': 'EXIT',
            'exit_type': exit_type.value,
            'price': exit_price,
            'pnl': position.realized_pnl,
            'r_multiple': position.r_multiple,
            'position_id': position_id
        })

    def _get_strategy_by_name(self, name: str) -> Optional[BaseStrategy]:
        """Get strategy instance by name"""
        if not self.strategy_composer:
            return None

        for strategy in self.strategy_composer.strategies:
            if strategy.name == name:
                return strategy
        return None

    def _compile_results(self) -> Dict:
        """Compile all results into a comprehensive dictionary"""
        # Calculate overall metrics
        overall_metrics = self.performance_tracker.calculate_metrics(
            self.position_manager.closed_positions
        )

        # Calculate per-strategy metrics
        strategy_metrics = {}
        for strategy in self.strategy_composer.strategies:
            strategy_positions = self.position_manager.get_strategy_positions(
                strategy.name
            )
            strategy_closed = [p for p in strategy_positions if not p.is_open]

            if strategy_closed:
                strategy_tracker = PerformanceTracker(self.initial_capital)
                # Note: This is simplified - in reality you'd need to track
                # per-strategy equity curves separately
                strategy_metrics[strategy.name] = strategy_tracker.calculate_metrics(
                    strategy_closed
                )

        # Get equity curve and drawdown data
        equity_df = self.performance_tracker.get_equity_dataframe()
        drawdown_df = self.performance_tracker.get_drawdown_dataframe()

        # Compile trade history
        trades_df = pd.DataFrame(self.trade_history)

        results = {
            'overall_metrics': overall_metrics,
            'strategy_metrics': strategy_metrics,
            'equity_curve': equity_df,
            'drawdown_curve': drawdown_df,
            'trades': trades_df,
            'all_positions': self.position_manager.closed_positions,
            'summary': self._create_summary(overall_metrics)
        }

        return results

    def _create_summary(self, metrics: PerformanceMetrics) -> Dict:
        """Create a text summary of results"""
        return {
            'Initial Capital': f"${metrics.initial_capital:,.2f}",
            'Final Capital': f"${metrics.final_capital:,.2f}",
            'Total Return': f"${metrics.total_return:,.2f} ({metrics.total_return_pct:.2f}%)",
            'Total Trades': metrics.total_trades,
            'Win Rate': f"{metrics.win_rate:.2f}%",
            'Profit Factor': f"{metrics.profit_factor:.2f}",
            'Max Drawdown': f"${metrics.max_drawdown:,.2f} ({metrics.max_drawdown_pct:.2f}%)",
            'Sharpe Ratio': f"{metrics.sharpe_ratio:.2f}",
            'Sortino Ratio': f"{metrics.sortino_ratio:.2f}",
            'Avg R-Multiple': f"{metrics.avg_r_multiple:.2f}"
        }