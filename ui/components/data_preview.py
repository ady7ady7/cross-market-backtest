"""
Data preview components for market data visualization.
"""

import streamlit as st
import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database import create_db_connection
from src.data_fetcher import fetch_market_data
import symbols_config
from .chart_utils import create_interactive_candlestick_chart


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

                # Interactive price chart
                st.subheader("📈 Interactive Price Chart")

                # Chart controls
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.caption("🖱️ **Mouse Controls**: Wheel to zoom • Click & drag to pan • Double-click to reset")
                with col2:
                    data_points = st.selectbox(
                        "Data points:",
                        [500, 1000, 2000, 5000, "All"],
                        index=1,
                        help="Select number of recent data points to display"
                    )

                # Prepare chart data based on selection
                if data_points == "All":
                    chart_data = df
                else:
                    chart_data = df.tail(data_points)

                # Create and display interactive chart
                fig, config = create_interactive_candlestick_chart(chart_data, selected_symbol)
                st.plotly_chart(fig, use_container_width=True, config=config)

            except Exception as e:
                st.error(f"❌ Error loading data for {selected_symbol}: {str(e)}")