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

To add a new technical indicator:

1. **Create Indicator Class** (`src/indicators/your_indicator.py`):
   ```python
   from .base import BaseIndicator

   class YourIndicator(BaseIndicator):
       def __init__(self, config=None):
           super().__init__("Your Indicator", config)

       def calculate(self, data):
           # Implementation
           pass

       def get_plot_data(self):
           # Return plot configuration
           pass
   ```

2. **Add Default Settings** (`ui/components/indicator_defaults.py`):
   ```python
   'Your Indicator': {
       'enabled': False,
       'parameter1': 'default_value',
       # ... other defaults
   }
   ```

3. **Register Indicator** (`ui/components/indicator_config.py`):
   ```python
   self.available_indicators = {
       'Your Indicator': YourIndicator,
       # ... existing indicators
   }
   ```

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