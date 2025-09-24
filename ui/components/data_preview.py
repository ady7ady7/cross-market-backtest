"""
Data preview components for market data visualization.
"""

import streamlit as st
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database import create_db_connection
from src.data_fetcher import fetch_market_data
import symbols_config


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