# Analysis Layer - Design Decisions & Rationale

This document explains the architectural choices made for the backtesting analysis layer.

## Context & Requirements

You requested a backtesting infrastructure with:
- Multi-timeframe strategy support
- Multi-strategy capability with individual tracking
- Proper time alignment to avoid lookahead bias
- Multiple SL/TP types (%, R:R, time-based, condition-based)
- Partial position exits
- Maximum total risk management
- Comprehensive performance visualization

## Key Design Decisions

### 1. Data Structure: Single Aligned DataFrame

**Decision**: Use one mega-row containing all timeframe data with prefixed columns.

**Rationale**:
- **Simplicity**: Single data structure to pass around, easier to reason about
- **Performance**: One merge operation upfront vs repeated lookups
- **Clarity**: Column naming (`1h_close`, `5m_high`) makes timeframe explicit
- **Pandas-native**: Leverages `merge_asof` for proper time alignment

**Alternative Considered**: Dictionary of separate DataFrames per timeframe
- Would require complex lookup logic
- More error-prone (accessing wrong timeframe)
- Harder to add indicators across timeframes

**Implementation**: `MultiTimeframeAligner.align_data()`

```python
# Result structure:
# timestamp | close | high | low | open | 5m_close | 5m_high | ... | 1h_close | 1h_high | ...
```

---

### 2. Time Alignment: merge_asof with Backward Direction

**Decision**: Use pandas `merge_asof` with `direction='backward'` to align timeframes.

**Rationale**:
- **No Lookahead Bias**: Only gets previous closed candles from higher timeframes
- **Automatic**: Pandas handles the alignment logic
- **Correct by Default**: Can't accidentally access future data

**Example**: At 08:04 on 1m chart:
- 1m candle: 08:04 (current)
- 5m candle: 07:55-08:00 (last closed)
- 1h candle: 07:00-08:00 (last closed)

This is how real trading works - you only know completed higher TF candles.

**Implementation**: `MultiTimeframeAligner._merge_timeframe()`

---

### 3. Strategy Architecture: Base Class with Two Key Methods

**Decision**: Simple base class requiring only `generate_signals()` and `should_exit()`.

**Rationale**:
- **Minimal Interface**: Only implement what's necessary for your strategy
- **Clear Separation**: Entry logic separate from exit logic
- **Extensible**: Easy to add new strategies
- **Testable**: Each method can be tested independently

**Alternative Considered**: More methods (e.g., on_bar_update, on_position_opened, etc.)
- Over-engineering for initial version
- Can add later if needed
- Keeps things simple as requested

**Implementation**: `BaseStrategy` in `strategy.py`

```python
class MyStrategy(BaseStrategy):
    def generate_signals(self, data, timestamp):
        # Return signal or None
        pass

    def should_exit(self, position, data, timestamp):
        # Return True/False
        pass
```

---

### 4. Position Management: Separate Position and PositionManager

**Decision**: `Position` dataclass for state, `PositionManager` for operations and risk control.

**Rationale**:
- **Single Responsibility**: Position holds data, Manager handles logic
- **Risk Control Centralized**: All risk checks in one place
- **Easy Testing**: Can test Position logic independently
- **Clear State**: Position is immutable except through Manager

**Key Features**:
- Automatic position sizing based on risk %
- Max total risk enforcement (won't open if exceeds limit)
- Per-strategy position tracking
- Support for partial exits

**Implementation**: `position.py`

---

### 5. Performance Tracking: Running Calculations

**Decision**: Track equity continuously, calculate metrics at end.

**Rationale**:
- **Efficiency**: Don't recalculate entire equity curve on each bar
- **Accuracy**: Track drawdowns in real-time as they happen
- **Complete History**: Full equity curve for visualization

**Metrics Chosen**:
- **Basic**: Return, win rate, profit factor (understand profitability)
- **Risk**: Max/avg drawdown (understand downside)
- **Risk-Adjusted**: Sharpe, Sortino (compare strategies fairly)
- **Trade-Based**: R-multiples, expectancy (understand per-trade performance)

**Implementation**: `PerformanceTracker` in `performance.py`

---

### 6. UI Structure: Configuration + Results Separation

**Decision**: Separate components for config (`backtest_config.py`) and results (`backtest_results.py`).

**Rationale**:
- **Reusability**: Results viewer can be used independently
- **Clarity**: Config UI separate from results visualization
- **Maintenance**: Easy to modify one without affecting other

**UI Flow**:
1. Configure in expander (keeps it compact)
2. Run button
3. Results appear below (persistent until reset)

**Implementation**: `ui/components/backtest_*.py`

---

### 7. Multi-Strategy Support: Composer Pattern

**Decision**: `MultiStrategyComposer` to coordinate multiple strategies.

**Rationale**:
- **Encapsulation**: Strategy coordination logic in one place
- **Scalable**: Easy to add more strategies
- **Independent Tracking**: Each strategy tracked separately
- **Allocation Future-Proof**: Can implement different capital allocation methods later

**Current**: Simple approach - each strategy independent
**Future**: Could add portfolio allocation, correlation checks, etc.

**Implementation**: `MultiStrategyComposer` in `strategy.py`

---

### 8. SL/TP Flexibility: Configuration-Based

**Decision**: Multiple SL/TP types defined in `PositionConfig`, checked in engine loop.

**Rationale**:
- **Flexibility**: Each strategy can use different SL/TP logic
- **Extensible**: Easy to add new types
- **Clear**: All position rules in config object

**Types Supported**:
- **Percent**: Simple fixed % from entry
- **R:R Ratio**: Based on risk amount
- **Time**: Exit after N bars
- **Condition**: Custom strategy logic

**Partial Exits**: List of (fraction, R-multiple) tuples
- Example: `[(0.5, 2.0), (0.5, 3.0)]` = 50% at 2R, 50% at 3R

**Implementation**: `PositionConfig` dataclass

---

### 9. Results Visualization: Tabbed Interface

**Decision**: Four tabs for different aspects of results.

**Rationale**:
- **Organization**: Don't overwhelm with all metrics at once
- **Progressive Disclosure**: Show summary first, details on demand
- **Use Case Focused**: Each tab serves specific analysis need

**Tabs**:
1. **Equity Curve**: Visual performance overview
2. **Drawdown**: Risk analysis
3. **Trade Analysis**: Per-trade breakdown
4. **Detailed Metrics**: All numbers

**Interactive Charts**: Using Plotly for zoom, hover, exploration

**Implementation**: `BacktestResults.show_results()`

---

### 10. File Organization: Modular by Responsibility

**Decision**: Separate files for each major component.

**Rationale**:
- **Maintainability**: Easy to find and modify specific functionality
- **Testability**: Can test modules independently
- **Follows Existing Pattern**: Mirrors your indicators structure
- **Clear Dependencies**: Import chain is obvious

**Structure**:
```
src/backtesting/
├── engine.py          # Orchestration
├── data_alignment.py  # Time sync
├── strategy.py        # Strategy base & composition
├── position.py        # Position management
├── performance.py     # Metrics & tracking
└── example_strategies.py  # Examples
```

---

## Optimization Choices

### What Was NOT Over-Engineered

1. **No Complex Event System**
   - Could have: event bus, listeners, callbacks
   - Instead: Simple method calls in loop
   - Why: YAGNI principle, easier to understand

2. **No Abstract Factory Pattern for Strategies**
   - Could have: Registry, factory methods, dependency injection
   - Instead: Direct instantiation
   - Why: Not needed for this scale

3. **No Database Persistence for Results**
   - Could have: Save all backtests to DB
   - Instead: Session state (UI) or return dict (programmatic)
   - Why: Results are exploratory, not production system

4. **No Parallel Execution**
   - Could have: Multi-processing for multiple strategies
   - Instead: Sequential execution
   - Why: Fast enough for your data size, simpler debugging

5. **Simple Equity Tracking Per Strategy**
   - Could have: Separate PerformanceTracker per strategy with full equity curves
   - Instead: Track positions per strategy, calculate metrics at end
   - Why: Sufficient for comparison, less memory

### What WAS Optimized

1. **Single Data Alignment Upfront**
   - Align all timeframes once at start
   - Not: Align on every bar
   - Benefit: Significant speed improvement

2. **NumPy for Metrics Calculation**
   - Use vectorized operations where possible
   - Not: Python loops for statistics
   - Benefit: Fast performance calculations

3. **Session State for UI Results**
   - Cache results until reset
   - Not: Recalculate on every interaction
   - Benefit: Instant tab switching

---

## Design Trade-offs

### Trade-off 1: Simplicity vs Features

**Choice**: Simple, focused feature set
**Given Up**: Some advanced features (optimization, walk-forward built-in)
**Gained**: Easy to understand and use, extensible foundation

### Trade-off 2: Flexibility vs Safety

**Choice**: Explicit strategy methods, type hints
**Given Up**: Dynamic strategy loading, plugin system
**Gained**: Clear API, fewer runtime errors, better IDE support

### Trade-off 3: Performance vs Accuracy

**Choice**: Bar-by-bar simulation, no tick data
**Given Up**: Intra-bar accuracy, exact fill prices
**Gained**: Reasonable speed, good enough for strategy validation

### Trade-off 4: UI Simplicity vs Configuration Depth

**Choice**: Streamlit UI with forms, limited to common use cases
**Given Up**: Every possible parameter exposed
**Gained**: User-friendly, not overwhelming, good defaults

---

## Why These Choices Work for Your Use Case

1. **Multi-Timeframe Focus**
   - Proper time alignment is core
   - Integrated deeply, not bolted on
   - Can't accidentally introduce lookahead bias

2. **Multi-Strategy Testing**
   - Each strategy independent
   - Can compare side-by-side
   - Foundation for portfolio testing

3. **Risk Management Priority**
   - Max total risk is enforced
   - Position sizing automatic
   - Can't over-leverage

4. **Extensibility**
   - Easy to add new strategies
   - Can extend with custom SL/TP logic
   - Framework supports growth

5. **Practical Focus**
   - Metrics that matter (Sharpe, DD, R-multiples)
   - Visualization aids understanding
   - Export for further analysis

---

## Future Extension Points

The architecture makes these future enhancements straightforward:

1. **Slippage/Commission**
   - Add to PositionManager.open_position() and close_position()
   - Deduct from realized P&L

2. **Parameter Optimization**
   - Wrap backtest.run() in optimizer loop
   - Compare results across parameter sets

3. **Walk-Forward Analysis**
   - Run multiple backtests with date splits
   - Aggregate results

4. **Portfolio Backtesting**
   - Run multiple symbols through same engine
   - Aggregate equity curves

5. **Custom SL/TP Types**
   - Add new type to PositionConfig
   - Implement check in engine loop

6. **Strategy Templates**
   - Provide more example strategies
   - Create UI for common patterns

---

## Summary

The design prioritizes:
- ✅ **Simplicity**: Clean API, easy to understand
- ✅ **Correctness**: Proper time alignment, no lookahead bias
- ✅ **Flexibility**: Multiple SL/TP types, partial exits
- ✅ **Organization**: Modular structure, clear responsibilities
- ✅ **Extensibility**: Easy to add strategies and features
- ✅ **Practicality**: Real-world metrics and visualization

This foundation supports your current needs while remaining open for future enhancements.