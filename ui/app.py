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

# Import UI component modules
from components.data_loader import initialize_session_state, load_data
from components.symbol_management import show_symbol_management
from components.data_preview import show_data_preview
from components.analysis_section import show_analysis_section

def main():
    """Main UI application orchestration"""

    # Configure Streamlit page settings
    st.set_page_config(
        page_title="Cross-Market Backtest",
        page_icon="📈",
        layout="wide"
    )

    # Initialize session state variables for data management
    initialize_session_state()

    # Display main header
    st.title("📈 Cross-Market Backtest Analysis")
    st.markdown("---")

    # Create sidebar navigation and data loading controls
    st.sidebar.title("🔧 Controls")
    st.sidebar.header("📡 Data Connection")

    # Data loading button with status indicator
    if st.sidebar.button("🔄 Load/Refresh Data", type="primary"):
        load_data()

    # Show connection status and handle data loading state
    if st.session_state.data_loaded:
        st.sidebar.success("✅ Data Connected")
    else:
        st.sidebar.warning("⚠️ No data loaded")
        st.info("👈 Click 'Load/Refresh Data' in the sidebar to connect to your database and load symbols.")
        return

    # Create main content tabs for different functionality areas
    tab1, tab2, tab3 = st.tabs(["🎯 Symbol Management", "📊 Data Preview", "🔍 Analysis"])

    # Symbol management interface for configuring which symbols to analyze
    with tab1:
        show_symbol_management()

    # Data preview interface for examining market data
    with tab2:
        show_data_preview()

    # Analysis section for future analytical features
    with tab3:
        show_analysis_section()

if __name__ == "__main__":
    main()