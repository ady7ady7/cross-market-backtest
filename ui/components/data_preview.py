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
from .indicator_config import IndicatorConfigManager


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

        # Initialize session state for current symbol data
        current_data_key = f"current_data_{selected_symbol}"

        # Load data button
        if st.button(f"📈 Load Data for {selected_symbol}", type="primary"):
            try:
                with st.spinner(f"Loading {selected_symbol} data..."):
                    engine = create_db_connection()
                    df = fetch_market_data(engine, table_name, selected_symbol)
                    st.session_state.market_data[table_name] = df
                    st.session_state[current_data_key] = df

            except Exception as e:
                st.error(f"❌ Error loading data for {selected_symbol}: {str(e)}")
                return

        # Check if we have data for the current symbol
        if current_data_key in st.session_state or table_name in st.session_state.market_data:
            # Get the data from session state
            if current_data_key in st.session_state:
                df = st.session_state[current_data_key]
            else:
                df = st.session_state.market_data[table_name]

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
            st.dataframe(df.head(20), width='stretch')

            # Chart controls
            col1, col2 = st.columns([3, 1])
            with col1:
                st.caption("🖱️ **Mouse Controls**: Wheel to zoom • Click & drag to pan • Double-click to reset")
            with col2:
                data_points = st.selectbox(
                    "Data points:",
                    [500, 1000, 2000, 5000, 10000, 20000, "Range Slider"],
                    index=6,  # Default to "Range Slider" (index 6)
                    help="Select number of recent data points to display or use Range Slider for large datasets",
                    key=f"data_points_{selected_symbol}"
                )

            # Indicators section - placed right before the chart
            st.subheader("🔧 Technical Indicators")
            indicator_manager = IndicatorConfigManager()
            available_indicators = indicator_manager.get_available_indicators()

            if available_indicators:
                active_indicators = []

                for indicator_name in available_indicators:
                    # Create container with border for each indicator
                    with st.container(border=True):
                        # Create columns for toggle, gear icon (next to each other), and indicator name
                        col1, col2, col3 = st.columns([1, 1, 8])

                        with col1:
                            # Toggle switch for enabling/disabling indicator
                            enabled_key = f"indicator_enabled_{selected_symbol}_{indicator_name.replace(' ', '_')}"
                            is_enabled = st.toggle(
                                "",
                                key=enabled_key,
                                help=f"Enable/disable {indicator_name}"
                            )

                            # Reset settings panel state when indicator is toggled off
                            if not is_enabled:
                                session_key = f"settings_visible_{selected_symbol}_{indicator_name.replace(' ', '_')}"
                                if session_key in st.session_state:
                                    st.session_state[session_key] = False

                        with col2:
                            # Settings gear icon (always visible)
                            settings_key = f"show_settings_{selected_symbol}_{indicator_name.replace(' ', '_')}"
                            show_settings = st.button(
                                "⚙️",
                                key=settings_key,
                                help=f"Configure {indicator_name} settings"
                            )

                            # Store settings visibility state
                            if show_settings:
                                session_key = f"settings_visible_{selected_symbol}_{indicator_name.replace(' ', '_')}"
                                st.session_state[session_key] = not st.session_state.get(session_key, False)

                        with col3:
                            # Indicator name
                            st.write(f"**{indicator_name}**")

                        # Show settings panel if expanded
                        session_key = f"settings_visible_{selected_symbol}_{indicator_name.replace(' ', '_')}"
                        if st.session_state.get(session_key, False):
                            with st.container():
                                st.markdown("---")
                                config = indicator_manager.create_indicator_config_ui(
                                    indicator_name,
                                    f"{selected_symbol}_{indicator_name.replace(' ', '_')}"
                                )
                                st.markdown("---")
                        else:
                            config = indicator_manager.get_default_config(indicator_name)

                        # Create indicator instance if enabled
                        if is_enabled:
                            try:
                                indicator = indicator_manager.create_indicator(indicator_name, config)
                                active_indicators.append(indicator)
                            except Exception as e:
                                st.error(f"Error creating {indicator_name}: {str(e)}")

                # Store indicators in session state for reuse
                indicators_key = f"active_indicators_{selected_symbol}"
                st.session_state[indicators_key] = active_indicators
            else:
                st.info("No indicators available.")
                st.session_state[f"active_indicators_{selected_symbol}"] = []

            # Interactive price chart
            st.subheader("📈 Interactive Price Chart")

            # Prepare chart data based on selection
            if data_points == "Range Slider":
                # Initialize session state for range slider
                slider_key = f"range_slider_{selected_symbol}"
                if slider_key not in st.session_state:
                    st.session_state[slider_key] = 0

                total_records = len(df)
                max_display_points = 15000  # Sweet spot for performance

                # Calculate total number of ranges
                total_ranges = max(1, (total_records - max_display_points) // 1000 + 1)

                # Range slider and controls
                st.markdown("---")
                st.subheader("📊 Data Range Navigation")

                # Display current range info
                current_start = st.session_state[slider_key] * 1000
                current_end = min(current_start + max_display_points, total_records)

                col_info1, col_info2, col_info3 = st.columns(3)
                with col_info1:
                    start_date = df.iloc[current_start]['timestamp'].strftime('%Y-%m-%d %H:%M')
                    st.metric("Range Start", start_date)
                with col_info2:
                    end_date = df.iloc[current_end-1]['timestamp'].strftime('%Y-%m-%d %H:%M')
                    st.metric("Range End", end_date)
                with col_info3:
                    st.metric("Points Shown", f"{current_end - current_start:,}")

                # Navigation controls
                col_nav1, col_nav2, col_nav3, col_nav4, col_nav5 = st.columns(5)

                with col_nav1:
                    if st.button("⏮️ First", help="Go to first range"):
                        st.session_state[slider_key] = 0
                        st.rerun()

                with col_nav2:
                    if st.button("⬅️ Previous", help="Go to previous range"):
                        if st.session_state[slider_key] > 0:
                            st.session_state[slider_key] -= 1
                            st.rerun()

                with col_nav3:
                    # Range slider
                    range_position = st.slider(
                        "Navigate through data:",
                        min_value=0,
                        max_value=max(0, total_ranges - 1),
                        value=st.session_state[slider_key],
                        help=f"Slide to navigate through {total_records:,} total records",
                        key=f"slider_control_{selected_symbol}"
                    )

                    if range_position != st.session_state[slider_key]:
                        st.session_state[slider_key] = range_position
                        st.rerun()

                with col_nav4:
                    if st.button("➡️ Next", help="Go to next range"):
                        if st.session_state[slider_key] < total_ranges - 1:
                            st.session_state[slider_key] += 1
                            st.rerun()

                with col_nav5:
                    if st.button("⏭️ Last", help="Go to last range"):
                        st.session_state[slider_key] = max(0, total_ranges - 1)
                        st.rerun()

                # Progress indicator
                progress = (st.session_state[slider_key] + 1) / total_ranges if total_ranges > 0 else 0
                st.progress(progress)
                st.caption(f"Range {st.session_state[slider_key] + 1} of {total_ranges} • Progress: {progress:.1%}")

                # Get chart data for current range
                chart_data = df.iloc[current_start:current_end].copy()

            elif data_points == "All":
                if len(df) > 50000:
                    st.warning(f"⚠️ Dataset has {len(df):,} records. Consider using 'Range Slider' for better performance.")
                    st.info("💡 Large datasets may cause performance issues. The Range Slider option shows 15,000 points at a time with smooth navigation.")
                chart_data = df
            else:
                chart_data = df.tail(data_points)

            # Calculate indicators for chart data
            calculated_indicators = []
            indicators_key = f"active_indicators_{selected_symbol}"

            if indicators_key in st.session_state and st.session_state[indicators_key]:
                for indicator in st.session_state[indicators_key]:
                    try:
                        # Calculate indicator for the chart data
                        indicator.calculate(chart_data)
                        calculated_indicators.append(indicator)
                    except Exception as e:
                        st.warning(f"Could not calculate {indicator.name}: {str(e)}")

            # Create and display interactive chart with indicators
            # Using a placeholder for smooth updates
            chart_placeholder = st.empty()

            with chart_placeholder.container():
                fig, config = create_interactive_candlestick_chart(
                    chart_data,
                    selected_symbol,
                    indicators=calculated_indicators
                )
                st.plotly_chart(fig, width='stretch', config=config, key=f"chart_{selected_symbol}_{hash(str(calculated_indicators))}")

            # Display indicator information if any are active
            if calculated_indicators:
                st.subheader("📊 Active Indicators")
                for indicator in calculated_indicators:
                    if hasattr(indicator, 'data') and indicator.data is not None and not indicator.data.empty:
                        with st.expander(f"{indicator.name} - Data Sample", expanded=False):
                            st.dataframe(indicator.data.head(10), width='stretch')