# Formatting Best Practices

## Problem: Conditional Format Specifiers in F-Strings

Python f-strings do **not** support conditional expressions inside format specifiers. This will cause errors:

```python
# ❌ WRONG - This will raise "Invalid format specifier" error
take_profit = None
print(f"TP: {take_profit:.2f if take_profit else 'None'}")
```

The error occurs because Python tries to interpret `.2f if take_profit else 'None'` as a format specifier, which is invalid.

## Solution: Use Formatting Utility Functions

We've created utility functions in `src/utils/format_utils.py` to handle optional values consistently across the codebase:

### Available Functions

#### 1. `fmt_optional(value, format_spec, none_text)` - General purpose

```python
from src.utils import fmt_optional

# Format any optional numeric value
take_profit = 123.456
stop_loss = None

print(f"TP: {fmt_optional(take_profit, '.2f')}")  # "TP: 123.46"
print(f"SL: {fmt_optional(stop_loss, '.2f')}")    # "SL: None"
print(f"SL: {fmt_optional(stop_loss, '.2f', 'N/A')}")  # "SL: N/A"
```

#### 2. `fmt_price(price, decimals)` - For price values

```python
from src.utils import fmt_price

entry_price = 14675.09
take_profit = None

print(f"Entry: {fmt_price(entry_price)}")     # "Entry: 14675.09"
print(f"TP: {fmt_price(take_profit)}")        # "TP: None"
```

#### 3. `fmt_pct(value, decimals, suffix)` - For percentages

```python
from src.utils import fmt_pct

win_rate = 65.4321
loss_rate = None

print(f"Win Rate: {fmt_pct(win_rate)}")       # "Win Rate: 65.43%"
print(f"Loss Rate: {fmt_pct(loss_rate)}")     # "Loss Rate: None"
```

#### 4. `fmt_units(units, decimals)` - For position sizes

```python
from src.utils import fmt_units

position_size = 62.3441
print(f"Size: {fmt_units(position_size)}")    # "Size: 62.3441"
```

## Before & After Examples

### ❌ Before (Error-prone)

```python
# This causes: Invalid format specifier error
print(f"TP: {take_profit:.2f if take_profit else 'None'}")

# Verbose workaround
tp_str = f"{take_profit:.2f}" if take_profit else "None"
print(f"TP: {tp_str}")
```

### ✅ After (Clean & Consistent)

```python
from src.utils import fmt_price

print(f"TP: {fmt_price(take_profit)}")
```

## Best Practices

1. **Always use formatting utilities** for optional numeric values in logs, reports, and UI displays
2. **Import at module level** to keep the code clean:
   ```python
   from src.utils import fmt_price, fmt_pct, fmt_units
   ```
3. **Choose the appropriate function** based on the value type:
   - Prices → `fmt_price()`
   - Percentages → `fmt_pct()`
   - Position sizes → `fmt_units()`
   - Other numbers → `fmt_optional()`

4. **Customize when needed**:
   ```python
   # Custom decimals
   fmt_price(value, decimals=4)

   # Custom none text
   fmt_optional(value, '.2f', 'N/A')

   # Percentage without suffix
   fmt_pct(value, suffix=False)
   ```

## Where to Use These Functions

- **Strategy logging** - Entry/exit signals with optional prices
- **Position management** - Stop loss and take profit levels
- **Performance reports** - Optional metrics and statistics
- **Debug output** - Any conditional numeric display
- **UI displays** - Consistent formatting in Streamlit or other interfaces

## Implementation Note

All formatting utilities are located in:
- **Module**: `src/utils/format_utils.py`
- **Import**: `from src.utils import fmt_optional, fmt_price, fmt_pct, fmt_units`
- **Auto-exported** from `src/utils/__init__.py`

This ensures consistent, error-free formatting throughout the entire codebase, both for existing and future strategies.
