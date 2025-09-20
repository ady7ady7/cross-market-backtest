#!/usr/bin/env python3
"""
UI Launcher Script for Cross-Market Backtest Application

This script launches the Streamlit UI application for managing symbols
and running market data analysis.

Usage:
    python run_ui.py

The UI will be available at http://localhost:8501

Features available in the UI:
- Symbol management (move between used/ignored lists)
- Data connection and preview
- Basic market data visualization
- Foundation for future analysis features
"""

import os
import sys
import subprocess

def main():
    """Launch the Streamlit UI application"""

    print("🚀 Starting Cross-Market Backtest UI...")
    print("📡 The UI will be available at: http://localhost:8501")
    print("🔧 Make sure your .env file is configured with DATABASE_URL and DATABASE_CA_CERT_PATH")
    print("💡 Press Ctrl+C to stop the server")
    print("-" * 60)

    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    ui_app_path = os.path.join(script_dir, "ui", "app.py")

    try:
        # Launch Streamlit with configuration to skip email setup
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", ui_app_path,
            "--server.headless", "false",
            "--server.port", "8501",
            "--server.address", "localhost",
            "--browser.gatherUsageStats", "false"
        ])
    except KeyboardInterrupt:
        print("\n🛑 Shutting down UI server...")
    except Exception as e:
        print(f"❌ Error starting UI: {str(e)}")
        print("💡 Make sure Streamlit is installed: pip install streamlit")

if __name__ == "__main__":
    main()