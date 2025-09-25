"""
Pivot Points indicator implementation.
Calculates Traditional Pivot Points based on previous day's OHLC data.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from datetime import time, datetime
from .base import BaseIndicator


class PivotPoints(BaseIndicator):
    """
    Traditional Pivot Points indicator.
    Calculates pivot point levels (P, S1-S5, R1-R5) based on previous day's data.
    """

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize Pivot Points indicator.

        Args:
            config: Configuration dictionary with:
                - start_time: Start time for daily calculation (default: "00:00")
                - end_time: End time for daily calculation (default: "23:59")
                - colors: Dictionary with colors for P, S, R levels
        """
        default_config = {
            'start_time': '00:00',
            'end_time': '23:59',
            'colors': {
                'pivot': '#FFFFFF',      # White for Pivot
                'support': '#FF0000',    # Red for Support
                'resistance': '#00FF00'  # Green for Resistance
            },
            'show_levels': {
                'P': True,
                'S1': True, 'S2': True, 'S3': True,
                'R1': True, 'R2': True, 'R3': True,
                'S4': False, 'S5': False,  # Optional extended levels
                'R4': False, 'R5': False
            }
        }

        if config:
            default_config.update(config)

        super().__init__("Pivot Points", default_config)

    def _parse_time(self, time_str: str) -> time:
        """Parse time string to time object."""
        try:
            return datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            return datetime.strptime('00:00', '%H:%M').time()

    def _filter_daily_data(self, data: pd.DataFrame, date: pd.Timestamp) -> pd.DataFrame:
        """
        Filter data for a specific date within configured time range.

        Args:
            data: OHLCV data
            date: Target date

        Returns:
            Filtered DataFrame for the specified date and time range
        """
        start_time = self._parse_time(self.config['start_time'])
        end_time = self._parse_time(self.config['end_time'])

        # Filter for specific date
        date_data = data[data['timestamp'].dt.date == date.date()].copy()

        if date_data.empty:
            return date_data

        # Filter by time range
        if start_time <= end_time:
            # Same day range
            mask = (date_data['timestamp'].dt.time >= start_time) & \
                   (date_data['timestamp'].dt.time <= end_time)
        else:
            # Overnight range (crosses midnight)
            mask = (date_data['timestamp'].dt.time >= start_time) | \
                   (date_data['timestamp'].dt.time <= end_time)

        return date_data[mask]

    def _calculate_daily_ohlc(self, data: pd.DataFrame, date: pd.Timestamp) -> Tuple[float, float, float, float]:
        """
        Calculate daily OHLC values for a specific date.

        Args:
            data: OHLCV data
            date: Target date

        Returns:
            Tuple of (open, high, low, close) for the day
        """
        daily_data = self._filter_daily_data(data, date)

        if daily_data.empty:
            return None, None, None, None

        # Sort by timestamp to get correct open/close
        daily_data = daily_data.sort_values('timestamp')

        open_price = daily_data.iloc[0]['open']
        high_price = daily_data['high'].max()
        low_price = daily_data['low'].min()
        close_price = daily_data.iloc[-1]['close']

        return open_price, high_price, low_price, close_price

    def _calculate_pivot_levels(self, prev_high: float, prev_low: float, prev_close: float) -> Dict[str, float]:
        """
        Calculate all pivot levels using Traditional formula.

        Args:
            prev_high: Previous day's high
            prev_low: Previous day's low
            prev_close: Previous day's close

        Returns:
            Dictionary with all pivot levels
        """
        # Traditional Pivot Point calculation
        P = (prev_high + prev_low + prev_close) / 3

        # Primary levels
        R1 = P * 2 - prev_low
        S1 = P * 2 - prev_high
        R2 = P + (prev_high - prev_low)
        S2 = P - (prev_high - prev_low)
        R3 = P * 2 + (prev_high - 2 * prev_low)
        S3 = P * 2 - (2 * prev_high - prev_low)

        # Extended levels (optional)
        R4 = P * 3 + (prev_high - 3 * prev_low)
        S4 = P * 3 - (3 * prev_high - prev_low)
        R5 = P * 4 + (prev_high - 4 * prev_low)
        S5 = P * 4 - (4 * prev_high - prev_low)

        return {
            'P': P,
            'R1': R1, 'R2': R2, 'R3': R3, 'R4': R4, 'R5': R5,
            'S1': S1, 'S2': S2, 'S3': S3, 'S4': S4, 'S5': S5
        }

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate pivot points for all trading days.

        Args:
            data: OHLCV DataFrame

        Returns:
            DataFrame with pivot levels for each timestamp
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data format. Required columns: timestamp, open, high, low, close")

        data = data.copy()
        data['timestamp'] = pd.to_datetime(data['timestamp'])
        data = data.sort_values('timestamp')

        # Get unique dates
        dates = data['timestamp'].dt.date.unique()
        dates = sorted(dates)

        # Initialize result DataFrame
        result_data = []

        for i, current_date in enumerate(dates[1:], 1):  # Start from second date
            prev_date = dates[i-1]

            # Calculate previous day's OHLC
            prev_open, prev_high, prev_low, prev_close = self._calculate_daily_ohlc(
                data, pd.Timestamp(prev_date)
            )

            if prev_high is None or prev_low is None or prev_close is None:
                continue

            # Calculate pivot levels
            levels = self._calculate_pivot_levels(prev_high, prev_low, prev_close)

            # Get all timestamps for current date
            current_day_data = data[data['timestamp'].dt.date == current_date]

            for _, row in current_day_data.iterrows():
                result_row = {
                    'timestamp': row['timestamp'],
                    'date': current_date
                }
                result_row.update(levels)
                result_data.append(result_row)

        if not result_data:
            # Return empty DataFrame with proper structure
            columns = ['timestamp', 'date', 'P', 'R1', 'R2', 'R3', 'R4', 'R5', 'S1', 'S2', 'S3', 'S4', 'S5']
            return pd.DataFrame(columns=columns)

        result_df = pd.DataFrame(result_data)
        self.data = result_df
        self.calculated = True

        return result_df

    def get_plot_data(self) -> Dict[str, Any]:
        """
        Get pivot points data formatted for plotting.

        Returns:
            Dictionary with plot traces for each pivot level
        """
        if not self.calculated or self.data is None or self.data.empty:
            return {'traces': [], 'layout_updates': {}}

        traces = []
        show_levels = self.config['show_levels']
        colors = self.config['colors']

        # Define level groups and their colors
        level_config = {
            'P': {'color': colors['pivot'], 'name': 'Pivot Point', 'dash': 'solid'},
            'R1': {'color': colors['resistance'], 'name': 'Resistance 1', 'dash': 'solid'},
            'R2': {'color': colors['resistance'], 'name': 'Resistance 2', 'dash': 'dash'},
            'R3': {'color': colors['resistance'], 'name': 'Resistance 3', 'dash': 'dot'},
            'R4': {'color': colors['resistance'], 'name': 'Resistance 4', 'dash': 'dashdot'},
            'R5': {'color': colors['resistance'], 'name': 'Resistance 5', 'dash': 'longdash'},
            'S1': {'color': colors['support'], 'name': 'Support 1', 'dash': 'solid'},
            'S2': {'color': colors['support'], 'name': 'Support 2', 'dash': 'dash'},
            'S3': {'color': colors['support'], 'name': 'Support 3', 'dash': 'dot'},
            'S4': {'color': colors['support'], 'name': 'Support 4', 'dash': 'dashdot'},
            'S5': {'color': colors['support'], 'name': 'Support 5', 'dash': 'longdash'}
        }

        for level, config in level_config.items():
            if show_levels.get(level, False) and level in self.data.columns:
                traces.append({
                    'type': 'scatter',
                    'mode': 'lines',
                    'x': self.data['timestamp'],
                    'y': self.data[level],
                    'name': config['name'],
                    'line': {
                        'color': config['color'],
                        'width': 1,
                        'dash': config['dash']
                    },
                    'showlegend': True,
                    'hovertemplate': f"{config['name']}: %{{y:.4f}}<br>Time: %{{x}}<extra></extra>"
                })

        return {
            'traces': traces,
            'layout_updates': {}
        }

    def get_config_schema(self) -> Dict[str, Any]:
        """
        Get configuration schema for UI generation.

        Returns:
            Dictionary describing configuration options
        """
        return {
            'name': 'Pivot Points',
            'parameters': {
                'start_time': {
                    'type': 'time',
                    'label': 'Daily Start Time',
                    'default': '00:00',
                    'help': 'Start time for daily OHLC calculation'
                },
                'end_time': {
                    'type': 'time',
                    'label': 'Daily End Time',
                    'default': '23:59',
                    'help': 'End time for daily OHLC calculation'
                },
                'pivot_color': {
                    'type': 'color',
                    'label': 'Pivot Point Color',
                    'default': '#FFFFFF',
                    'help': 'Color for pivot point line'
                },
                'support_color': {
                    'type': 'color',
                    'label': 'Support Color',
                    'default': '#FF0000',
                    'help': 'Color for support levels'
                },
                'resistance_color': {
                    'type': 'color',
                    'label': 'Resistance Color',
                    'default': '#00FF00',
                    'help': 'Color for resistance levels'
                },
                'show_levels': {
                    'type': 'multiselect',
                    'label': 'Show Levels',
                    'options': ['P', 'S1', 'S2', 'S3', 'S4', 'S5', 'R1', 'R2', 'R3', 'R4', 'R5'],
                    'default': ['P', 'S1', 'S2', 'S3', 'R1', 'R2', 'R3'],
                    'help': 'Select which pivot levels to display'
                }
            }
        }