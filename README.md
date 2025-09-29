# Cross-Market Backtest Application

A Python application for cross-market backtesting with market data from multiple exchanges and asset types (TradFi and Crypto). Features an intuitive web interface with advanced charting and technical indicator overlays.

## Features

- 🗄️ **Database Integration**: Connects to PostgreSQL with SSL certificate authentication
- 📊 **Multi-Asset Support**: Handles both traditional finance and cryptocurrency data
- 🎯 **Symbol Management**: Easy configuration of which symbols to include/exclude from analysis
- 🖥️ **Interactive Web UI**: Modern Streamlit interface with tabbed navigation
- 📈 **Advanced Charting**: Interactive candlestick charts with zoom, pan, and range navigation
- 🔧 **Technical Indicators**: Configurable indicators with real-time overlays (Pivot Points, etc.)
- 🎨 **Customizable Settings**: Color themes, time ranges, and display options for indicators
- 📊 **Data Range Navigation**: Efficient handling of large datasets with slider controls
- 🏗️ **Modular Architecture**: Clean, extensible code structure with component-based UI

## Project Structure

```
cross-market-backtest/
├── src/                      # Core application modules
│   ├── database.py           # Database connection and SSL handling
│   ├── data_fetcher.py       # Market data fetching functions
│   └── indicators/           # Technical indicator implementations
│       ├── __init__.py       # Indicator exports
│       ├── base.py           # Base indicator interface
│       └── pivot_points.py   # Pivot Points indicator
├── ui/                       # Streamlit web interface
│   ├── app.py               # Main UI application with tabs
│   └── components/          # Modular UI components
│       ├── analysis_section.py     # Analysis tab functionality
│       ├── chart_utils.py          # Interactive chart utilities
│       ├── data_loader.py          # Data loading components
│       ├── data_preview.py         # Data preview with charts/indicators
│       ├── indicator_config.py     # Indicator configuration UI
│       ├── indicator_defaults.py   # Default indicator settings
│       └── symbol_management.py    # Symbol management interface
├── certs/                   # SSL certificates
│   └── ca-certificate.crt
├── config.py               # Environment configuration
├── symbols_config.py       # Symbol management configuration
├── main.py                # CLI data fetching script
├── run_ui.py              # UI launcher script
├── requirements.txt       # Python dependencies
└── .env                   # Environment variables (create this)
```

## Setup Instructions

### 1. Environment Setup

Create a virtual environment and install dependencies:

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/Scripts/activate  # Windows Git Bash
# or
source venv/bin/activate      # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Configuration

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://username:password@host:port/database
DATABASE_CA_CERT_PATH=certs/ca-certificate.crt
```

Place your SSL certificate file in the `certs/` directory as `ca-certificate.crt`.

### 3. Symbol Configuration

Edit `symbols_config.py` to configure which symbols to analyze:

```python
# Move symbols from ignored to used list
from symbols_config import move_to_used
move_to_used("xauusd")
move_to_used("eurusd")
```

## Usage

### Command Line Interface

Run the CLI data fetching script:

```bash
python main.py
```

This will:
- Connect to the database
- Read symbol metadata
- Fetch market data for all symbols
- Display data previews (head/tail)

### Web UI Interface

Launch the interactive web interface:

```bash
python run_ui.py
```

The UI will be available at http://localhost:8501

#### UI Features:

1. **Symbol Management Tab**:
   - View used/ignored symbol lists
   - Move symbols between lists with buttons
   - Bulk operations (use all, ignore all)
   - Real-time symbol status updates

2. **Data Preview Tab**:
   - Symbol selection and data loading
   - Comprehensive data statistics and samples
   - **Interactive Charts**:
     - Zoom, pan, and double-click reset
     - Range slider navigation for large datasets (15k points optimized view)
     - Mouse controls with performance indicators
   - **Technical Indicators**:
     - Toggle-based indicator activation
     - Expandable settings with gear icon controls
     - Live indicator overlays on charts
     - Configurable colors, time ranges, and display levels
     - Currently supports: Pivot Points (with S1-S5, R1-R5 levels)

3. **Analysis Tab**:
   - Foundation for future backtesting and strategy features

## Available Symbols

The application currently supports these symbols:

**Traditional Finance (TradFi)**:
- `deuidxeur` - German DAX Index
- `nzdcad` - NZD/CAD Currency Pair
- `eurjpy` - EUR/JPY Currency Pair
- `usdcad` - USD/CAD Currency Pair
- `usa30idxusd` - US Dow Jones 30 Index
- `eurusd` - EUR/USD Currency Pair
- `lightcmdusd` - Light Crude Oil
- `xagusd` - Silver/USD
- `usa500idxusd` - S&P 500 Index
- `usatechidxusd` - NASDAQ Tech Index
- `xauusd` - Gold/USD

**Cryptocurrency**:
- `ETH/USDT` - Ethereum/Tether (Binance)

## Data Schema

Market data follows this structure:

```sql
timestamp TIMESTAMPTZ NOT NULL,
open DECIMAL(12, 8) NOT NULL,
high DECIMAL(12, 8) NOT NULL,
low DECIMAL(12, 8) NOT NULL,
close DECIMAL(12, 8) NOT NULL,
volume DECIMAL(20, 8) DEFAULT NULL,
day_of_week TEXT NOT NULL
```

Symbol metadata includes:
- Asset type (tradfi/crypto)
- Exchange information
- Data coverage statistics
- Update timestamps

## Development

### Adding New Features

1. **Database Functions**: Add to `src/database.py` or `src/data_fetcher.py`
2. **UI Components**: Create new modules in `ui/components/` following existing patterns
3. **Technical Indicators**:
   - Create new indicator class in `src/indicators/` extending `BaseIndicator`
   - Add default settings to `ui/components/indicator_defaults.py`
   - Register in `ui/components/indicator_config.py`
4. **Configuration**: Update `symbols_config.py` for symbol management
5. **Dependencies**: Add to `requirements.txt`

### Technical Indicator Development

To add a new technical indicator, follow these comprehensive steps:

#### Step 1: Create Indicator Class (`src/indicators/your_indicator.py`)
```python
"""
Your Indicator description.
Brief explanation of what this indicator does.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List
from .base import BaseIndicator


class YourIndicator(BaseIndicator):
    """
    Your Indicator class with detailed description.

    Explain parameters, calculations, and usage.
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__("Your Indicator", config)

        # Extract configuration parameters
        self.parameter1 = self.config.get('parameter1', default_value)
        self.parameter2 = self.config.get('parameter2', default_value)
        # ... other parameters

    def calculate(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate indicator values.

        Args:
            data: DataFrame with OHLC data

        Returns:
            DataFrame with calculated indicator values
        """
        if not self.validate_data(data):
            raise ValueError("Invalid data format for Your Indicator")

        self.data = data.copy()

        # Perform calculations
        # self.data['indicator_value'] = your_calculation_logic

        self.calculated = True
        return self.data

    def get_plot_data(self) -> Dict[str, Any]:
        """
        Get data formatted for plotting.

        Returns:
            Dictionary with plot configuration and data
        """
        if not self.calculated or self.data is None:
            return {'traces': [], 'layout_updates': {}}

        traces = []

        # Add your plot traces
        traces.append({
            'type': 'scatter',
            'x': self.data['timestamp'],
            'y': self.data['indicator_value'],
            'mode': 'lines',
            'name': 'Your Indicator Line',
            'line': {'color': '#00FF00', 'width': 2},
            'showlegend': True,
            'hovertemplate': 'Value: %{y:.4f}<br>%{x}<extra></extra>'
        })

        return {
            'traces': traces,
            'layout_updates': {}
        }
```

#### Step 2: Add to Indicators Package (`src/indicators/__init__.py`)
```python
from .base import BaseIndicator
from .pivot_points import PivotPoints
from .hts import HTS
from .your_indicator import YourIndicator  # Add your import

__all__ = ['BaseIndicator', 'PivotPoints', 'HTS', 'YourIndicator']  # Add to exports
```

#### Step 3: Add Default Settings (`ui/components/indicator_defaults.py`)

Add to the `get_indicator_defaults()` function:
```python
'Your Indicator': {
    'enabled': False,
    'parameter1': default_value1,
    'parameter2': default_value2,
    'colors': {
        'line1': '#00FF00',
        'line2': '#FF0000'
    },
    'show_options': {
        'option1': True,
        'option2': False
    }
}
```

Add to the `get_indicator_ui_config()` function:
```python
'Your Indicator': {
    'sections': [
        {
            'title': '⚙️ Basic Settings',
            'type': 'basic_group',
            'fields': [
                {
                    'key': 'parameter1',
                    'label': 'Parameter 1',
                    'type': 'number',
                    'default': default_value1,
                    'min': min_value,
                    'max': max_value,
                    'help': 'Description of parameter 1'
                }
            ]
        },
        {
            'title': '🎨 Display Settings',
            'type': 'display_group',
            'fields': [
                {
                    'key': 'colors.line1',
                    'label': 'Line 1 Color',
                    'type': 'color_picker',
                    'default': '#00FF00',
                    'help': 'Color for line 1'
                }
            ]
        }
    ]
}
```

#### Step 4: Register in Configuration Manager (`ui/components/indicator_config.py`)

**4a. Add Import:**
```python
from src.indicators import PivotPoints, HTS, YourIndicator  # Add your import
```

**4b. Register in Available Indicators:**
```python
def __init__(self):
    self.available_indicators = {
        'Pivot Points': PivotPoints,
        'HTS': HTS,
        'Your Indicator': YourIndicator  # Add your indicator
    }
```

**4c. Add Session State Extraction Method:**
```python
def get_current_config_from_session(self, indicator_name: str, key_prefix: str) -> Dict[str, Any]:
    # ... existing conditions
    elif indicator_name == 'Your Indicator':
        return self._extract_your_indicator_config_from_session(key_prefix)

    return self.get_default_config(indicator_name)

def _extract_your_indicator_config_from_session(self, key_prefix: str) -> Dict[str, Any]:
    """Extract Your Indicator configuration from session state."""
    import streamlit as st

    config = {}
    defaults = self.get_default_config('Your Indicator')

    # Extract all parameters from session state
    config['parameter1'] = st.session_state.get(f"{key_prefix}_parameter1", defaults['parameter1'])
    config['parameter2'] = st.session_state.get(f"{key_prefix}_parameter2", defaults['parameter2'])

    # Extract colors
    config['colors'] = {
        'line1': st.session_state.get(f"{key_prefix}_line1_color", defaults['colors']['line1'])
    }

    return config
```

**4d. Add UI Creation Method:**
```python
def create_indicator_config_ui(self, indicator_name: str, key_prefix: str = "") -> Dict[str, Any]:
    # ... existing conditions
    elif indicator_name == 'Your Indicator':
        return self._create_your_indicator_config(key_prefix)

def _create_your_indicator_config(self, key_prefix: str) -> Dict[str, Any]:
    """Create configuration UI for Your Indicator."""
    config = {}
    defaults = self.get_default_config('Your Indicator')

    st.subheader("⚙️ Your Indicator Configuration")

    # Create UI controls
    parameter1 = st.number_input(
        "Parameter 1",
        min_value=min_value,
        max_value=max_value,
        value=defaults['parameter1'],
        help="Description of parameter 1",
        key=f"{key_prefix}_parameter1"
    )

    line1_color = st.color_picker(
        "Line 1 Color",
        value=defaults['colors']['line1'],
        key=f"{key_prefix}_line1_color"
    )

    config = {
        'parameter1': parameter1,
        'colors': {
            'line1': line1_color
        }
    }

    return config
```

#### Complete Example: HTS Indicator

See `src/indicators/hts.py` and related configuration files for a complete working example of a dual EMA channel indicator with:
- Multiple configurable periods (EMA33, EMA144)
- Configurable data sources (high, low, close, open)
- Multiple colors and visibility toggles
- Complex plotting with solid/dotted line styles

#### File Checklist

When adding a new indicator, ensure you update these files:
- ✅ `src/indicators/your_indicator.py` - Main indicator class
- ✅ `src/indicators/__init__.py` - Add import and export
- ✅ `ui/components/indicator_defaults.py` - Add defaults and UI config
- ✅ `ui/components/indicator_config.py` - Add import, registration, session extraction, and UI creation methods

#### Testing Your Indicator

1. Start the application: `python run_ui.py`
2. Go to Data Preview tab
3. Load symbol data
4. Scroll to Technical Indicators Configuration
5. Toggle your indicator ON - should show with defaults
6. Click gear icon to configure settings
7. Verify Save & Apply workflow works correctly

### Code Style

- Keep functions simple and focused
- Add docstrings to all functions
- Use type hints where helpful
- Follow existing naming conventions

## Troubleshooting

### Environment Issues

If you get "Module not found" errors:
1. Ensure virtual environment is activated (`(venv)` in prompt)
2. Reinstall dependencies: `pip install -r requirements.txt`

### Database Connection Issues

1. Verify `.env` file has correct DATABASE_URL
2. Check SSL certificate path
3. Ensure database is accessible from your network

### UI Issues

1. Make sure Streamlit is installed: `pip install streamlit`
2. Check that port 8501 is available
3. Verify all dependencies are installed

## Future Enhancements

### Core Functionality
- [ ] Backtesting engine implementation
- [ ] Strategy configuration interface
- [ ] Performance metrics and reporting
- [ ] Multi-timeframe analysis
- [ ] Portfolio optimization features
- [ ] Risk management tools

### Technical Indicators
- [ ] Moving Averages (SMA, EMA, WMA)
- [ ] RSI (Relative Strength Index)
- [ ] MACD (Moving Average Convergence Divergence)
- [ ] Bollinger Bands
- [ ] Fibonacci Retracements
- [ ] Support/Resistance levels
- [ ] Volume indicators

### UI/UX Improvements
- [ ] Export functionality (CSV, Excel)
- [ ] Chart annotations and drawing tools
- [ ] Multiple chart layouts
- [ ] Dark/light theme toggle
- [ ] Chart templates and presets
- [ ] Real-time data streaming
- [ ] Advanced filtering and search

## License

This project is for educational and research purposes.