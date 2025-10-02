"""
Data loading and session state management for the UI application.
"""

import streamlit as st
import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.database import create_db_connection
from src.data_fetcher import read_symbol_metadata


def initialize_session_state():
    """Initialize session state variables"""
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
            unique_symbols = metadata_df['symbol'].nunique()
            st.metric("Total Symbols", unique_symbols)
        with col2:
            tradfi_count = metadata_df[metadata_df['asset_type'] == 'tradfi']['symbol'].nunique()
            st.metric("TradFi Assets", tradfi_count)
        with col3:
            crypto_count = metadata_df[metadata_df['asset_type'] == 'crypto']['symbol'].nunique()
            st.metric("Crypto Assets", crypto_count)

    except Exception as e:
        st.error(f"❌ Error loading data: {str(e)}")
        st.session_state.data_loaded = False