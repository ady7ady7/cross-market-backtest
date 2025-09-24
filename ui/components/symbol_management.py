"""
Symbol management interface components.
"""

import streamlit as st
import sys
import os

# Add parent directory to path to import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import symbols_config


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