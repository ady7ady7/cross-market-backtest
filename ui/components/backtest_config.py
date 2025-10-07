"""
Backtesting configuration UI components.

Provides interface for configuring and running backtests.
"""

import streamlit as st
import sys
import os
from typing import Dict, List, Any
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import symbols_config


class BacktestConfig:
    """Manages backtest configuration UI"""

    @staticmethod
    def show_config_ui() -> Dict[str, Any]:
        """
        Display backtesting configuration UI.

        Returns:
            Dictionary with configuration parameters
        """
        st.subheader("⚙️ Backtest Configuration")

        config = {}

        # Symbol and timeframe selection
        col1, col2 = st.columns(2)

        with col1:
            used_symbols = symbols_config.get_active_symbols()
            if not used_symbols:
                st.warning("No symbols available. Configure symbols in Symbol Management tab.")
                return None

            config['symbol'] = st.selectbox(
                "Symbol",
                used_symbols,
                help="Select symbol to backtest"
            )

        with col2:
            # Get available timeframes
            if st.session_state.metadata_df is not None and config.get('symbol'):
                symbol_data = st.session_state.metadata_df[
                    st.session_state.metadata_df['symbol'] == config['symbol']
                ]
                available_tfs = sorted(symbol_data['timeframe'].unique())
            else:
                available_tfs = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']

            config['timeframes'] = st.multiselect(
                "Timeframes",
                available_tfs,
                default=[available_tfs[0]] if available_tfs else [],
                help="Select timeframes for strategy (first will be base timeframe)"
            )

        if not config.get('timeframes'):
            st.info("Please select at least one timeframe")
            return None

        # Date range selection
        st.markdown("---")
        st.markdown("**📅 Date Range**")

        use_full_range = st.checkbox("Use full data range", value=True)

        if not use_full_range:
            col1, col2 = st.columns(2)
            with col1:
                config['start_date'] = st.date_input("Start Date")
            with col2:
                config['end_date'] = st.date_input("End Date")
        else:
            config['start_date'] = None
            config['end_date'] = None

        # Capital and risk settings
        st.markdown("---")
        st.markdown("**💰 Capital & Risk Management**")

        col1, col2 = st.columns(2)

        with col1:
            config['initial_capital'] = st.number_input(
                "Initial Capital ($)",
                min_value=1000.0,
                max_value=10000000.0,
                value=10000.0,
                step=1000.0,
                help="Starting account balance"
            )

        with col2:
            config['max_total_risk'] = st.number_input(
                "Max Total Risk (%)",
                min_value=1.0,
                max_value=50.0,
                value=6.0,
                step=0.5,
                help="Maximum % of capital at risk across all open positions"
            )

        # Strategy configuration
        st.markdown("---")
        from .strategy_selector import show_strategy_selector
        config = show_strategy_selector(config)

        # Check if strategy was selected
        if not config.get('strategy_metadata'):
            st.info("Please select a strategy to continue")
            return None

        metadata = config['strategy_metadata']

        # Time and Day Filters
        st.markdown("---")
        st.markdown("**⏰ Trading Time Filters**")

        use_time_filters = st.checkbox(
            "Enable time/day filters",
            value=False,
            help="Restrict trading to specific days of the week and/or times of day"
        )

        if use_time_filters:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Days of Week**")
                allowed_days = []
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

                for day in day_names:
                    if st.checkbox(day, value=True, key=f"day_{day}"):
                        allowed_days.append(day)

                config['allowed_days'] = allowed_days if allowed_days else None

            with col2:
                st.markdown("**Time of Day (UTC)**")
                use_time_range = st.checkbox("Enable time range", value=False, key="use_time_range")

                if use_time_range:
                    time_col1, time_col2 = st.columns(2)
                    with time_col1:
                        start_hour = st.number_input("Start Hour", min_value=0, max_value=23, value=10, key="start_hour")
                        start_minute = st.number_input("Start Minute", min_value=0, max_value=59, value=0, key="start_min")
                    with time_col2:
                        end_hour = st.number_input("End Hour", min_value=0, max_value=23, value=18, key="end_hour")
                        end_minute = st.number_input("End Minute", min_value=0, max_value=59, value=0, key="end_min")

                    config['allowed_time_range'] = f"{start_hour:02d}:{start_minute:02d}-{end_hour:02d}:{end_minute:02d}"
                else:
                    config['allowed_time_range'] = None
        else:
            config['allowed_days'] = None
            config['allowed_time_range'] = None

        # Position management
        st.markdown("---")
        st.markdown("**📊 Position Management**")

        col1, col2 = st.columns([2, 1])
        with col1:
            config['risk_per_trade'] = st.number_input(
                "Risk Per Trade (%)",
                min_value=0.1,
                max_value=10.0,
                value=1.0,
                step=0.1,
                help="% of account to risk per trade"
            )
        with col2:
            config['use_compounding'] = st.checkbox(
                "Compounding",
                value=False,
                help="If ON: risk % of current capital (grows/shrinks). If OFF: risk % of initial capital (fixed)"
            )

        # Stop Loss Configuration
        # Only show if strategy doesn't control SL
        if not metadata.uses_custom_sl:
            st.markdown("**🛑 Stop Loss**")
            config['sl_type'] = st.selectbox(
                "SL Type",
                ["percent", "time", "condition"],
                help="Stop loss type"
            )
        else:
            st.markdown("**🛑 Stop Loss**")
            st.info(f"ℹ️ Stop loss is controlled by the strategy ({metadata.default_sl_type})")
            config['sl_type'] = metadata.default_sl_type

        # SL parameters (only if not strategy-controlled)
        if not metadata.uses_custom_sl:
            if config['sl_type'] == 'percent':
                config['sl_percent'] = st.number_input(
                    "SL %",
                    min_value=0.1,
                    max_value=20.0,
                    value=2.0,
                    step=0.1,
                    help="Stop loss distance as % from entry"
                )
            elif config['sl_type'] == 'time':
                config['sl_time_bars'] = st.number_input(
                    "Exit after N bars",
                    min_value=1,
                    max_value=1000,
                    value=50,
                    step=1,
                    help="Exit position after this many bars"
                )

        # Take Profit Configuration
        # Only show if strategy doesn't control TP
        if not metadata.uses_custom_tp:
            st.markdown("**🎯 Take Profit**")
            config['tp_type'] = st.selectbox(
                "TP Type",
                ["rr", "percent", "condition"],
                help="Take profit type"
            )
        else:
            st.markdown("**🎯 Take Profit**")
            st.info(f"ℹ️ Take profit is controlled by the strategy ({metadata.default_tp_type})")
            config['tp_type'] = metadata.default_tp_type

        # TP parameters (only if not strategy-controlled)
        if not metadata.uses_custom_tp:
            if config['tp_type'] == 'rr':
                config['tp_rr_ratio'] = st.number_input(
                    "Risk:Reward Ratio",
                    min_value=0.5,
                    max_value=10.0,
                    value=2.0,
                    step=0.5,
                    help="Risk:Reward ratio (e.g., 2.0 = 1:2)"
                )
            elif config['tp_type'] == 'percent':
                config['tp_percent'] = st.number_input(
                    "TP %",
                    min_value=0.1,
                    max_value=50.0,
                    value=4.0,
                    step=0.1,
                    help="Take profit distance as % from entry"
                )

            # Partial exits (only if not strategy-controlled)
            st.markdown("**📉 Partial Exits (Optional)**")
            use_partial_exits = st.checkbox("Enable partial position exits", value=False)

            if use_partial_exits:
                config['partial_exits'] = []
                num_exits = st.number_input("Number of partial exits", min_value=1, max_value=5, value=1)

                for i in range(int(num_exits)):
                    col1, col2 = st.columns(2)
                    with col1:
                        size = st.number_input(
                            f"Exit {i+1}: Size Fraction",
                            min_value=0.1,
                            max_value=1.0,
                            value=0.5,
                            step=0.1,
                            key=f"partial_size_{i}"
                        )
                    with col2:
                        rr = st.number_input(
                            f"Exit {i+1}: At R-Multiple",
                            min_value=0.5,
                            max_value=10.0,
                            value=2.0,
                            step=0.5,
                            key=f"partial_rr_{i}"
                        )
                    config['partial_exits'].append((size, rr))
            else:
                config['partial_exits'] = []
        else:
            config['partial_exits'] = []  # Strategy controls partial exits

        return config