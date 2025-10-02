# Timeframe Normalization

## Overview

The backtesting system supports multiple timeframe naming conventions to ensure compatibility across different data sources (crypto exchanges, TradFi providers, etc.).

## Supported Formats

### Database Format (default)
- `m1`, `m5`, `m15`, `m30` - Minutes
- `h1`, `h2`, `h4`, `h6`, `h12` - Hours
- `d1`, `d7` - Days
- `w1` - Week
- `M1` - Month

### Standard Format
- `1m`, `5m`, `15m`, `30m` - Minutes
- `1h`, `2h`, `4h`, `6h`, `12h` - Hours
- `1d`, `7d` - Days
- `1w` - Week
- `1M` - Month

## TimeframeNormalizer API

### Basic Conversions

```python
from src.utils import TimeframeNormalizer

# Convert to standard format (1m, 5m, 1h)
TimeframeNormalizer.to_standard('m5')  # Returns: '5m'
TimeframeNormalizer.to_standard('h1')  # Returns: '1h'

# Convert to database format (m5, h1)
TimeframeNormalizer.to_db_format('5m')  # Returns: 'm5'
TimeframeNormalizer.to_db_format('1h')  # Returns: 'h1'
```

### Equivalence Checking

```python
# Check if two timeframes are equivalent
TimeframeNormalizer.are_equivalent('m5', '5m')  # Returns: True
TimeframeNormalizer.are_equivalent('h1', '1h')  # Returns: True
```

### Finding Matches

```python
# Find matching timeframe in available list
available = ['m1', 'm5', 'h1', 'd1']
TimeframeNormalizer.find_matching_timeframe('5m', available)  # Returns: 'm5'
TimeframeNormalizer.find_matching_timeframe('1h', available)  # Returns: 'h1'
```

### Duration Conversion

```python
# Convert to minutes for sorting/comparison
TimeframeNormalizer.to_minutes('m5')   # Returns: 5
TimeframeNormalizer.to_minutes('h1')   # Returns: 60
TimeframeNormalizer.to_minutes('d1')   # Returns: 1440
```

### Column Prefix Detection

```python
# Find actual column prefix in DataFrame
columns = ['timestamp', 'close', 'm5_close', 'h1_close']
TimeframeNormalizer.get_column_prefix('5m', columns)  # Returns: 'm5'
```

## Usage in Strategies

### Multi-timeframe Strategy Example

```python
from src.utils import TimeframeNormalizer

class MyStrategy(BaseStrategy):
    def __init__(self, config: dict = None):
        # ... setup ...

        # Normalize timeframes automatically
        self.m5_tf = None
        self.h1_tf = None

        for tf in self.timeframes:
            tf_standard = TimeframeNormalizer.to_standard(tf)
            if tf_standard == '5m':
                self.m5_tf = tf  # Store original format
            elif tf_standard == '1h':
                self.h1_tf = tf

    def generate_signals(self, data: pd.DataFrame, timestamp: datetime):
        # Use dynamic column names based on actual format
        h1_close = data[f'{self.h1_tf}_close']
        m5_close = data[f'{self.m5_tf}_close']
        # ... strategy logic ...
```

### UI Integration

```python
from src.utils import TimeframeNormalizer

# Find required timeframes regardless of format
m5_match = TimeframeNormalizer.find_matching_timeframe('5m', config['timeframes'])
h1_match = TimeframeNormalizer.find_matching_timeframe('1h', config['timeframes'])

if not m5_match or not h1_match:
    st.error("Missing required timeframes!")
    return

# Use actual format from data
strategy_config = {
    'timeframes': [m5_match, h1_match]
}
```

## Benefits

1. **Format Independence**: Works with any timeframe naming convention
2. **Automatic Detection**: Finds matching timeframes regardless of format
3. **Bidirectional Conversion**: Convert between any supported formats
4. **Cross-Market Support**: Handles both crypto and TradFi conventions
5. **Future-Proof**: Easy to add new timeframe formats

## Implementation Details

The normalizer uses regex pattern matching and lookup tables to:
- Parse timeframe strings in any format
- Convert between different conventions
- Sort timeframes by duration
- Match equivalent timeframes

All conversions are bidirectional and maintain consistency across the entire backtesting system.
