"""
Example strategies demonstrating various strategy patterns.

These serve as templates and examples for creating custom strategies.
"""

import pandas as pd
from typing import Optional
from datetime import datetime

from .strategy import BaseStrategy, StrategySignal
from .position import PositionSide, Position


class SimpleMAStrategy(BaseStrategy):
    """
    Simple Moving Average crossover strategy.

    Buys when fast MA crosses above slow MA, sells when crosses below.
    Single timeframe strategy example.
    """

    def __init__(self, config: dict = None):
        default_config = {
            'fast_period': 20,
            'slow_period': 50,
            'risk_percent': 1.0,
            'sl_percent': 2.0,
            'tp_rr_ratio': 2.0
        }
        if config:
            default_config.update(config)

        super().__init__(
            name="Simple MA Crossover",
            timeframes=['1h'],  # Single timeframe
            config=default_config
        )

    def generate_signals(self, data: pd.DataFrame, timestamp: datetime) -> Optional[StrategySignal]:
        """Generate signals based on MA crossover"""
        # Get current and previous rows
        current_idx = data[data['timestamp'] == timestamp].index
        if len(current_idx) == 0 or current_idx[0] < self.config['slow_period']:
            return None

        idx = current_idx[0]

        # Calculate MAs
        close_prices = data['close'].iloc[max(0, idx - self.config['slow_period']):idx + 1]

        fast_ma_current = close_prices.iloc[-self.config['fast_period']:].mean()
        slow_ma_current = close_prices.iloc[-self.config['slow_period']:].mean()

        fast_ma_prev = close_prices.iloc[-self.config['fast_period'] - 1:-1].mean()
        slow_ma_prev = close_prices.iloc[-self.config['slow_period'] - 1:-1].mean()

        # Check for crossover
        if fast_ma_prev <= slow_ma_prev and fast_ma_current > slow_ma_current:
            # Bullish crossover
            return StrategySignal(
                timestamp=timestamp,
                side=PositionSide.LONG,
                confidence=1.0,
                metadata={'fast_ma': fast_ma_current, 'slow_ma': slow_ma_current}
            )
        elif fast_ma_prev >= slow_ma_prev and fast_ma_current < slow_ma_current:
            # Bearish crossover
            return StrategySignal(
                timestamp=timestamp,
                side=PositionSide.SHORT,
                confidence=1.0,
                metadata={'fast_ma': fast_ma_current, 'slow_ma': slow_ma_current}
            )

        return None

    def should_exit(self, position: Position, data: pd.DataFrame, timestamp: datetime) -> bool:
        """Exit on opposite crossover"""
        current_idx = data[data['timestamp'] == timestamp].index
        if len(current_idx) == 0 or current_idx[0] < self.config['slow_period']:
            return False

        idx = current_idx[0]
        close_prices = data['close'].iloc[max(0, idx - self.config['slow_period']):idx + 1]

        fast_ma = close_prices.iloc[-self.config['fast_period']:].mean()
        slow_ma = close_prices.iloc[-self.config['slow_period']:].mean()

        # Exit on opposite signal
        if position.side == PositionSide.LONG and fast_ma < slow_ma:
            return True
        elif position.side == PositionSide.SHORT and fast_ma > slow_ma:
            return True

        return False


class MultiTimeframeStrategy(BaseStrategy):
    """
    Multi-timeframe strategy example.

    Uses higher timeframe for trend, lower timeframe for entries.
    This demonstrates proper timeframe alignment.
    """

    def __init__(self, config: dict = None):
        default_config = {
            'trend_tf': '1h',  # Higher timeframe for trend
            'entry_tf': '5m',  # Lower timeframe for entry
            'trend_ma_period': 50,
            'entry_ma_period': 20,
            'risk_percent': 1.0,
            'sl_percent': 1.5,
            'tp_rr_ratio': 2.5
        }
        if config:
            default_config.update(config)

        super().__init__(
            name="Multi-Timeframe Trend",
            timeframes=[default_config['entry_tf'], default_config['trend_tf']],
            config=default_config
        )

    def generate_signals(self, data: pd.DataFrame, timestamp: datetime) -> Optional[StrategySignal]:
        """Generate signals using multi-timeframe analysis"""
        current_row = data[data['timestamp'] == timestamp]
        if current_row.empty:
            return None

        row = current_row.iloc[0]

        # Get trend from higher timeframe
        trend_tf = self.config['trend_tf']
        trend_close = row.get(f'{trend_tf}_close')

        if pd.isna(trend_close):
            return None

        # For this example, simplified: check if price is above/below trend MA
        # In reality, you'd calculate this properly with the aligned data

        entry_tf = self.config['entry_tf']
        entry_close = row.get(f'{entry_tf}_close', row.get('close'))

        # Simple condition: if trend is bullish and entry shows momentum
        # This is a simplified example - implement your own logic
        if trend_close > entry_close * 0.99:  # Simplified bullish trend
            return StrategySignal(
                timestamp=timestamp,
                side=PositionSide.LONG,
                confidence=0.8
            )

        return None

    def should_exit(self, position: Position, data: pd.DataFrame, timestamp: datetime) -> bool:
        """Exit when trend reverses on higher timeframe"""
        # Implement your exit logic based on higher timeframe
        return False


class PartialExitStrategy(BaseStrategy):
    """
    Strategy demonstrating partial position exits.

    Takes partial profits at different R-multiples.
    """

    def __init__(self, config: dict = None):
        default_config = {
            'risk_percent': 2.0,
            'sl_percent': 2.0,
            'tp_type': 'rr',
            'tp_rr_ratio': 3.0,  # Final target
            'partial_exits': [
                (0.5, 2.0),  # Close 50% at 2R
                (0.5, 3.0)   # Close remaining 50% at 3R
            ]
        }
        if config:
            default_config.update(config)

        super().__init__(
            name="Partial Exit Strategy",
            timeframes=['1h'],
            config=default_config
        )

    def generate_signals(self, data: pd.DataFrame, timestamp: datetime) -> Optional[StrategySignal]:
        """Example signal generation - implement your logic"""
        # Implement your entry logic here
        return None

    def should_exit(self, position: Position, data: pd.DataFrame, timestamp: datetime) -> bool:
        """Example exit condition"""
        # Implement your exit logic here
        return False