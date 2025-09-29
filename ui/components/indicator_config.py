"""
Indicator configuration UI components.
Provides interactive controls for configuring indicators.
"""

import streamlit as st
import sys
import os
from typing import Dict, Any, List
from datetime import time

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.indicators import PivotPoints
from .indicator_defaults import get_indicator_defaults, get_indicator_ui_config, DEFAULT_COLORS


class IndicatorConfigManager:
    """Manages indicator configurations and UI components."""

    def __init__(self):
        self.available_indicators = {
            'Pivot Points': PivotPoints
        }

    def get_available_indicators(self) -> List[str]:
        """Get list of available indicator names."""
        return list(self.available_indicators.keys())

    def get_default_config(self, indicator_name: str) -> Dict[str, Any]:
        """
        Get default configuration for an indicator.

        Args:
            indicator_name: Name of the indicator

        Returns:
            Dictionary with default configuration
        """
        defaults = get_indicator_defaults()
        return defaults.get(indicator_name, {})

    def create_indicator_config_ui(self, indicator_name: str, key_prefix: str = "") -> Dict[str, Any]:
        """
        Create UI controls for indicator configuration.

        Args:
            indicator_name: Name of the indicator
            key_prefix: Prefix for Streamlit component keys

        Returns:
            Dictionary with configuration values
        """
        if indicator_name not in self.available_indicators:
            st.error(f"Unknown indicator: {indicator_name}")
            return {}

        indicator_class = self.available_indicators[indicator_name]

        if indicator_name == 'Pivot Points':
            return self._create_pivot_points_config(key_prefix)

        return {}

    def _create_pivot_points_config(self, key_prefix: str) -> Dict[str, Any]:
        """Create configuration UI for Pivot Points."""
        config = {}
        defaults = self.get_default_config('Pivot Points')

        st.subheader("⚙️ Pivot Points Configuration")

        # Time range settings
        col1, col2 = st.columns(2)
        with col1:
            start_time = st.time_input(
                "Daily Start Time",
                value=time(0, 0),
                help="Start time for daily OHLC calculation",
                key=f"{key_prefix}_pivot_start_time"
            )
            config['start_time'] = start_time.strftime('%H:%M')

        with col2:
            end_time = st.time_input(
                "Daily End Time",
                value=time(23, 59),
                help="End time for daily OHLC calculation",
                key=f"{key_prefix}_pivot_end_time"
            )
            config['end_time'] = end_time.strftime('%H:%M')

        # Color settings
        st.markdown("**🎨 Color Settings**")
        col1, col2, col3 = st.columns(3)

        with col1:
            pivot_color = st.selectbox(
                "Pivot Point Color",
                options=DEFAULT_COLORS['pivot']['options'],
                format_func=lambda x: DEFAULT_COLORS['pivot']['labels'][x],
                index=DEFAULT_COLORS['pivot']['options'].index(defaults['colors']['pivot']),
                key=f"{key_prefix}_pivot_color"
            )

        with col2:
            support_color = st.selectbox(
                "Support Color",
                options=DEFAULT_COLORS['support']['options'],
                format_func=lambda x: DEFAULT_COLORS['support']['labels'][x],
                index=DEFAULT_COLORS['support']['options'].index(defaults['colors']['support']),
                key=f"{key_prefix}_support_color"
            )

        with col3:
            resistance_color = st.selectbox(
                "Resistance Color",
                options=DEFAULT_COLORS['resistance']['options'],
                format_func=lambda x: DEFAULT_COLORS['resistance']['labels'][x],
                index=DEFAULT_COLORS['resistance']['options'].index(defaults['colors']['resistance']),
                key=f"{key_prefix}_resistance_color"
            )

        config['colors'] = {
            'pivot': pivot_color,
            'support': support_color,
            'resistance': resistance_color
        }

        # Level selection
        st.markdown("**📊 Levels to Display**")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("*Core Levels:*")
            show_pivot = st.checkbox("Pivot Point (P)", value=defaults['show_levels']['P'], key=f"{key_prefix}_show_P")
            show_s1 = st.checkbox("Support 1 (S1)", value=defaults['show_levels']['S1'], key=f"{key_prefix}_show_S1")
            show_s2 = st.checkbox("Support 2 (S2)", value=defaults['show_levels']['S2'], key=f"{key_prefix}_show_S2")
            show_s3 = st.checkbox("Support 3 (S3)", value=defaults['show_levels']['S3'], key=f"{key_prefix}_show_S3")

        with col2:
            st.markdown("*Resistance Levels:*")
            show_r1 = st.checkbox("Resistance 1 (R1)", value=defaults['show_levels']['R1'], key=f"{key_prefix}_show_R1")
            show_r2 = st.checkbox("Resistance 2 (R2)", value=defaults['show_levels']['R2'], key=f"{key_prefix}_show_R2")
            show_r3 = st.checkbox("Resistance 3 (R3)", value=defaults['show_levels']['R3'], key=f"{key_prefix}_show_R3")

        # Extended levels (collapsed by default)
        with st.expander("Extended Levels (R4, R5, S4, S5)"):
            col1, col2 = st.columns(2)
            with col1:
                show_s4 = st.checkbox("Support 4 (S4)", value=defaults['show_levels']['S4'], key=f"{key_prefix}_show_S4")
                show_s5 = st.checkbox("Support 5 (S5)", value=defaults['show_levels']['S5'], key=f"{key_prefix}_show_S5")
            with col2:
                show_r4 = st.checkbox("Resistance 4 (R4)", value=defaults['show_levels']['R4'], key=f"{key_prefix}_show_R4")
                show_r5 = st.checkbox("Resistance 5 (R5)", value=defaults['show_levels']['R5'], key=f"{key_prefix}_show_R5")

        config['show_levels'] = {
            'P': show_pivot,
            'S1': show_s1, 'S2': show_s2, 'S3': show_s3, 'S4': show_s4, 'S5': show_s5,
            'R1': show_r1, 'R2': show_r2, 'R3': show_r3, 'R4': show_r4, 'R5': show_r5
        }

        return config

    def create_indicator(self, indicator_name: str, config: Dict[str, Any]):
        """
        Create an indicator instance with given configuration.

        Args:
            indicator_name: Name of the indicator
            config: Configuration dictionary

        Returns:
            Configured indicator instance
        """
        if indicator_name not in self.available_indicators:
            raise ValueError(f"Unknown indicator: {indicator_name}")

        indicator_class = self.available_indicators[indicator_name]
        return indicator_class(config)


def show_indicator_config_panel():
    """Show the indicator configuration panel."""
    st.header("🔧 Indicator Configuration")

    manager = IndicatorConfigManager()
    available_indicators = manager.get_available_indicators()

    if not available_indicators:
        st.info("No indicators available.")
        return None, None

    # Indicator selection
    selected_indicator = st.selectbox(
        "Select Indicator:",
        options=available_indicators,
        help="Choose an indicator to configure"
    )

    if selected_indicator:
        # Create configuration UI
        config = manager.create_indicator_config_ui(selected_indicator, "main")

        # Create indicator instance
        indicator = manager.create_indicator(selected_indicator, config)

        return indicator, config

    return None, None