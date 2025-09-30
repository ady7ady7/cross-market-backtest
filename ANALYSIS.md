# Backtesting & Analysis Layer

Comprehensive backtesting infrastructure for multi-strategy, multi-timeframe trading analysis with advanced position management and performance analytics.

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Quick Start](#quick-start)
4. [Core Components](#core-components)
5. [Creating Strategies](#creating-strategies)
6. [Position Management](#position-management)
7. [Multi-Timeframe Analysis](#multi-timeframe-analysis)
8. [Performance Metrics](#performance-metrics)
9. [UI Usage](#ui-usage)
10. [Advanced Features](#advanced-features)
11. [Best Practices](#best-practices)

---

## Overview

The analysis layer provides a complete backtesting engine supporting:

- **Multi-timeframe strategies**: Test strategies using multiple timeframes (e.g., 1m + 5m + 1h)
- **Multi-strategy execution**: Run multiple strategies simultaneously and track individually
- **Advanced position management**: Multiple SL/TP types (%, R:R, time-based, condition-based)
- **Partial position exits**: Close positions in stages (e.g., 50% at 2R, 50% at 3R)
- **Risk management**: Maximum total risk limits across all positions
- **Comprehensive analytics**: Equity curves, drawdowns, Sharpe/Sortino ratios, and more

### Design Principles

- **Simple**: Clean API, easy to understand
- **Organized**: Modular structure following existing conventions
- **Time-aligned**: Proper multi-timeframe synchronization to avoid lookahead bias
- **Extensible**: Easy to add new strategies and features

---

## Architecture

```
src/backtesting/
├── __init__.py              # Package exports
├── engine.py                # Main backtesting engine
├── data_alignment.py        # Multi-timeframe data alignment
├── strategy.py              # Base strategy class and signal handling
├── position.py              # Position and position manager
├── performance.py           # Performance tracking and metrics
└── example_strategies.py    # Example strategy implementations

ui/components/
├── backtest_config.py       # Backtesting configuration UI
├── backtest_results.py      # Results visualization
└── analysis_section.py      # Main analysis tab integration
```

### Component Responsibilities

| Component | Purpose |
|-----------|---------|
| **BacktestEngine** | Orchestrates backtest execution, main loop |
| **MultiTimeframeAligner** | Aligns data from multiple timeframes properly |
| **BaseStrategy** | Base class for all strategies |
| **Position** | Represents a single trading position |
| **PositionManager** | Manages multiple positions, risk controls |
| **PerformanceTracker** | Tracks equity, drawdowns, calculates metrics |

---

## Quick Start

### 1. Basic Backtest via UI

1. Launch the application: `python run_ui.py`
2. Navigate to **Analysis** tab
3. Configure your backtest:
   - Select symbol and timeframes
   - Set initial capital and risk limits
   - Choose strategy type (Simple MA Crossover to start)
   - Configure position management (SL/TP settings)
4. Click **Run Backtest**
5. View results: equity curve, metrics, trades

### 2. Programmatic Backtest

```python
from src.backtesting import BacktestEngine
from src.backtesting.example_strategies import SimpleMAStrategy
from src.database import create_db_connection
from src.data_fetcher import fetch_market_data

# Load data
engine = create_db_connection()
data_1h = fetch_market_data(engine, 'xauusd_1h', 'xauusd')

# Create strategy
strategy = SimpleMAStrategy(config={
    'fast_period': 20,
    'slow_period': 50,
    'risk_percent': 1.0,
    'sl_percent': 2.0,
    'tp_rr_ratio': 2.0
})

# Run backtest
backtest = BacktestEngine(initial_capital=10000, max_total_risk_percent=6.0)
results = backtest.run(
    strategies=[strategy],
    data_dict={'1h': data_1h}
)

# View results
print(results['summary'])
```

---

## Core Components

### BacktestEngine

Main orchestrator that runs the backtest loop.

**Key Methods:**
- `run(strategies, data_dict, start_date, end_date)`: Execute backtest
- Returns comprehensive results dictionary

**Example:**
```python
backtest = BacktestEngine(
    initial_capital=10000.0,
    max_total_risk_percent=6.0  # Max 6% of capital at risk
)

results = backtest.run(
    strategies=[strategy1, strategy2],
    data_dict={'1m': df_1m, '5m': df_5m, '1h': df_1h}
)
```

### MultiTimeframeAligner

Ensures proper time synchronization across timeframes.

**Critical Concept**: For any timestamp, only **closed** candles from higher timeframes are available.

Example at 08:04 (1m candles):
- Valid 5m candle: 07:55-08:00 (last closed 5m bar)
- Valid 1h candle: 07:00-08:00 (last closed 1h bar)

This prevents lookahead bias.

**Usage:**
```python
aligner = MultiTimeframeAligner(['1m', '5m', '1h'])
aligned_data = aligner.align_data({
    '1m': df_1m,
    '5m': df_5m,
    '1h': df_1h
})
# Result: DataFrame with 1m base + columns prefixed with '5m_' and '1h_'
```

### PositionManager

Manages all positions with risk controls.

**Features:**
- Position sizing based on risk %
- Maximum total risk enforcement
- Tracks open and closed positions
- Per-strategy position tracking

**Example:**
```python
manager = PositionManager(
    initial_capital=10000,
    max_total_risk_percent=6.0
)

# Check if can open new position
if manager.can_open_position:
    position = manager.open_position(
        strategy_name="MA Crossover",
        entry_time=timestamp,
        entry_price=1800.50,
        side=PositionSide.LONG,
        config=position_config
    )
```

### PerformanceTracker

Tracks equity curve and calculates metrics.

**Metrics Calculated:**
- Basic: Total return, P&L, win rate
- Risk: Max drawdown, average drawdown
- Risk-adjusted: Sharpe ratio, Sortino ratio, Calmar ratio
- Trade stats: Avg duration, R-multiples, expectancy

---

## Creating Strategies

### Strategy Structure

All strategies inherit from `BaseStrategy`:

```python
from src.backtesting.strategy import BaseStrategy, StrategySignal
from src.backtesting.position import PositionSide, Position
from typing import Optional
from datetime import datetime
import pandas as pd

class MyStrategy(BaseStrategy):
    def __init__(self, config: dict = None):
        default_config = {
            'parameter1': 20,
            'risk_percent': 1.0,
            'sl_percent': 2.0,
            'tp_rr_ratio': 2.0
        }
        if config:
            default_config.update(config)

        super().__init__(
            name="My Strategy",
            timeframes=['1h'],  # Timeframes this strategy uses
            config=default_config
        )

    def generate_signals(self, data: pd.DataFrame,
                        timestamp: datetime) -> Optional[StrategySignal]:
        """
        Analyze data and generate trading signals.

        Returns StrategySignal or None
        """
        # Your signal logic here
        # Access current data row:
        current_row = data[data['timestamp'] == timestamp]
        if current_row.empty:
            return None

        row = current_row.iloc[0]

        # Example: Buy if price crosses above MA
        if row['close'] > row['ma_50']:
            return StrategySignal(
                timestamp=timestamp,
                side=PositionSide.LONG,
                confidence=1.0,
                metadata={'reason': 'Price above MA50'}
            )

        return None

    def should_exit(self, position: Position, data: pd.DataFrame,
                   timestamp: datetime) -> bool:
        """
        Check if position should be closed based on strategy logic.

        This is called AFTER SL/TP checks, for additional exit conditions.
        """
        # Your exit logic here
        return False
```

### Multi-Timeframe Strategy

```python
class MultiTFStrategy(BaseStrategy):
    def __init__(self, config: dict = None):
        super().__init__(
            name="Multi-TF Strategy",
            timeframes=['5m', '1h'],  # Uses both 5m and 1h
            config=config
        )

    def generate_signals(self, data: pd.DataFrame,
                        timestamp: datetime) -> Optional[StrategySignal]:
        row = data[data['timestamp'] == timestamp].iloc[0]

        # Access 1h data (last closed 1h candle)
        h1_close = row['1h_close']
        h1_high = row['1h_high']

        # Access 5m data (current timeframe)
        m5_close = row['5m_close']

        # Example: Trend from 1h, entry on 5m
        if h1_close > h1_high * 0.995:  # Bullish 1h
            if m5_close > row['5m_ma_20']:  # 5m confirmation
                return StrategySignal(
                    timestamp=timestamp,
                    side=PositionSide.LONG
                )

        return None
```

### Strategy Configuration

Configure position management per strategy:

```python
strategy = MyStrategy(config={
    # Strategy parameters
    'fast_period': 20,
    'slow_period': 50,

    # Position management
    'risk_percent': 1.0,      # Risk 1% per trade

    # Stop Loss
    'sl_type': 'percent',     # 'percent', 'time', 'condition'
    'sl_percent': 2.0,        # 2% SL

    # Take Profit
    'tp_type': 'rr',          # 'rr', 'percent', 'condition'
    'tp_rr_ratio': 2.0,       # 1:2 risk:reward

    # Partial Exits (optional)
    'partial_exits': [
        (0.5, 2.0),  # Close 50% at 2R
        (0.5, 3.0)   # Close remaining at 3R
    ]
})
```

---

## Position Management

### SL/TP Types

#### 1. Percentage-Based

```python
config = {
    'sl_type': 'percent',
    'sl_percent': 2.0,     # 2% from entry
    'tp_type': 'percent',
    'tp_percent': 4.0      # 4% from entry
}
```

**Use case**: Fixed risk/reward percentages

#### 2. Risk:Reward Ratio

```python
config = {
    'sl_type': 'percent',
    'sl_percent': 1.0,     # 1% SL
    'tp_type': 'rr',
    'tp_rr_ratio': 3.0     # Take profit at 3R (3x the risk)
}
```

**Use case**: Consistent R:R ratios

#### 3. Time-Based

```python
config = {
    'sl_type': 'time',
    'sl_time_bars': 50     # Exit after 50 bars if not hit SL/TP
}
```

**Use case**: Time decay strategies

#### 4. Condition-Based

```python
def should_exit(self, position, data, timestamp):
    # Custom exit logic
    row = data[data['timestamp'] == timestamp].iloc[0]

    # Example: Exit if RSI overbought
    if row['rsi'] > 70:
        return True

    return False
```

**Use case**: Complex exit conditions

### Partial Position Exits

Close positions in stages:

```python
config = {
    'risk_percent': 2.0,
    'sl_percent': 2.0,
    'partial_exits': [
        (0.5, 2.0),  # Take 50% profit at 2R
        (0.3, 3.0),  # Take 30% profit at 3R
        (0.2, 5.0)   # Take remaining 20% at 5R
    ]
}
```

**Benefits:**
- Lock in profits early
- Let winners run
- Reduce risk after partial exit

### Risk Management

Maximum total risk prevents over-leveraging:

```python
backtest = BacktestEngine(
    initial_capital=10000,
    max_total_risk_percent=6.0  # Never risk more than 6% total
)
```

If 3 positions each risk 2%, cannot open 4th position until one closes.

---

## Multi-Timeframe Analysis

### Time Alignment

The system automatically aligns timeframes using `merge_asof` with backward direction:

```python
# At 08:04 on 1m chart:
# - 1m candle: 08:04-08:05 (current bar)
# - 5m candle: 07:55-08:00 (last CLOSED 5m)
# - 1h candle: 07:00-08:00 (last CLOSED 1h)
```

This ensures no lookahead bias.

### Accessing Multi-Timeframe Data

In strategies, data columns are prefixed:

```python
def generate_signals(self, data, timestamp):
    row = data[data['timestamp'] == timestamp].iloc[0]

    # Base timeframe (no prefix)
    close = row['close']
    high = row['high']

    # Higher timeframe (prefixed)
    h1_close = row['1h_close']
    h1_ma50 = row['1h_ma_50']  # If you added MA indicator
```

### Multi-Timeframe Strategy Pattern

Common pattern: **Higher timeframe for trend, lower for entry**

```python
class TrendFollowStrategy(BaseStrategy):
    def __init__(self):
        super().__init__(
            name="Trend Follow",
            timeframes=['15m', '1h', '4h']  # Entry, trend, filter
        )

    def generate_signals(self, data, timestamp):
        row = data[data['timestamp'] == timestamp].iloc[0]

        # 4h trend filter
        if row['4h_ma_200'] > row['4h_close']:
            return None  # Only trade with 4h trend

        # 1h trend
        h1_bullish = row['1h_close'] > row['1h_ma_50']

        # 15m entry
        m15_entry = row['close'] > row['15m_ma_20']

        if h1_bullish and m15_entry:
            return StrategySignal(timestamp=timestamp, side=PositionSide.LONG)

        return None
```

---

## Performance Metrics

### Metrics Calculated

| Metric | Description |
|--------|-------------|
| **Total Return** | Final capital - initial capital |
| **Win Rate** | % of winning trades |
| **Profit Factor** | Gross profit / Gross loss |
| **Max Drawdown** | Largest peak-to-trough decline |
| **Avg Drawdown** | Average of all drawdowns |
| **Sharpe Ratio** | Risk-adjusted return (considers all volatility) |
| **Sortino Ratio** | Risk-adjusted return (considers only downside) |
| **Calmar Ratio** | Return / Max drawdown |
| **Avg R-Multiple** | Average profit in terms of initial risk |
| **Expectancy** | Average $ per trade |

### Understanding R-Multiples

R-multiple measures profit in terms of initial risk:

- **1R**: Profit equals initial risk (if risked $100, made $100)
- **2R**: Profit is 2x initial risk (risked $100, made $200)
- **-1R**: Lost the full risk amount

**Example:**
```
Entry: $1800
Stop Loss: $1760 (risk = $40)
Exit: $1880 (profit = $80)

R-multiple = $80 / $40 = 2R
```

**Why R-multiples?**
- Normalizes trades of different sizes
- Shows quality of exits vs risk taken
- Avg R > 0 = profitable system

---

## UI Usage

### Configuration UI

Access via **Analysis** tab:

1. **Symbol & Timeframes**
   - Select symbol to test
   - Choose timeframes (first is base timeframe)

2. **Date Range**
   - Use full range or specify dates
   - Useful for in-sample/out-of-sample testing

3. **Capital & Risk**
   - Initial capital
   - Max total risk % (across all positions)

4. **Strategy Type**
   - Select pre-built strategy
   - Or implement custom in code

5. **Position Management**
   - Risk per trade
   - SL type and parameters
   - TP type and parameters
   - Optional partial exits

6. **Run**
   - Click "Run Backtest"
   - Save configuration for reuse

### Results Visualization

Results shown in 4 tabs:

#### 1. Equity Curve
- Total equity over time
- Realized vs unrealized P&L
- Visual representation of growth

#### 2. Drawdown Analysis
- Equity vs peak equity
- Drawdown % over time
- DD statistics (max, avg, duration)

#### 3. Trade Analysis
- P&L distribution histogram
- R-multiple distribution
- Trade-by-trade log
- CSV export

#### 4. Detailed Metrics
- All performance metrics
- Trade statistics
- Risk metrics
- Duration stats

### Multi-Strategy Results

When testing multiple strategies:
- Individual strategy metrics shown
- Comparison table
- Combined equity curve

---

## Advanced Features

### Multiple Concurrent Strategies

Test multiple strategies simultaneously:

```python
strategy1 = SimpleMAStrategy(config={'fast_period': 20, 'slow_period': 50})
strategy2 = SimpleMAStrategy(config={'fast_period': 10, 'slow_period': 30})

results = backtest.run(
    strategies=[strategy1, strategy2],
    data_dict=data_dict
)

# Each strategy tracked separately
for name, metrics in results['strategy_metrics'].items():
    print(f"{name}: {metrics.total_return_pct:.2f}%")
```

**Use cases:**
- Compare different parameter sets
- Portfolio of strategies
- Diversification analysis

### Custom Indicators in Strategies

Add indicators to data before backtesting:

```python
# Add indicators to your dataframe
df['ma_20'] = df['close'].rolling(20).mean()
df['ma_50'] = df['close'].rolling(50).mean()
df['rsi'] = calculate_rsi(df['close'], 14)

# Use in strategy
class IndicatorStrategy(BaseStrategy):
    def generate_signals(self, data, timestamp):
        row = data[data['timestamp'] == timestamp].iloc[0]

        if row['ma_20'] > row['ma_50'] and row['rsi'] < 70:
            return StrategySignal(timestamp, PositionSide.LONG)

        return None
```

### Walk-Forward Analysis

Split data for robust testing:

```python
# In-sample: Train/optimize
in_sample_results = backtest.run(
    strategies=[strategy],
    data_dict=data_dict,
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2023, 6, 30)
)

# Out-of-sample: Validate
out_sample_results = backtest.run(
    strategies=[strategy],
    data_dict=data_dict,
    start_date=datetime(2023, 7, 1),
    end_date=datetime(2023, 12, 31)
)
```

---

## Best Practices

### Strategy Development

1. **Start Simple**
   - Begin with simple strategies
   - Add complexity only if needed
   - Avoid over-fitting

2. **Use Multiple Timeframes Wisely**
   - Higher TF = trend/filter
   - Lower TF = entry/exit
   - Don't use too many (3-4 max)

3. **Test Robustness**
   - Try different parameter values
   - Test on multiple symbols
   - Use walk-forward analysis

4. **Risk Management First**
   - Always define SL before entry
   - Use consistent risk per trade
   - Never exceed max total risk

### Backtesting Best Practices

1. **Avoid Lookahead Bias**
   - System handles this automatically
   - Don't manually access future data
   - Check indicator calculations

2. **Account for Slippage** (Future enhancement)
   - Current system uses exact prices
   - Real trading has slippage
   - Be conservative with results

3. **Consider Transaction Costs** (Future enhancement)
   - Not currently modeled
   - Will affect profitability
   - Factor in when analyzing results

4. **Use Sufficient Data**
   - More trades = more reliable stats
   - Need 30+ trades for significance
   - Test across market conditions

### Performance Analysis

1. **Don't Chase High Returns**
   - Focus on risk-adjusted returns
   - Sharpe ratio > 1.0 is good
   - Consistency > big wins

2. **Monitor Drawdowns**
   - Max DD should be acceptable
   - Avg DD shows typical pain
   - DD duration matters for psychology

3. **Check Win Rate Context**
   - High win rate + low profit factor = small wins, big losses
   - Low win rate + high profit factor = big wins, small losses
   - Both can be profitable

4. **Expectancy is King**
   - Positive expectancy = profitable
   - Higher is better
   - Multiply by # trades for expected profit

---

## Troubleshooting

### Common Issues

**1. No trades generated**
- Check strategy logic
- Verify signal generation
- Ensure sufficient data for indicators

**2. All trades hit stop loss**
- SL too tight
- Strategy not catching trends
- Review entry conditions

**3. Memory issues with large datasets**
- Use date range filtering
- Test on shorter periods first
- Consider higher timeframes

**4. Results look too good**
- Check for lookahead bias
- Verify indicator calculations
- Test on out-of-sample data

### Debug Mode

Add debug prints in your strategy:

```python
def generate_signals(self, data, timestamp):
    row = data[data['timestamp'] == timestamp].iloc[0]

    print(f"[{timestamp}] Close: {row['close']}, MA: {row['ma_50']}")

    if row['close'] > row['ma_50']:
        print(f"  -> BUY SIGNAL")
        return StrategySignal(timestamp, PositionSide.LONG)

    return None
```

---

## Future Enhancements

Potential improvements:

- [ ] **Commission/Slippage modeling**
- [ ] **More built-in strategies**
- [ ] **Strategy optimization** (grid search, genetic algorithms)
- [ ] **Monte Carlo analysis**
- [ ] **Trade visualization on price charts** (see entry/exit points)
- [ ] **Export reports** (PDF, Excel)
- [ ] **Portfolio backtesting** (multiple symbols)
- [ ] **Live trading interface** (paper trading)
- [ ] **Strategy templates library**
- [ ] **Parameter optimization UI**

---

## Examples

### Complete Example: Multi-Timeframe Trend Strategy

```python
from src.backtesting import BacktestEngine
from src.backtesting.strategy import BaseStrategy, StrategySignal
from src.backtesting.position import PositionSide

class TrendStrategy(BaseStrategy):
    """Trend following using 1h and 4h timeframes"""

    def __init__(self):
        super().__init__(
            name="Trend Follow",
            timeframes=['1h', '4h'],
            config={
                'risk_percent': 1.5,
                'sl_percent': 2.0,
                'tp_rr_ratio': 3.0,
                'partial_exits': [(0.5, 2.0), (0.5, 4.0)]
            }
        )

    def generate_signals(self, data, timestamp):
        row = data[data['timestamp'] == timestamp].iloc[0]

        # Calculate MAs (you'd add these to data beforehand)
        # For demo, using simple price logic

        h1_close = row.get('1h_close')
        h4_close = row.get('4h_close')

        if pd.isna(h1_close) or pd.isna(h4_close):
            return None

        current_close = row['close']

        # Simple trend: both timeframes showing strength
        if h1_close > h4_close * 0.998 and current_close > h1_close:
            return StrategySignal(timestamp, PositionSide.LONG)

        return None

    def should_exit(self, position, data, timestamp):
        # Exit if trend breaks on 4h
        row = data[data['timestamp'] == timestamp].iloc[0]
        h4_close = row.get('4h_close')

        if position.side == PositionSide.LONG:
            if h4_close < position.entry_price * 0.995:
                return True

        return False

# Run backtest
from src.database import create_db_connection
from src.data_fetcher import fetch_market_data

engine = create_db_connection()
data_1h = fetch_market_data(engine, 'xauusd_1h', 'xauusd')
data_4h = fetch_market_data(engine, 'xauusd_4h', 'xauusd')

strategy = TrendStrategy()

backtest = BacktestEngine(initial_capital=10000, max_total_risk_percent=6)
results = backtest.run(
    strategies=[strategy],
    data_dict={'1h': data_1h, '4h': data_4h}
)

# Print results
print("=" * 50)
print("BACKTEST RESULTS")
print("=" * 50)
for key, value in results['summary'].items():
    print(f"{key:.<30} {value}")
print("=" * 50)
```

---

## Support & Contribution

For questions or issues:
- Check this documentation
- Review example strategies in `src/backtesting/example_strategies.py`
- Open an issue on the repository

When reporting issues:
1. Describe the strategy configuration
2. Include error messages
3. Specify data being used
4. Provide minimal reproducible example

---

## License & Disclaimer

This backtesting system is for educational and research purposes.

**Disclaimer**: Past performance does not guarantee future results. Backtested results are hypothetical and do not represent actual trading. Always test strategies with paper trading before risking real capital.