"""
Analysis section components for future analysis features.
"""

import streamlit as st
import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import symbols_config


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