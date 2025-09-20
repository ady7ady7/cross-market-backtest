"""
Cross-Market Backtest UI Application

This is the main UI application for managing symbols and running backtests.
Built with Streamlit for an interactive web interface.

Features:
- Symbol management (move between used/ignored lists)
- Data fetching and preview
- Integration with existing database and configuration system
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import create_db_connection
from src.data_fetcher import read_symbol_metadata, fetch_market_data
import symbols_config

# Configure Streamlit page
st.set_page_config(
    page_title="Cross-Market Backtest",
    page_icon="📈",
    layout="wide"
)

# Session state initialization
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False
if 'market_data' not in st.session_state:
    st.session_state.market_data = {}
if 'metadata_df' not in st.session_state:
    st.session_state.metadata_df = None

def load_data():
    """Load market data using existing data fetching functions"""
    try:
        with st.spinner("Connecting to database..."):
            engine = create_db_connection()

        with st.spinner("Reading symbol metadata..."):
            metadata_df = read_symbol_metadata(engine)
            st.session_state.metadata_df = metadata_df

        st.success("✅ Data loaded successfully!")
        st.session_state.data_loaded = True

        # Show metadata summary
        st.subheader("📊 Available Symbols Overview")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Symbols", len(metadata_df))
        with col2:
            tradfi_count = len(metadata_df[metadata_df['asset_type'] == 'tradfi'])
            st.metric("TradFi Assets", tradfi_count)
        with col3:
            crypto_count = len(metadata_df[metadata_df['asset_type'] == 'crypto'])
            st.metric("Crypto Assets", crypto_count)

    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.session_state.data_loaded = False

def main():
    """Main UI application"""

    # Header
    st.title("📈 Cross-Market Backtest Analysis")
    st.markdown("---")

    # Sidebar for navigation
    st.sidebar.title("🔧 Controls")

    # Data loading section
    st.sidebar.header("📡 Data Connection")
    if st.sidebar.button("🔄 Load/Refresh Data", type="primary"):
        load_data()

    if st.session_state.data_loaded:
        st.sidebar.success("✅ Data Connected")
    else:
        st.sidebar.warning("⚠️ No data loaded")
        st.info("👈 Click 'Load/Refresh Data' in the sidebar to connect to your database and load symbols.")
        return

    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["🎯 Symbol Management", "📊 Data Preview", "🔍 Analysis"])

    with tab1:
        show_symbol_management()

    with tab2:
        show_data_preview()

    with tab3:
        show_analysis_section()

def show_symbol_management():
    """Display symbol management interface"""

    st.header("🎯 Symbol Configuration")
    st.markdown("Manage which symbols to include in your analysis.")

    # Get current symbol lists
    used_symbols = symbols_config.get_active_symbols()
    ignored_symbols = symbols_config.get_ignored_symbols()

    # Two columns for used and ignored symbols
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("✅ Used Symbols")
        st.caption(f"Symbols included in analysis ({len(used_symbols)} total)")

        if used_symbols:
            for symbol in used_symbols:
                col_symbol, col_btn = st.columns([3, 1])
                with col_symbol:
                    st.text(f"📈 {symbol}")
                with col_btn:
                    if st.button("➡️", key=f"move_to_ignored_{symbol}", help=f"Move {symbol} to ignored"):
                        symbols_config.move_to_ignored(symbol)
                        st.rerun()
        else:
            st.info("No symbols selected for analysis. Move symbols from the ignored list.")

    with col2:
        st.subheader("❌ Ignored Symbols")
        st.caption(f"Symbols not included in analysis ({len(ignored_symbols)} total)")

        if ignored_symbols:
            for symbol in ignored_symbols:
                col_symbol, col_btn = st.columns([3, 1])
                with col_symbol:
                    st.text(f"📊 {symbol}")
                with col_btn:
                    if st.button("⬅️", key=f"move_to_used_{symbol}", help=f"Move {symbol} to used"):
                        symbols_config.move_to_used(symbol)
                        st.rerun()
        else:
            st.info("All symbols are being used in analysis.")

    # Bulk operations
    st.markdown("---")
    st.subheader("🔄 Bulk Operations")

    bulk_col1, bulk_col2, bulk_col3 = st.columns(3)

    with bulk_col1:
        if st.button("📈 Use All Symbols", help="Move all symbols to used list"):
            for symbol in ignored_symbols.copy():
                symbols_config.move_to_used(symbol)
            st.rerun()

    with bulk_col2:
        if st.button("❌ Ignore All Symbols", help="Move all symbols to ignored list"):
            for symbol in used_symbols.copy():
                symbols_config.move_to_ignored(symbol)
            st.rerun()

    with bulk_col3:
        if st.button("🔄 Reset Config", help="Reset to default configuration"):
            # This would require modifying symbols_config to have a reset function
            st.info("Reset functionality can be added if needed")

def show_data_preview():
    """Display data preview for selected symbols"""

    st.header("📊 Data Preview")

    used_symbols = symbols_config.get_active_symbols()

    if not used_symbols:
        st.warning("⚠️ No symbols selected. Go to Symbol Management to select symbols for analysis.")
        return

    # Symbol selector
    selected_symbol = st.selectbox(
        "Select symbol to preview:",
        used_symbols,
        help="Choose a symbol to preview its market data"
    )

    if selected_symbol and st.session_state.metadata_df is not None:
        # Get table information for selected symbol
        symbol_info = st.session_state.metadata_df[
            st.session_state.metadata_df['symbol'] == selected_symbol
        ].iloc[0]

        table_name = symbol_info['table_name']

        # Load and display data
        if st.button(f"📈 Load Data for {selected_symbol}", type="primary"):
            try:
                with st.spinner(f"Loading {selected_symbol} data..."):
                    engine = create_db_connection()
                    df = fetch_market_data(engine, table_name, selected_symbol)
                    st.session_state.market_data[table_name] = df

                # Display data info
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Total Records", len(df))
                with col2:
                    st.metric("Date Range", f"{(df['timestamp'].max() - df['timestamp'].min()).days} days")
                with col3:
                    st.metric("Asset Type", symbol_info['asset_type'].upper())
                with col4:
                    if 'volume' in df.columns:
                        avg_volume = df['volume'].mean()
                        st.metric("Avg Volume", f"{avg_volume:.2f}")

                # Data preview
                st.subheader("📋 Data Sample")
                st.dataframe(df.head(20), use_container_width=True)

                # Simple price chart
                st.subheader("📈 Price Chart (Last 1000 records)")
                chart_data = df.tail(1000)

                fig = go.Figure()
                fig.add_trace(go.Candlestick(
                    x=chart_data['timestamp'],
                    open=chart_data['open'],
                    high=chart_data['high'],
                    low=chart_data['low'],
                    close=chart_data['close'],
                    name=selected_symbol
                ))

                fig.update_layout(
                    title=f"{selected_symbol} Price Chart",
                    xaxis_title="Time",
                    yaxis_title="Price",
                    height=500
                )

                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"❌ Error loading data for {selected_symbol}: {str(e)}")

def show_analysis_section():
    """Placeholder for future analysis features"""

    st.header("🔍 Analysis")
    st.info("🚧 Analysis features will be implemented in future iterations.")

    used_symbols = symbols_config.get_active_symbols()

    if used_symbols:
        st.write("**Symbols ready for analysis:**")
        for symbol in used_symbols:
            st.write(f"• {symbol}")
    else:
        st.warning("No symbols selected for analysis.")

if __name__ == "__main__":
    main()