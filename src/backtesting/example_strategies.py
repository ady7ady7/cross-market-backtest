"""
Example strategies demonstrating various strategy patterns.

These serve as templates and examples for creating custom strategies.
"""

import pandas as pd
from typing import Optional
from datetime import datetime

from .strategy import BaseStrategy, StrategySignal
from .position import PositionSide, Position
from ..utils import TimeframeNormalizer


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
            'tp_rr_ratio': 2.0,
            'timeframes': ['1h']  # Default timeframe
        }
        if config:
            default_config.update(config)

        super().__init__(
            name="Simple MA Crossover",
            timeframes=default_config['timeframes'],  # Use timeframes from config
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


class HTSTrendFollowStrategy(BaseStrategy):
    """
    Multi-timeframe HTS Trend Following Strategy.

    Logic:
    1. H1 Filter: Price must be above/below Pivot P AND HTS crossover bias (EMA33 vs EMA144)
       - Long: Price > P AND EMA33 channel > EMA144 channel
       - Short: Price < P AND EMA33 channel < EMA144 channel

    2. M5 Entry: Retest EMA133 channel and return to EMA33 channel
       - Long: Price dips to EMA133 low, then rallies back above EMA33 low
       - Short: Price rallies to EMA133 high, then drops back below EMA33 high

    3. Stop Loss: Below/above the EMA133 retest low/high

    4. Take Profit: Partial exits at 1.5R (50%) and 4R (50%)
    """

    def __init__(self, config: dict = None):
        default_config = {
            'h1_ema_fast': 33,
            'h1_ema_slow': 144,
            'm5_ema_fast': 33,
            'm5_ema_slow': 133,
            'risk_percent': 1.0,
            'partial_exits': [
                (0.5, 1.5),  # 50% at 1.5R
                (0.5, 4.0)   # 50% at 4R
            ],
            'timeframes': ['5m', '1h']  # m5 for entry, h1 for trend filter
        }
        if config:
            default_config.update(config)

        super().__init__(
            name="HTS Trend Follow",
            timeframes=default_config['timeframes'],
            config=default_config
        )

        # Normalize timeframes to handle any format (m5/5m, h1/1h)
        self.m5_tf = None
        self.h1_tf = None

        for tf in self.timeframes:
            tf_standard = TimeframeNormalizer.to_standard(tf)
            if tf_standard == '5m':
                self.m5_tf = tf  # Store original format from data
            elif tf_standard == '1h':
                self.h1_tf = tf  # Store original format from data

        # Track retest state
        self.retest_low = None
        self.retest_high = None
        self.in_retest = False

        # Cache for pre-calculated indicators
        self.indicators_calculated = False
        self.h1_ema33_high = None
        self.h1_ema33_low = None
        self.h1_ema144_high = None
        self.h1_ema144_low = None
        self.m5_ema33_high = None
        self.m5_ema33_low = None
        self.m5_ema133_high = None
        self.m5_ema133_low = None

    def _calculate_ema(self, prices: pd.Series, period: int) -> float:
        """Calculate EMA for given prices and period"""
        if len(prices) < period:
            return None
        return prices.ewm(span=period, adjust=False).mean().iloc[-1]

    def _get_h1_trend_bias(self, data: pd.DataFrame, timestamp: datetime) -> Optional[str]:
        """
        Determine H1 trend bias using Pivot P and HTS crossover.

        Returns:
            'bullish', 'bearish', or None
        """
        current_row = data[data['timestamp'] == timestamp]
        if current_row.empty:
            return None

        row = current_row.iloc[0]

        # Get H1 close price (use dynamic timeframe format)
        h1_close_col = f'{self.h1_tf}_close'
        h1_close = row.get(h1_close_col)
        if pd.isna(h1_close):
            return None

        # Get Pivot P (needs to be calculated from H1 data)
        # For simplicity, we'll use a rolling pivot approximation
        # In practice, you'd integrate with pivot_points.py
        h1_high_col = f'{self.h1_tf}_high'
        h1_low_col = f'{self.h1_tf}_low'
        h1_high = row.get(h1_high_col)
        h1_low = row.get(h1_low_col)

        if pd.isna(h1_high) or pd.isna(h1_low):
            return None

        # Calculate pivot point (simplified - previous bar's HLC/3)
        pivot_p = (h1_high + h1_low + h1_close) / 3

        # Get current index for EMA lookup
        current_idx = data[data['timestamp'] == timestamp].index
        if len(current_idx) == 0:
            return None
        idx = current_idx[0]

        # Get pre-calculated H1 EMAs at current timestamp
        ema33_high = self.h1_ema33_high.iloc[idx]
        ema33_low = self.h1_ema33_low.iloc[idx]
        ema144_high = self.h1_ema144_high.iloc[idx]
        ema144_low = self.h1_ema144_low.iloc[idx]

        if pd.isna(ema33_high) or pd.isna(ema33_low) or pd.isna(ema144_high) or pd.isna(ema144_low):
            return None

        # Check trend conditions
        price_above_pivot = h1_close > pivot_p
        ema33_above_ema144 = (ema33_high > ema144_high) and (ema33_low > ema144_low)

        if price_above_pivot and ema33_above_ema144:
            return 'bullish'
        elif not price_above_pivot and not ema33_above_ema144:
            return 'bearish'

        return None

    def _check_m5_entry(self, data: pd.DataFrame, timestamp: datetime, trend_bias: str) -> Optional[StrategySignal]:
        """
        Check for M5 entry signal: retest EMA133 and return to EMA33.
        """
        current_row = data[data['timestamp'] == timestamp]
        if current_row.empty:
            return None

        row = current_row.iloc[0]

        # Get M5 OHLC (base timeframe data)
        m5_high = row.get('high')
        m5_low = row.get('low')
        m5_close = row.get('close')

        if pd.isna(m5_high) or pd.isna(m5_low) or pd.isna(m5_close):
            return None

        # Get current index for EMA lookup
        current_idx = data[data['timestamp'] == timestamp].index
        if len(current_idx) == 0:
            return None
        idx = current_idx[0]

        # Get pre-calculated M5 EMAs at current timestamp
        ema33_high = self.m5_ema33_high.iloc[idx]
        ema33_low = self.m5_ema33_low.iloc[idx]
        ema133_high = self.m5_ema133_high.iloc[idx]
        ema133_low = self.m5_ema133_low.iloc[idx]

        if pd.isna(ema33_high) or pd.isna(ema33_low) or pd.isna(ema133_high) or pd.isna(ema133_low):
            return None

        # LONG setup: retest EMA133 low and return to EMA33
        if trend_bias == 'bullish':
            # Check if we're touching/below EMA133 low (retest)
            if m5_low <= ema133_low * 1.002:  # 0.2% tolerance
                self.in_retest = True
                self.retest_low = m5_low

            # Check if we've returned above EMA33 low (entry trigger)
            if self.in_retest and m5_close > ema33_low:
                self.in_retest = False

                # Ensure SL is below entry (add small buffer if needed)
                sl_level = self.retest_low
                if sl_level >= m5_close:
                    sl_level = m5_close * 0.999  # 0.1% below entry as minimum

                return StrategySignal(
                    timestamp=timestamp,
                    side=PositionSide.LONG,
                    confidence=1.0,
                    metadata={
                        'entry_price': m5_close,
                        'sl_level': sl_level,
                        'ema33_low': ema33_low,
                        'ema133_low': ema133_low
                    }
                )

        # SHORT setup: retest EMA133 high and return to EMA33
        elif trend_bias == 'bearish':
            # Check if we're touching/above EMA133 high (retest)
            if m5_high >= ema133_high * 0.998:  # 0.2% tolerance
                self.in_retest = True
                self.retest_high = m5_high

            # Check if we've returned below EMA33 high (entry trigger)
            if self.in_retest and m5_close < ema33_high:
                self.in_retest = False

                # Ensure SL is above entry (add small buffer if needed)
                sl_level = self.retest_high
                if sl_level <= m5_close:
                    sl_level = m5_close * 1.001  # 0.1% above entry as minimum

                return StrategySignal(
                    timestamp=timestamp,
                    side=PositionSide.SHORT,
                    confidence=1.0,
                    metadata={
                        'entry_price': m5_close,
                        'sl_level': sl_level,
                        'ema33_high': ema33_high,
                        'ema133_high': ema133_high
                    }
                )

        return None

    def _precalculate_indicators(self, data: pd.DataFrame):
        """Pre-calculate all EMAs once for the entire dataset"""
        print("Pre-calculating indicators for HTS strategy...")

        # Calculate H1 EMAs
        h1_high_col = f'{self.h1_tf}_high'
        h1_low_col = f'{self.h1_tf}_low'
        self.h1_ema33_high = data[h1_high_col].ewm(span=self.config['h1_ema_fast'], adjust=False).mean()
        self.h1_ema33_low = data[h1_low_col].ewm(span=self.config['h1_ema_fast'], adjust=False).mean()
        self.h1_ema144_high = data[h1_high_col].ewm(span=self.config['h1_ema_slow'], adjust=False).mean()
        self.h1_ema144_low = data[h1_low_col].ewm(span=self.config['h1_ema_slow'], adjust=False).mean()

        # Calculate M5 EMAs
        self.m5_ema33_high = data['high'].ewm(span=self.config['m5_ema_fast'], adjust=False).mean()
        self.m5_ema33_low = data['low'].ewm(span=self.config['m5_ema_fast'], adjust=False).mean()
        self.m5_ema133_high = data['high'].ewm(span=self.config['m5_ema_slow'], adjust=False).mean()
        self.m5_ema133_low = data['low'].ewm(span=self.config['m5_ema_slow'], adjust=False).mean()

        self.indicators_calculated = True
        print("Indicators pre-calculated successfully")

    def generate_signals(self, data: pd.DataFrame, timestamp: datetime) -> Optional[StrategySignal]:
        """Generate signals based on H1 trend and M5 entry logic"""
        # Pre-calculate indicators on first call
        if not self.indicators_calculated:
            self._precalculate_indicators(data)

        # Validate that we have the required timeframes
        if self.m5_tf is None or self.h1_tf is None:
            return None

        # Step 1: Check H1 trend bias
        trend_bias = self._get_h1_trend_bias(data, timestamp)

        if trend_bias is None:
            return None

        # Step 2: Check for M5 entry signal
        signal = self._check_m5_entry(data, timestamp, trend_bias)

        # If we have a signal, add SL/TP configuration
        if signal:
            # Calculate stop loss distance
            entry_price = signal.metadata['entry_price']
            sl_level = signal.metadata['sl_level']
            sl_distance = abs(entry_price - sl_level)

            # Set position config with dynamic SL and partial exits
            signal.metadata['sl_price'] = sl_level
            signal.metadata['sl_distance'] = sl_distance
            signal.metadata['partial_exits'] = self.config['partial_exits']

        return signal

    def should_exit(self, position: Position, data: pd.DataFrame, timestamp: datetime) -> bool:
        """Exit logic - handled by partial exits and SL/TP in position manager"""
        # Strategy-specific exit conditions can be added here
        # For now, rely on automated SL/TP and partial exits
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