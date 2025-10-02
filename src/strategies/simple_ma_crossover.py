"""
Simple Moving Average Crossover Strategy

A basic trend-following strategy using two moving averages.
- Buy when fast MA crosses above slow MA
- Sell when fast MA crosses below slow MA
- Uses UI-configured SL/TP settings
"""

import pandas as pd
from typing import Optional
from datetime import datetime

from ..backtesting.strategy import BaseStrategy, StrategySignal
from ..backtesting.position import PositionSide, Position
from .base_strategy_template import StrategyMetadata


class SimpleMAStrategy(BaseStrategy):
    """
    Simple MA Crossover Strategy - Single Timeframe

    Configuration:
    - User sets SL/TP in UI (strategy doesn't override)
    - Works on any single timeframe
    - Configurable MA periods
    """

    @classmethod
    def get_metadata(cls) -> StrategyMetadata:
        return StrategyMetadata(
            id='simple_ma',
            name='Simple MA Crossover',
            description='Buy/sell on moving average crossovers. Uses your SL/TP settings.',

            required_timeframes=[],  # Works on any timeframe user selects
            base_timeframe='',  # Will use first selected timeframe

            # User controls SL/TP via UI
            uses_custom_sl=False,
            uses_custom_tp=False,
            default_sl_type='percent',
            default_tp_type='rr',

            configurable_params={
                'fast_period': {
                    'type': 'number',
                    'label': 'Fast MA Period',
                    'default': 20,
                    'min': 5,
                    'max': 200,
                    'help': 'Period for fast moving average'
                },
                'slow_period': {
                    'type': 'number',
                    'label': 'Slow MA Period',
                    'default': 50,
                    'min': 10,
                    'max': 500,
                    'help': 'Period for slow moving average'
                }
            }
        )

    def __init__(self, config: dict = None):
        metadata = self.get_metadata()

        default_config = {
            'fast_period': 20,
            'slow_period': 50,
            'risk_percent': 1.0,
            'timeframes': ['1h']  # Default, will be overridden by UI
        }

        if config:
            default_config.update(config)

        super().__init__(
            name=metadata.name,
            timeframes=default_config['timeframes'],
            config=default_config
        )

    def generate_signals(self, data: pd.DataFrame, timestamp: datetime) -> Optional[StrategySignal]:
        """Generate signals based on MA crossover"""
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
