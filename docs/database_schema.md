# Database Schema Documentation

## Overview

The cross-market backtest application uses PostgreSQL to store market data across multiple assets, exchanges, and timeframes.

## Tables

### 1. Market Data Tables (OHLCV)

Each symbol-timeframe combination has its own table with standardized structure.

#### Naming Convention

```
{symbol}_{timeframe}_{asset_type}_ohlcv
```

**Examples**:
- `btcusdt_m5_crypto_ohlcv` - Bitcoin 5-minute data (crypto)
- `eurusd_m5_tradfi_ohlcv` - EUR/USD 5-minute data (traditional finance)
- `xauusd_1h_tradfi_ohlcv` - Gold 1-hour data
- `ethusdt_m15_crypto_ohlcv` - Ethereum 15-minute data

#### Table Structure

```sql
CREATE TABLE {table_name} (
    timestamp TIMESTAMPTZ NOT NULL,
    open DECIMAL(12, 8) NOT NULL,
    high DECIMAL(12, 8) NOT NULL,
    low DECIMAL(12, 8) NOT NULL,
    close DECIMAL(12, 8) NOT NULL,
    volume DECIMAL(20, 8) DEFAULT NULL,
    day_of_week TEXT NOT NULL
);
```

#### Column Details

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `timestamp` | TIMESTAMPTZ | Bar timestamp (UTC) | `2023-01-09 09:00:00+00:00` |
| `open` | DECIMAL(12,8) | Opening price | `14637.77900000` |
| `high` | DECIMAL(12,8) | Highest price in bar | `14673.89900000` |
| `low` | DECIMAL(12,8) | Lowest price in bar | `14631.78900000` |
| `close` | DECIMAL(12,8) | Closing price | `14670.76900000` |
| `volume` | DECIMAL(20,8) | Trading volume | `0.88000000` |
| `day_of_week` | TEXT | Day name | `Monday`, `Tuesday`, etc. |

#### Sample Data

```
timestamp                    | open      | high      | low       | close     | volume | day_of_week
2023-01-09 09:00:00+00:00   | 14637.779 | 14673.899 | 14631.789 | 14670.769 | 0.88   | Monday
2023-01-09 10:00:00+00:00   | 14670.731 | 14690.789 | 14657.259 | 14678.259 | 0.81   | Monday
2023-01-09 11:00:00+00:00   | 14677.711 | 14725.789 | 14676.759 | 14723.799 | 1.59   | Monday
2023-01-09 12:00:00+00:00   | 14724.799 | 14750.899 | 14694.749 | 14721.259 | 1.98   | Monday
2023-01-09 13:00:00+00:00   | 14721.799 | 14782.749 | 14718.899 | 14781.249 | 3.50   | Monday
```

#### Important Notes

- **Timeframe**: Stored in table name, NOT as a column (e.g., `m5`, `1h`, `4h`)
- **Timezone**: All timestamps are in UTC (TIMESTAMPTZ)
- **Day of Week**: Pre-calculated column - use this instead of computing from timestamp
- **Precision**: Prices stored with 8 decimal places for crypto compatibility

---

### 2. Symbol Metadata Table

Tracks all available symbol-timeframe combinations and their corresponding data tables.

#### Table Name
```
symbol_metadata
```

#### Table Structure

```sql
CREATE TABLE symbol_metadata (
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    table_name TEXT NOT NULL,
    asset_type TEXT NOT NULL,
    exchange TEXT,
    first_timestamp TIMESTAMPTZ,
    last_timestamp TIMESTAMPTZ,
    total_rows INTEGER,
    -- Additional metadata fields
);
```

#### Column Details

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `symbol` | TEXT | Symbol identifier | `xauusd`, `ETH/USDT`, `BTCUSDT` |
| `timeframe` | TEXT | Data interval | `1m`, `5m`, `15m`, `1h`, `4h`, `1d` |
| `table_name` | TEXT | OHLCV table name | `btcusdt_m5_crypto_ohlcv` |
| `asset_type` | TEXT | Asset class | `tradfi`, `crypto` |
| `exchange` | TEXT | Exchange/source | `Binance`, `Forex`, `MetaTrader` |
| `first_timestamp` | TIMESTAMPTZ | Earliest data point | `2023-01-01 00:00:00+00:00` |
| `last_timestamp` | TIMESTAMPTZ | Latest data point | `2025-12-31 23:59:00+00:00` |
| `total_rows` | INTEGER | Row count | `52560` |

#### Sample Data

```
symbol    | timeframe | table_name                  | asset_type | exchange
BTCUSDT   | 5m        | btcusdt_m5_crypto_ohlcv     | crypto     | Binance
BTCUSDT   | 1h        | btcusdt_1h_crypto_ohlcv     | crypto     | Binance
xauusd    | 5m        | xauusd_m5_tradfi_ohlcv      | tradfi     | MetaTrader
xauusd    | 1h        | xauusd_1h_tradfi_ohlcv      | tradfi     | MetaTrader
eurusd    | 5m        | eurusd_m5_tradfi_ohlcv      | tradfi     | Forex
```

#### Usage

The metadata table enables:
1. **Symbol discovery**: Find all available symbols
2. **Timeframe lookup**: Get available timeframes for a symbol
3. **Table mapping**: Map symbol+timeframe to data table
4. **Data coverage**: Check date ranges and completeness

---

## Timeframe Codes

Standard timeframe notation used throughout the system:

| Code | Description | Bars per Day (approx) |
|------|-------------|----------------------|
| `1m` | 1 minute | 1440 |
| `5m` | 5 minutes | 288 |
| `15m` | 15 minutes | 96 |
| `30m` | 30 minutes | 48 |
| `1h` | 1 hour | 24 |
| `4h` | 4 hours | 6 |
| `1d` | 1 day | 1 |

---

## Asset Types

| Type | Description | Examples |
|------|-------------|----------|
| `tradfi` | Traditional Finance | Forex (EUR/USD), Commodities (XAU/USD), Indices |
| `crypto` | Cryptocurrency | BTC/USDT, ETH/USDT, etc. |

---

## Query Examples

### Get All Timeframes for a Symbol

```sql
SELECT timeframe, table_name
FROM symbol_metadata
WHERE symbol = 'BTCUSDT'
ORDER BY timeframe;
```

### Get OHLCV Data for Specific Period

```sql
SELECT timestamp, open, high, low, close, volume, day_of_week
FROM btcusdt_m5_crypto_ohlcv
WHERE timestamp >= '2023-01-01'
  AND timestamp < '2023-02-01'
ORDER BY timestamp;
```

### Filter by Day of Week

```sql
SELECT timestamp, close, day_of_week
FROM xauusd_1h_tradfi_ohlcv
WHERE day_of_week IN ('Monday', 'Friday')
ORDER BY timestamp;
```

### Get Trading Hours Data

```sql
SELECT timestamp, close, day_of_week
FROM btcusdt_m5_crypto_ohlcv
WHERE EXTRACT(HOUR FROM timestamp) BETWEEN 10 AND 18
  AND day_of_week IN ('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday')
ORDER BY timestamp;
```

---

## Data Access in Code

### Using data_fetcher.py

```python
from src.database import create_db_connection
from src.data_fetcher import read_symbol_metadata, fetch_market_data

# Connect to database
engine = create_db_connection()

# Read available symbols
metadata_df = read_symbol_metadata(engine)

# Fetch specific symbol-timeframe data
df = fetch_market_data(engine, 'btcusdt_m5_crypto_ohlcv', 'BTCUSDT')
```

### DataFrame Structure

When loaded into pandas, the data has these columns:

```python
df.columns
# Index(['timestamp', 'open', 'high', 'low', 'close', 'volume', 'day_of_week'], dtype='object')

df.dtypes
# timestamp      datetime64[ns, UTC]
# open           float64
# high           float64
# low            float64
# close          float64
# volume         float64
# day_of_week    object (string)
```

---

## Multi-Timeframe Alignment

When using multiple timeframes in backtesting, the data aligner creates a merged DataFrame:

### Base Timeframe (e.g., 5m)
```
timestamp, open, high, low, close, volume, day_of_week
```

### Higher Timeframe (e.g., 1h) - Prefixed
```
timestamp, 1h_open, 1h_high, 1h_low, 1h_close, 1h_volume, 1h_day_of_week
```

### Merged DataFrame
```python
# Columns after alignment:
['timestamp', 'open', 'high', 'low', 'close', 'volume', 'day_of_week',
 '1h_open', '1h_high', '1h_low', '1h_close', '1h_volume', '1h_day_of_week']
```

**Important**: The base timeframe columns are unprefixed. Higher timeframe columns are prefixed with `{timeframe}_`.

---

## Day of Week Column

### Purpose
Pre-calculated day names for efficient filtering without timestamp parsing.

### Values
- `Monday`
- `Tuesday`
- `Wednesday`
- `Thursday`
- `Friday`
- `Saturday`
- `Sunday`

### Usage in Strategies

```python
# Filter data by day
df[df['day_of_week'] == 'Friday']

# Check if current bar is on specific days
if row['day_of_week'] in ['Monday', 'Friday']:
    # Take trade
    pass
```

### Time/Day Filters in Backtesting

The backtesting engine uses this column directly:

```python
# In strategy.py
def is_trading_time_allowed(self, data: pd.DataFrame, timestamp: datetime) -> bool:
    if self.allowed_days is not None:
        current_row = data[data['timestamp'] == timestamp]
        day_name = current_row.iloc[0].get('day_of_week')
        if day_name not in self.allowed_days:
            return False
    return True
```

**Benefit**: No need to calculate `timestamp.weekday()` or convert to day names - already available!

---

## Index and Performance

### Recommended Indexes

```sql
-- Primary index on timestamp for fast time-range queries
CREATE INDEX idx_{table_name}_timestamp ON {table_name} (timestamp);

-- Composite index for day filtering
CREATE INDEX idx_{table_name}_day_timestamp ON {table_name} (day_of_week, timestamp);
```

### Query Optimization

- Use `timestamp` for range filters (automatically uses index)
- Use `day_of_week` for day filtering (pre-calculated, no function overhead)
- Combine both for optimal performance on time-restricted backtests

---

## Connection Details

Database connection uses SSL certificate authentication:

```python
# In .env file
DATABASE_URL=postgresql://username:password@host:port/database
SSL_CERT_PATH=./certs/ca-certificate.crt
```

Connection is established via `src/database.py`:
```python
from src.database import create_db_connection
engine = create_db_connection()
```

---

## Summary

- **OHLCV Tables**: One per symbol-timeframe, named `{symbol}_{tf}_{type}_ohlcv`
- **Metadata Table**: Maps symbols to their data tables
- **Day Column**: Pre-calculated `day_of_week` TEXT column (Monday-Sunday)
- **Timestamps**: All in UTC with timezone awareness
- **Precision**: 8 decimal places for prices
- **Timeframes**: Embedded in table name, not as column
