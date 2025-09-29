"""
HTS indicator with dual EMA channels.
Uses two channels of EMAs calculated on high/low prices.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .base import BaseIndicator


class HTS(BaseIndicator):
    """
    HTS indicator with dual EMA channels.

    Channel 1: EMA33 High/Low
    Channel 2: EMA144 High/Low
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("HTS", config)

        # Default configuration
        self.channel1_period = self.config.get('channel1_period', 33)
        self.channel2_period = self.config.get('channel2_period', 144)
        self.channel1_source_high = self.config.get('channel1_source_high', 'high')
        self.channel1_source_low = self.config.get('channel1_source_low', 'low')
        self.channel2_source_high = self.config.get('channel2_source_high', 'high')
        self.channel2_source_low = self.config.get('channel2_source_low', 'low')

        # Colors
        self.colors = self.config.get('colors', {
            'channel1': '#00FF00',  # Green
            'channel2': '#FF0000'   # Red
        })

        # Visibility
        self.show_channels = self.config.get('show_channels', {
            'channel1': True,
            'channel2': True
        })

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate EMA channels.

        Args:
            data: DataFrame with OHLC data

        Returns:
            DataFrame with calculated EMA channels
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data format for HTS indicator")

        self.data = data.copy()

        # Calculate Channel 1 EMAs
        if self.show_channels['channel1']:
            self.data[f'ema{self.channel1_period}_high'] = self._calculate_ema(
                data[self.channel1_source_high], self.channel1_period
            )
            self.data[f'ema{self.channel1_period}_low'] = self._calculate_ema(
                data[self.channel1_source_low], self.channel1_period
            )

        # Calculate Channel 2 EMAs
        if self.show_channels['channel2']:
            self.data[f'ema{self.channel2_period}_high'] = self._calculate_ema(
                data[self.channel2_source_high], self.channel2_period
            )
            self.data[f'ema{self.channel2_period}_low'] = self._calculate_ema(
                data[self.channel2_source_low], self.channel2_period
            )

        self.calculated = True
        return self.data

    def _calculate_ema(self, prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average.

        Args:
            prices: Price series
            period: EMA period

        Returns:
            EMA series
        """
        return prices.ewm(span=period, adjust=False).mean()

    def get_plot_data(self) -> Dict[str, Any]:
        """
        Get data formatted for plotting.

        Returns:
            Dictionary with plot configuration and data
        """
        if not self.calculated or self.data is None:
            return {'traces': [], 'layout_updates': {}}

        traces = []

        # Channel 1 traces
        if self.show_channels['channel1']:
            # EMA33 High
            if f'ema{self.channel1_period}_high' in self.data.columns:
                traces.append({
                    'type': 'scatter',
                    'x': self.data['timestamp'],
                    'y': self.data[f'ema{self.channel1_period}_high'],
                    'mode': 'lines',
                    'name': f'EMA{self.channel1_period} High',
                    'line': {
                        'color': self.colors['channel1'],
                        'width': 2,
                        'dash': 'solid'
                    },
                    'showlegend': True,
                    'hovertemplate': f'EMA{self.channel1_period} High: %{{y:.4f}}<br>%{{x}}<extra></extra>'
                })

            # EMA33 Low
            if f'ema{self.channel1_period}_low' in self.data.columns:
                traces.append({
                    'type': 'scatter',
                    'x': self.data['timestamp'],
                    'y': self.data[f'ema{self.channel1_period}_low'],
                    'mode': 'lines',
                    'name': f'EMA{self.channel1_period} Low',
                    'line': {
                        'color': self.colors['channel1'],
                        'width': 2,
                        'dash': 'dot'
                    },
                    'showlegend': True,
                    'hovertemplate': f'EMA{self.channel1_period} Low: %{{y:.4f}}<br>%{{x}}<extra></extra>'
                })

        # Channel 2 traces
        if self.show_channels['channel2']:
            # EMA144 High
            if f'ema{self.channel2_period}_high' in self.data.columns:
                traces.append({
                    'type': 'scatter',
                    'x': self.data['timestamp'],
                    'y': self.data[f'ema{self.channel2_period}_high'],
                    'mode': 'lines',
                    'name': f'EMA{self.channel2_period} High',
                    'line': {
                        'color': self.colors['channel2'],
                        'width': 2,
                        'dash': 'solid'
                    },
                    'showlegend': True,
                    'hovertemplate': f'EMA{self.channel2_period} High: %{{y:.4f}}<br>%{{x}}<extra></extra>'
                })

            # EMA144 Low
            if f'ema{self.channel2_period}_low' in self.data.columns:
                traces.append({
                    'type': 'scatter',
                    'x': self.data['timestamp'],
                    'y': self.data[f'ema{self.channel2_period}_low'],
                    'mode': 'lines',
                    'name': f'EMA{self.channel2_period} Low',
                    'line': {
                        'color': self.colors['channel2'],
                        'width': 2,
                        'dash': 'dot'
                    },
                    'showlegend': True,
                    'hovertemplate': f'EMA{self.channel2_period} Low: %{{y:.4f}}<br>%{{x}}<extra></extra>'
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
            'name': self.name,
            'parameters': {
                'channel1_period': {
                    'type': 'integer',
                    'default': 33,
                    'min': 2,
                    'max': 200,
                    'description': 'Channel 1 EMA period'
                },
                'channel2_period': {
                    'type': 'integer',
                    'default': 144,
                    'min': 2,
                    'max': 500,
                    'description': 'Channel 2 EMA period'
                },
                'channel1_source_high': {
                    'type': 'select',
                    'default': 'high',
                    'options': ['high', 'close', 'open'],
                    'description': 'Channel 1 high line data source'
                },
                'channel1_source_low': {
                    'type': 'select',
                    'default': 'low',
                    'options': ['low', 'close', 'open'],
                    'description': 'Channel 1 low line data source'
                },
                'channel2_source_high': {
                    'type': 'select',
                    'default': 'high',
                    'options': ['high', 'close', 'open'],
                    'description': 'Channel 2 high line data source'
                },
                'channel2_source_low': {
                    'type': 'select',
                    'default': 'low',
                    'options': ['low', 'close', 'open'],
                    'description': 'Channel 2 low line data source'
                },
                'colors': {
                    'type': 'color_group',
                    'default': {
                        'channel1': '#00FF00',
                        'channel2': '#FF0000'
                    },
                    'description': 'Channel colors'
                },
                'show_channels': {
                    'type': 'checkbox_group',
                    'default': {
                        'channel1': True,
                        'channel2': True
                    },
                    'description': 'Channel visibility'
                }
            }
        }