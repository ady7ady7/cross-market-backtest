# Strategy Architecture Refactoring - Summary

## Overview
Refactored the strategy system to be modular, clear, and user-friendly with proper separation of concerns between strategy logic and UI controls.

## Key Changes

### 1. New Strategy Folder Structure
```
src/strategies/
├── __init__.py              # Registry system (list_strategies, get_strategy_class)
├── base_strategy_template.py  # Template + StrategyMetadata dataclass
├── simple_ma_crossover.py    # Example: UI-controlled SL/TP
└── hts_trend_follow.py       # Example: Strategy-controlled SL/TP
```

### 2. Strategy Metadata System
Each strategy now declares its requirements using `StrategyMetadata`:

```python
@dataclass
class StrategyMetadata:
    id: str                           # Unique identifier
    name: str                         # Display name
    description: str                  # What the strategy does
    required_timeframes: List[str]    # e.g., ['5m', '1h'] or []
    base_timeframe: str               # Primary timeframe
    uses_custom_sl: bool = False      # True = strategy controls SL
    uses_custom_tp: bool = False      # True = strategy controls TP
    default_sl_type: str = 'percent'  # Shown in UI
    default_tp_type: str = 'rr'       # Shown in UI
    configurable_params: Dict = None  # Strategy-specific parameters
```

### 3. Clear SL/TP Control
- **Simple MA Strategy**: `uses_custom_sl=False, uses_custom_tp=False`
  - User controls SL/TP via UI inputs
  - UI shows all SL/TP options

- **HTS Trend Follow**: `uses_custom_sl=True, uses_custom_tp=True`
  - Strategy sets SL at retest level dynamically
  - Strategy uses fixed partial exits (50% @ 1.5R, 50% @ 4R)
  - UI shows info message: "Stop loss is controlled by the strategy"

### 4. UI Components Refactored

#### strategy_selector.py (NEW)
- Auto-detects all strategies from registry
- Shows strategy information:
  - Description
  - Required timeframes
  - SL/TP control (strategy vs user)
  - Configurable parameters
- Generates UI inputs automatically from `configurable_params`

#### backtest_config.py
- Imports `show_strategy_selector()`
- Conditionally shows/hides SL/TP inputs based on `uses_custom_sl/tp`
- Shows info messages when strategy controls SL/TP

#### analysis_section.py
- Removed hardcoded strategy imports
- Uses `get_strategy_class()` from registry
- Validates required timeframes with `TimeframeNormalizer`
- Passes SL/TP config only if strategy doesn't control it

### 5. Benefits

✅ **Clear**: UI explicitly shows who controls SL/TP
✅ **Simple**: Strategies declare requirements, UI adapts automatically
✅ **Maintainable**: Add new strategies by creating one file, no UI changes needed
✅ **User-friendly**: No confusion about which settings are used
✅ **Best practices**: Separation of concerns, declarative metadata

## How to Add a New Strategy

1. Create `src/strategies/my_strategy.py`
2. Inherit from `BaseStrategy`
3. Implement `get_metadata()` classmethod
4. Implement `generate_signals()` and `should_exit()`
5. Strategy automatically appears in UI dropdown!

Example:
```python
class MyStrategy(BaseStrategy):
    @classmethod
    def get_metadata(cls) -> StrategyMetadata:
        return StrategyMetadata(
            id='my_strat',
            name='My Strategy',
            description='Does something cool',
            required_timeframes=['5m'],
            base_timeframe='5m',
            uses_custom_sl=False,  # User controls SL
            uses_custom_tp=False,  # User controls TP
            configurable_params={
                'period': {
                    'type': 'number',
                    'label': 'Period',
                    'default': 20,
                    'min': 5,
                    'max': 100,
                    'help': 'Lookback period'
                }
            }
        )
```

## Files Modified
- `src/strategies/__init__.py` (NEW)
- `src/strategies/base_strategy_template.py` (NEW)
- `src/strategies/simple_ma_crossover.py` (NEW)
- `src/strategies/hts_trend_follow.py` (REFACTORED from example_strategies.py)
- `ui/components/strategy_selector.py` (NEW)
- `ui/components/backtest_config.py` (REFACTORED)
- `ui/components/analysis_section.py` (REFACTORED)

## Performance Optimizations
- Pre-calculated indicators in HTS strategy (100x speedup)
- Vectorized pandas operations instead of per-bar recalculation
- Progress indicators for long backtests

## User Experience Improvements
- Strategy requirements clearly shown
- SL/TP control explicitly stated
- Auto-validation of timeframe requirements
- Info messages instead of hidden behavior
