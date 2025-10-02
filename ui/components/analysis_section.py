"""
Analysis section components for backtesting and strategy analysis.
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import symbols_config
from src.database import create_db_connection
from src.data_fetcher import fetch_market_data
from src.backtesting import BacktestEngine
from src.backtesting.example_strategies import SimpleMAStrategy, HTSTrendFollowStrategy
from src.backtesting.position import PositionConfig
from .backtest_config import BacktestConfig
from .backtest_results import BacktestResults


def show_analysis_section():
    """
    Main analysis section with backtesting functionality.
    """
    st.header("🔍 Backtesting & Analysis")

    st.markdown("""
    Run backtests on your trading strategies with multi-timeframe support,
    advanced position management, and comprehensive performance analytics.
    """)

    # Check if we have symbols
    used_symbols = symbols_config.get_active_symbols()
    if not used_symbols:
        st.warning("⚠️ No symbols selected. Go to Symbol Management to select symbols for analysis.")
        return

    # Configuration section
    with st.expander("⚙️ Configure Backtest", expanded=True):
        config = BacktestConfig.show_config_ui()

    # Run backtest button
    if config:
        st.markdown("---")

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            run_button = st.button("🚀 Run Backtest", type="primary", width="stretch")
        with col2:
            if st.button("📋 Save Config", width="stretch"):
                st.session_state.saved_backtest_config = config
                st.success("Configuration saved!")
        with col3:
            if st.button("🔄 Reset", width="stretch"):
                if 'backtest_results' in st.session_state:
                    del st.session_state.backtest_results
                st.rerun()

        if run_button:
            _run_backtest(config)

    # Display results if available
    if 'backtest_results' in st.session_state:
        st.markdown("---")
        BacktestResults.show_results(
            st.session_state.backtest_results,
            st.session_state.backtest_symbol
        )


def _run_backtest(config: dict):
    """
    Execute the backtest with given configuration.
    """
    try:
        with st.spinner("Loading data and running backtest..."):

            # Load data for all timeframes (reuse cached data if available)
            data_dict = {}
            engine_db = None

            for timeframe in config['timeframes']:
                # Get table name from metadata
                symbol_info = st.session_state.metadata_df[
                    (st.session_state.metadata_df['symbol'] == config['symbol']) &
                    (st.session_state.metadata_df['timeframe'] == timeframe)
                ]

                if symbol_info.empty:
                    st.error(f"No data found for {config['symbol']} at {timeframe}")
                    return

                table_name = symbol_info.iloc[0]['table_name']

                # Check if data is already loaded in session state
                if table_name in st.session_state.market_data:
                    df = st.session_state.market_data[table_name]
                else:
                    # Load fresh data if not cached
                    if engine_db is None:
                        engine_db = create_db_connection()
                    df = fetch_market_data(engine_db, table_name, config['symbol'])
                    # Cache it for future use
                    st.session_state.market_data[table_name] = df

                data_dict[timeframe] = df

            # Create strategy based on config
            if config['strategy_type'] == "Simple MA Crossover":
                strategy_config = {
                    **config['strategy_params'],
                    'timeframes': config['timeframes'],  # Pass selected timeframes to strategy
                    'risk_percent': config['risk_per_trade'],
                    'sl_type': config['sl_type'],
                    'sl_percent': config.get('sl_percent'),
                    'sl_time_bars': config.get('sl_time_bars'),
                    'tp_type': config['tp_type'],
                    'tp_percent': config.get('tp_percent'),
                    'tp_rr_ratio': config.get('tp_rr_ratio'),
                    'partial_exits': config.get('partial_exits', [])
                }
                strategy = SimpleMAStrategy(config=strategy_config)
            elif config['strategy_type'] == "HTS Trend Follow (Multi-TF)":
                # HTS strategy requires specific timeframes
                if '5m' not in config['timeframes'] or '1h' not in config['timeframes']:
                    st.error("❌ HTS Trend Follow strategy requires both 5m and 1h timeframes to be selected!")
                    return

                strategy_config = {
                    **config['strategy_params'],
                    'timeframes': ['5m', '1h'],  # Fixed timeframes for HTS strategy
                    'risk_percent': config['risk_per_trade'],
                    'partial_exits': config.get('partial_exits', [
                        (0.5, 1.5),  # Default: 50% at 1.5R
                        (0.5, 4.0)   # Default: 50% at 4R
                    ])
                }
                strategy = HTSTrendFollowStrategy(config=strategy_config)
            else:
                st.error("Custom strategies need to be implemented in code")
                return

            # Create and run backtest engine
            backtest = BacktestEngine(
                initial_capital=config['initial_capital'],
                max_total_risk_percent=config['max_total_risk']
            )

            # Convert dates if provided
            start_date = None
            end_date = None
            if config.get('start_date'):
                start_date = datetime.combine(config['start_date'], datetime.min.time())
            if config.get('end_date'):
                end_date = datetime.combine(config['end_date'], datetime.max.time())

            # Run backtest
            results = backtest.run(
                strategies=[strategy],
                data_dict=data_dict,
                start_date=start_date,
                end_date=end_date
            )

            # Store results in session state
            st.session_state.backtest_results = results
            st.session_state.backtest_symbol = config['symbol']

            st.success("✅ Backtest completed successfully!")
            st.rerun()

    except Exception as e:
        st.error(f"❌ Error running backtest: {str(e)}")
        import traceback
        with st.expander("Error details"):
            st.code(traceback.format_exc())