"""
Default settings for indicators.
Centralized configuration to avoid code duplication and provide consistent defaults.
"""

from datetime import time
from typing import Dict, Any


# Default color palettes
DEFAULT_COLORS = {
    'pivot': {
        'options': ['#FFFFFF', '#FFFF00', '#FF00FF'],
        'labels': {'#FFFFFF': 'White', '#FFFF00': 'Yellow', '#FF00FF': 'Magenta'},
        'default': '#FFFFFF'
    },
    'support': {
        'options': ['#FF0000', '#FF4500', '#DC143C'],
        'labels': {'#FF0000': 'Red', '#FF4500': 'Orange Red', '#DC143C': 'Crimson'},
        'default': '#FF0000'
    },
    'resistance': {
        'options': ['#00FF00', '#32CD32', '#228B22'],
        'labels': {'#00FF00': 'Green', '#32CD32': 'Lime Green', '#228B22': 'Forest Green'},
        'default': '#00FF00'
    }
}


def get_indicator_defaults() -> Dict[str, Dict[str, Any]]:
    """
    Get default settings for all indicators.

    Returns:
        Dictionary with default settings for each indicator
    """
    return {
        'Pivot Points': {
            'enabled': False,
            'start_time': '06:00',
            'end_time': '20:00',
            'colors': {
                'pivot': DEFAULT_COLORS['pivot']['default'],
                'support': DEFAULT_COLORS['support']['default'],
                'resistance': DEFAULT_COLORS['resistance']['default']
            },
            'show_levels': {
                'P': True,
                'S1': True, 'S2': True, 'S3': True, 'S4': False, 'S5': False,
                'R1': True, 'R2': True, 'R3': True, 'R4': False, 'R5': False
            }
        },
        'HTS': {
            'enabled': False,
            'channel1_period': 33,
            'channel2_period': 144,
            'channel1_source_high': 'high',
            'channel1_source_low': 'low',
            'channel2_source_high': 'high',
            'channel2_source_low': 'low',
            'colors': {
                'channel1': '#00FF00',  # Green
                'channel2': '#FF0000'   # Red
            },
            'show_channels': {
                'channel1': True,
                'channel2': True
            }
        }
    }


def get_indicator_ui_config() -> Dict[str, Dict[str, Any]]:
    """
    Get UI configuration for indicators.
    Defines how each indicator's settings should be displayed.

    Returns:
        Dictionary with UI configuration for each indicator
    """
    return {
        'Pivot Points': {
            'sections': [
                {
                    'title': '⏰ Time Range Settings',
                    'type': 'time_range',
                    'fields': [
                        {
                            'key': 'start_time',
                            'label': 'Daily Start Time',
                            'type': 'time',
                            'default': time(0, 0),
                            'help': 'Start time for daily OHLC calculation'
                        },
                        {
                            'key': 'end_time',
                            'label': 'Daily End Time',
                            'type': 'time',
                            'default': time(23, 59),
                            'help': 'End time for daily OHLC calculation'
                        }
                    ]
                },
                {
                    'title': '🎨 Color Settings',
                    'type': 'color_group',
                    'fields': [
                        {
                            'key': 'colors.pivot',
                            'label': 'Pivot Point Color',
                            'type': 'color_select',
                            'options': DEFAULT_COLORS['pivot']['options'],
                            'labels': DEFAULT_COLORS['pivot']['labels'],
                            'default': DEFAULT_COLORS['pivot']['default']
                        },
                        {
                            'key': 'colors.support',
                            'label': 'Support Color',
                            'type': 'color_select',
                            'options': DEFAULT_COLORS['support']['options'],
                            'labels': DEFAULT_COLORS['support']['labels'],
                            'default': DEFAULT_COLORS['support']['default']
                        },
                        {
                            'key': 'colors.resistance',
                            'label': 'Resistance Color',
                            'type': 'color_select',
                            'options': DEFAULT_COLORS['resistance']['options'],
                            'labels': DEFAULT_COLORS['resistance']['labels'],
                            'default': DEFAULT_COLORS['resistance']['default']
                        }
                    ]
                },
                {
                    'title': '📊 Core Levels',
                    'type': 'checkbox_group',
                    'fields': [
                        {'key': 'show_levels.P', 'label': 'Pivot Point (P)', 'default': True},
                        {'key': 'show_levels.S1', 'label': 'Support 1 (S1)', 'default': True},
                        {'key': 'show_levels.S2', 'label': 'Support 2 (S2)', 'default': True},
                        {'key': 'show_levels.S3', 'label': 'Support 3 (S3)', 'default': True},
                        {'key': 'show_levels.R1', 'label': 'Resistance 1 (R1)', 'default': True},
                        {'key': 'show_levels.R2', 'label': 'Resistance 2 (R2)', 'default': True},
                        {'key': 'show_levels.R3', 'label': 'Resistance 3 (R3)', 'default': True}
                    ]
                },
                {
                    'title': '📈 Extended Levels',
                    'type': 'checkbox_group',
                    'expandable': True,
                    'fields': [
                        {'key': 'show_levels.S4', 'label': 'Support 4 (S4)', 'default': False},
                        {'key': 'show_levels.S5', 'label': 'Support 5 (S5)', 'default': False},
                        {'key': 'show_levels.R4', 'label': 'Resistance 4 (R4)', 'default': False},
                        {'key': 'show_levels.R5', 'label': 'Resistance 5 (R5)', 'default': False}
                    ]
                }
            ]
        },
        'HTS': {
            'sections': [
                {
                    'title': '📈 Channel 1 Settings (EMA33)',
                    'type': 'channel_group',
                    'fields': [
                        {
                            'key': 'channel1_period',
                            'label': 'Channel 1 Period',
                            'type': 'number',
                            'default': 33,
                            'min': 2,
                            'max': 200,
                            'help': 'Period for Channel 1 EMA calculation'
                        },
                        {
                            'key': 'channel1_source_high',
                            'label': 'High Line Source',
                            'type': 'selectbox',
                            'options': ['high', 'close', 'open'],
                            'default': 'high',
                            'help': 'Data source for Channel 1 high line'
                        },
                        {
                            'key': 'channel1_source_low',
                            'label': 'Low Line Source',
                            'type': 'selectbox',
                            'options': ['low', 'close', 'open'],
                            'default': 'low',
                            'help': 'Data source for Channel 1 low line'
                        }
                    ]
                },
                {
                    'title': '📊 Channel 2 Settings (EMA144)',
                    'type': 'channel_group',
                    'fields': [
                        {
                            'key': 'channel2_period',
                            'label': 'Channel 2 Period',
                            'type': 'number',
                            'default': 144,
                            'min': 2,
                            'max': 500,
                            'help': 'Period for Channel 2 EMA calculation'
                        },
                        {
                            'key': 'channel2_source_high',
                            'label': 'High Line Source',
                            'type': 'selectbox',
                            'options': ['high', 'close', 'open'],
                            'default': 'high',
                            'help': 'Data source for Channel 2 high line'
                        },
                        {
                            'key': 'channel2_source_low',
                            'label': 'Low Line Source',
                            'type': 'selectbox',
                            'options': ['low', 'close', 'open'],
                            'default': 'low',
                            'help': 'Data source for Channel 2 low line'
                        }
                    ]
                },
                {
                    'title': '🎨 Colors & Visibility',
                    'type': 'display_group',
                    'fields': [
                        {
                            'key': 'colors.channel1',
                            'label': 'Channel 1 Color',
                            'type': 'color_picker',
                            'default': '#00FF00',
                            'help': 'Color for Channel 1 (EMA33) lines'
                        },
                        {
                            'key': 'colors.channel2',
                            'label': 'Channel 2 Color',
                            'type': 'color_picker',
                            'default': '#FF0000',
                            'help': 'Color for Channel 2 (EMA144) lines'
                        },
                        {
                            'key': 'show_channels.channel1',
                            'label': 'Show Channel 1',
                            'type': 'checkbox',
                            'default': True,
                            'help': 'Display Channel 1 (EMA33) lines'
                        },
                        {
                            'key': 'show_channels.channel2',
                            'label': 'Show Channel 2',
                            'type': 'checkbox',
                            'default': True,
                            'help': 'Display Channel 2 (EMA144) lines'
                        }
                    ]
                }
            ]
        }
    }