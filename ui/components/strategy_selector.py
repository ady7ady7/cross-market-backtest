"""
Strategy Selector Component

Automatically detects available strategies and shows their requirements.
"""

import streamlit as st
from typing import Dict, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.strategies import list_strategies, get_strategy_class


def show_strategy_selector(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Show strategy selector with auto-detected requirements.

    Returns:
        Updated config with strategy selection and parameters
    """
    st.markdown("**🎯 Strategy Selection**")

    # Get all available strategies
    strategies = list_strategies()

    if not strategies:
        st.error("No strategies available!")
        return config

    # Create strategy options
    strategy_options = {
        f"{meta.name}": strategy_id
        for strategy_id, meta in strategies.items()
    }

    selected_name = st.selectbox(
        "Select Strategy",
        options=list(strategy_options.keys()),
        help="Choose a trading strategy"
    )

    selected_id = strategy_options[selected_name]
    metadata = strategies[selected_id]

    # Show strategy info
    with st.expander("ℹ️ Strategy Information", expanded=True):
        st.info(metadata.description)

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**Required Timeframes:**")
            if metadata.required_timeframes:
                for tf in metadata.required_timeframes:
                    st.markdown(f"- `{tf}`")
            else:
                st.markdown("- Any timeframe")

        with col2:
            st.markdown("**SL/TP Control:**")
            if metadata.uses_custom_sl:
                st.markdown(f"- **SL**: Strategy-controlled (at retest level)")
            else:
                st.markdown(f"- **SL**: Your settings ({metadata.default_sl_type})")

            if metadata.uses_custom_tp:
                st.markdown(f"- **TP**: Strategy-controlled (partial exits)")
            else:
                st.markdown(f"- **TP**: Your settings ({metadata.default_tp_type})")

    # Auto-select required timeframes if specified
    if metadata.required_timeframes:
        config['required_timeframes'] = metadata.required_timeframes
        st.info(f"📌 This strategy requires timeframes: {', '.join(metadata.required_timeframes)}")

    # Show configurable parameters
    strategy_params = {}
    if metadata.configurable_params:
        st.markdown("**⚙️ Strategy Parameters**")

        for param_name, param_info in metadata.configurable_params.items():
            if param_info['type'] == 'number':
                strategy_params[param_name] = st.number_input(
                    param_info['label'],
                    min_value=param_info.get('min', 1),
                    max_value=param_info.get('max', 1000),
                    value=param_info['default'],
                    help=param_info.get('help', '')
                )

    config['strategy_id'] = selected_id
    config['strategy_metadata'] = metadata
    config['strategy_params'] = strategy_params

    return config
