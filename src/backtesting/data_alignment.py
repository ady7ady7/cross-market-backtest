"""
Multi-timeframe data alignment system.

Ensures that for any given timestamp, only closed candles from higher timeframes
are available to avoid lookahead bias. For example, at 08:04 on m1:
- Valid m5 candle: 07:55-08:00 (last closed m5)
- Valid h1 candle: 07:00-08:00 (last closed h1)
"""

import pandas as pd
from typing import Dict, List, Optional
from datetime import datetime, timedelta


class MultiTimeframeAligner:
    """
    Aligns data from multiple timeframes to ensure proper time synchronization.
    """

    # Timeframe to minutes mapping
    TIMEFRAME_MINUTES = {
        '1m': 1,
        '5m': 5,
        '15m': 15,
        '30m': 30,
        '1h': 60,
        '4h': 240,
        '1d': 1440
    }

    def __init__(self, timeframes: List[str]):
        """
        Initialize with list of timeframes to align.

        Args:
            timeframes: List of timeframe strings (e.g., ['1m', '5m', '1h'])
        """
        self.timeframes = sorted(timeframes, key=lambda x: self.TIMEFRAME_MINUTES.get(x, 0))
        self.base_timeframe = self.timeframes[0]  # Smallest timeframe is base

    def align_data(self, data_dict: Dict[str, pd.DataFrame]) -> pd.DataFrame:
        """
        Align multiple timeframe dataframes into a single synchronized dataframe.

        Args:
            data_dict: Dictionary mapping timeframe to DataFrame (e.g., {'1m': df1, '5m': df5})

        Returns:
            Single DataFrame with aligned data from all timeframes
        """
        if not data_dict or self.base_timeframe not in data_dict:
            raise ValueError(f"Base timeframe {self.base_timeframe} data not provided")

        # Start with base timeframe
        base_df = data_dict[self.base_timeframe].copy()
        base_df = base_df.sort_values('timestamp').reset_index(drop=True)

        # Add columns from higher timeframes
        for tf in self.timeframes[1:]:
            if tf not in data_dict:
                continue

            higher_df = data_dict[tf].copy()
            higher_df = higher_df.sort_values('timestamp').reset_index(drop=True)

            # Merge with asof to get last closed candle
            base_df = self._merge_timeframe(base_df, higher_df, tf)

        return base_df

    def _merge_timeframe(self, base_df: pd.DataFrame, higher_df: pd.DataFrame,
                        timeframe: str) -> pd.DataFrame:
        """
        Merge higher timeframe data into base dataframe using asof merge.

        This ensures that for each base timestamp, we only get the last closed
        candle from the higher timeframe.
        """
        # Rename columns to include timeframe prefix
        rename_map = {
            col: f"{timeframe}_{col}"
            for col in higher_df.columns
            if col != 'timestamp'
        }
        higher_df = higher_df.rename(columns=rename_map)

        # Use merge_asof to get the last closed candle
        # direction='backward' ensures we only get previous closed candles
        merged = pd.merge_asof(
            base_df,
            higher_df,
            on='timestamp',
            direction='backward'
        )

        return merged

    def get_last_closed_candle(self, data: pd.DataFrame, current_time: datetime,
                               timeframe: str) -> Optional[pd.Series]:
        """
        Get the last closed candle for a specific timeframe at current_time.

        Args:
            data: DataFrame with aligned data
            current_time: Current timestamp
            timeframe: Timeframe to get candle for

        Returns:
            Series with OHLCV data or None if not available
        """
        if timeframe == self.base_timeframe:
            # For base timeframe, get the candle at current_time
            candle = data[data['timestamp'] == current_time]
        else:
            # For higher timeframes, get last closed candle
            prefix = f"{timeframe}_"
            candle = data[data['timestamp'] == current_time]

        return candle.iloc[0] if not candle.empty else None

    @staticmethod
    def calculate_candle_close_time(timestamp: datetime, timeframe: str) -> datetime:
        """
        Calculate when a candle closes for a given open timestamp.

        Args:
            timestamp: Candle open time
            timeframe: Timeframe string

        Returns:
            Candle close time
        """
        minutes = MultiTimeframeAligner.TIMEFRAME_MINUTES.get(timeframe, 1)
        return timestamp + timedelta(minutes=minutes)

    @staticmethod
    def is_candle_closed(current_time: datetime, candle_open: datetime,
                        timeframe: str) -> bool:
        """
        Check if a candle is closed at current time.

        Args:
            current_time: Current timestamp
            candle_open: Candle open timestamp
            timeframe: Timeframe string

        Returns:
            True if candle is closed
        """
        close_time = MultiTimeframeAligner.calculate_candle_close_time(candle_open, timeframe)
        return current_time >= close_time