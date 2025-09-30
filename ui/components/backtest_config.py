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
        st.markdown("**🎯 Strategy Configuration**")

        config['strategy_type'] = st.selectbox(
            "Strategy Type",
            ["Simple MA Crossover", "Custom"],
            help="Select a pre-built strategy or configure custom"
        )

        if config['strategy_type'] == "Simple MA Crossover":
            config['strategy_params'] = BacktestConfig._ma_strategy_config()
        else:
            st.info("Custom strategy configuration - implement your strategy in code")
            config['strategy_params'] = {}

        # Position management
        st.markdown("---")
        st.markdown("**📊 Position Management**")

        config['risk_per_trade'] = st.number_input(
            "Risk Per Trade (%)",
            min_value=0.1,
            max_value=10.0,
            value=1.0,
            step=0.1,
            help="% of account to risk per trade"
        )

        # Stop Loss Configuration
        st.markdown("**🛑 Stop Loss**")
        config['sl_type'] = st.selectbox(
            "SL Type",
            ["percent", "time", "condition"],
            help="Stop loss type"
        )

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
        st.markdown("**🎯 Take Profit**")
        config['tp_type'] = st.selectbox(
            "TP Type",
            ["rr", "percent", "condition"],
            help="Take profit type"
        )

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

        # Partial exits
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

        return config

    @staticmethod
    def _ma_strategy_config() -> Dict[str, Any]:
        """Configuration for MA crossover strategy"""
        st.markdown("**Moving Average Settings**")

        col1, col2 = st.columns(2)

        with col1:
            fast_period = st.number_input(
                "Fast MA Period",
                min_value=5,
                max_value=200,
                value=20,
                step=5,
                help="Period for fast moving average"
            )

        with col2:
            slow_period = st.number_input(
                "Slow MA Period",
                min_value=10,
                max_value=500,
                value=50,
                step=10,
                help="Period for slow moving average"
            )

        return {
            'fast_period': fast_period,
            'slow_period': slow_period
        }