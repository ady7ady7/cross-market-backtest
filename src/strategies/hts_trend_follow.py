"""
HTS Trend Following Strategy (Multi-Timeframe)

A trend-following strategy using H1 trend filter and M5 entries.

LOGIC:
1. H1 Filter: Price above/below Pivot P AND EMA33 channel above/below EMA144
2. M5 Entry: Retest EMA133, then return to EMA33
3. SL: Below/above the farthest EMA (EMA133) with buffer (strategy-controlled)
4. TP: Partial exits at 1.5R (50%) and 4R (50%) (strategy-controlled)
5. Risk Management: Maximum ONE position per day

IMPORTANT: This strategy CONTROLS its own SL/TP.
UI SL/TP settings are IGNORED - strategy uses dynamic levels.
SL is placed at the farthest EMA to ensure proper risk calculation.
"""

import pandas as pd
from typing import Optional
from datetime import datetime

from ..backtesting.strategy import BaseStrategy, StrategySignal
from ..backtesting.position import PositionSide, Position
from ..utils import TimeframeNormalizer
from .base_strategy_template import StrategyMetadata


class HTSTrendFollowStrategy(BaseStrategy):
    """
    Multi-timeframe HTS trend following with dynamic SL/TP.

    SL/TP Behavior:
    - SL: Automatically placed at retest low/high
    - TP: Partial exits (50% at 1.5R, 50% at 4R)
    - UI SL/TP inputs are disabled for this strategy
    """

    @classmethod
    def get_metadata(cls) -> StrategyMetadata:
        return StrategyMetadata(
            id='hts_trend',
            name='HTS Trend Follow (Multi-TF)',
            description='H1 trend filter + M5 entries. SL at farthest EMA (EMA133), TP at 1.5R/4R. Max 1 position/day.',

            # Requires both timeframes
            required_timeframes=['5m', '1h'],
            base_timeframe='5m',

            # Strategy controls SL/TP (UI settings ignored)
            uses_custom_sl=True,  # SL placed at retest level
            uses_custom_tp=True,  # Partial exits at 1.5R and 4R
            default_sl_type='price',
            default_tp_type='rr',

            configurable_params={
                'h1_ema_fast': {
                    'type': 'number',
                    'label': 'H1 Fast EMA (Trend)',
                    'default': 33,
                    'min': 10,
                    'max': 100,
                    'help': 'Fast EMA period for H1 trend channel'
                },
                'h1_ema_slow': {
                    'type': 'number',
                    'label': 'H1 Slow EMA (Trend)',
                    'default': 144,
                    'min': 50,
                    'max': 200,
                    'help': 'Slow EMA period for H1 trend channel'
                },
                'm5_ema_fast': {
                    'type': 'number',
                    'label': 'M5 Fast EMA (Entry)',
                    'default': 33,
                    'min': 10,
                    'max': 100,
                    'help': 'Fast EMA period for M5 entry'
                },
                'm5_ema_slow': {
                    'type': 'number',
                    'label': 'M5 Slow EMA (Retest)',
                    'default': 133,
                    'min': 50,
                    'max': 200,
                    'help': 'Slow EMA period for M5 retest level'
                }
            }
        )

    def __init__(self, config: dict = None):
        metadata = self.get_metadata()

        default_config = {
            'h1_ema_fast': 33,
            'h1_ema_slow': 144,
            'm5_ema_fast': 33,
            'm5_ema_slow': 133,
            'risk_percent': 1.0,
            'timeframes': metadata.required_timeframes,
            # Fixed partial exits (strategy-controlled)
            'partial_exits': [
                (0.5, 1.5),  # 50% at 1.5R
                (0.5, 4.0)   # 50% at 4R
            ]
        }

        if config:
            default_config.update(config)

        super().__init__(
            name=metadata.name,
            timeframes=default_config['timeframes'],
            config=default_config
        )

        # Detect timeframe formats
        self.m5_tf = None
        self.h1_tf = None
        for tf in self.timeframes:
            tf_standard = TimeframeNormalizer.to_standard(tf)
            if tf_standard == '5m':
                self.m5_tf = tf
            elif tf_standard == '1h':
                self.h1_tf = tf

        # Retest state tracking
        self.retest_low = None
        self.retest_high = None
        self.in_retest = False

        # One position per day tracking
        self.last_entry_date = None

        # Pre-calculated indicators cache
        self.indicators_calculated = False
        self.h1_ema33_high = None
        self.h1_ema33_low = None
        self.h1_ema144_high = None
        self.h1_ema144_low = None
        self.m5_ema33_high = None
        self.m5_ema33_low = None
        self.m5_ema133_high = None
        self.m5_ema133_low = None

    def _precalculate_indicators(self, data: pd.DataFrame):
        """Pre-calculate all EMAs once for performance"""
        print("Pre-calculating HTS indicators...")

        # H1 EMAs
        h1_high_col = f'{self.h1_tf}_high'
        h1_low_col = f'{self.h1_tf}_low'
        self.h1_ema33_high = data[h1_high_col].ewm(span=self.config['h1_ema_fast'], adjust=False).mean()
        self.h1_ema33_low = data[h1_low_col].ewm(span=self.config['h1_ema_fast'], adjust=False).mean()
        self.h1_ema144_high = data[h1_high_col].ewm(span=self.config['h1_ema_slow'], adjust=False).mean()
        self.h1_ema144_low = data[h1_low_col].ewm(span=self.config['h1_ema_slow'], adjust=False).mean()

        # M5 EMAs
        self.m5_ema33_high = data['high'].ewm(span=self.config['m5_ema_fast'], adjust=False).mean()
        self.m5_ema33_low = data['low'].ewm(span=self.config['m5_ema_fast'], adjust=False).mean()
        self.m5_ema133_high = data['high'].ewm(span=self.config['m5_ema_slow'], adjust=False).mean()
        self.m5_ema133_low = data['low'].ewm(span=self.config['m5_ema_slow'], adjust=False).mean()

        self.indicators_calculated = True
        print("HTS indicators ready")

    def generate_signals(self, data: pd.DataFrame, timestamp: datetime) -> Optional[StrategySignal]:
        """Generate signals with strategy-controlled SL/TP"""
        # Pre-calculate on first run
        if not self.indicators_calculated:
            self._precalculate_indicators(data)

        if self.m5_tf is None or self.h1_tf is None:
            return None

        # One position per day: Check if we already entered today
        current_date = timestamp.date()
        if self.last_entry_date == current_date:
            return None

        # Check H1 trend
        trend_bias = self._get_h1_trend_bias(data, timestamp)
        if trend_bias is None:
            return None

        # Check M5 entry
        signal = self._check_m5_entry(data, timestamp, trend_bias)

        # Add strategy-controlled SL/TP to signal metadata
        if signal:
            entry_price = signal.metadata['entry_price']
            sl_level = signal.metadata['sl_level']

            # IMPORTANT: Set SL in metadata (overrides UI)
            signal.metadata['sl_price'] = sl_level
            signal.metadata['partial_exits'] = self.config['partial_exits']

            # Record entry date to prevent multiple entries today
            self.last_entry_date = current_date

        return signal

    def _get_h1_trend_bias(self, data: pd.DataFrame, timestamp: datetime) -> Optional[str]:
        """Determine H1 trend bias using Pivot P and EMA crossover"""
        current_row = data[data['timestamp'] == timestamp]
        if current_row.empty:
            return None
        row = current_row.iloc[0]

        # Get H1 data
        h1_close = row.get(f'{self.h1_tf}_close')
        h1_high = row.get(f'{self.h1_tf}_high')
        h1_low = row.get(f'{self.h1_tf}_low')

        if pd.isna(h1_close) or pd.isna(h1_high) or pd.isna(h1_low):
            return None

        # Pivot point
        pivot_p = (h1_high + h1_low + h1_close) / 3

        # Get EMAs at current timestamp
        idx = current_row.index[0]
        ema33_high = self.h1_ema33_high.iloc[idx]
        ema33_low = self.h1_ema33_low.iloc[idx]
        ema144_high = self.h1_ema144_high.iloc[idx]
        ema144_low = self.h1_ema144_low.iloc[idx]

        if pd.isna(ema33_high) or pd.isna(ema144_high):
            return None

        # Trend logic
        price_above_pivot = h1_close > pivot_p
        ema33_above_ema144 = (ema33_high > ema144_high) and (ema33_low > ema144_low)

        if price_above_pivot and ema33_above_ema144:
            return 'bullish'
        elif not price_above_pivot and not ema33_above_ema144:
            return 'bearish'

        return None

    def _check_m5_entry(self, data: pd.DataFrame, timestamp: datetime, trend_bias: str) -> Optional[StrategySignal]:
        """Check M5 entry: retest EMA133, return to EMA33"""
        current_row = data[data['timestamp'] == timestamp]
        if current_row.empty:
            return None
        row = current_row.iloc[0]

        m5_high = row.get('high')
        m5_low = row.get('low')
        m5_close = row.get('close')

        if pd.isna(m5_high) or pd.isna(m5_low) or pd.isna(m5_close):
            return None

        # Get EMAs at current timestamp
        idx = current_row.index[0]
        ema33_high = self.m5_ema33_high.iloc[idx]
        ema33_low = self.m5_ema33_low.iloc[idx]
        ema133_high = self.m5_ema133_high.iloc[idx]
        ema133_low = self.m5_ema133_low.iloc[idx]

        if pd.isna(ema33_high) or pd.isna(ema133_high):
            return None

        # LONG setup
        if trend_bias == 'bullish':
            if m5_low <= ema133_low * 1.002:
                self.in_retest = True
                self.retest_low = m5_low

            if self.in_retest and m5_close > ema33_low:
                self.in_retest = False

                # SL: Place BELOW the farthest EMA (EMA133 for longs)
                # Add small buffer to ensure we're actually below the EMA
                sl_level = ema133_low * 0.998

                # Ensure SL is meaningfully below entry (at least 0.3%)
                min_sl = m5_close * 0.997
                if sl_level >= min_sl:
                    sl_level = min_sl

                return StrategySignal(
                    timestamp=timestamp,
                    side=PositionSide.LONG,
                    confidence=1.0,
                    metadata={
                        'entry_price': m5_close,
                        'sl_level': sl_level
                    }
                )

        # SHORT setup
        elif trend_bias == 'bearish':
            if m5_high >= ema133_high * 0.998:
                self.in_retest = True
                self.retest_high = m5_high

            if self.in_retest and m5_close < ema33_high:
                self.in_retest = False

                # SL: Place ABOVE the farthest EMA (EMA133 for shorts)
                # Add small buffer to ensure we're actually above the EMA
                sl_level = ema133_high * 1.002

                # Ensure SL is meaningfully above entry (at least 0.3%)
                max_sl = m5_close * 1.003
                if sl_level <= max_sl:
                    sl_level = max_sl

                return StrategySignal(
                    timestamp=timestamp,
                    side=PositionSide.SHORT,
                    confidence=1.0,
                    metadata={
                        'entry_price': m5_close,
                        'sl_level': sl_level
                    }
                )

        return None

    def should_exit(self, position: Position, data: pd.DataFrame, timestamp: datetime) -> bool:
        """Exit logic (handled by partial exits in position manager)"""
        return False
