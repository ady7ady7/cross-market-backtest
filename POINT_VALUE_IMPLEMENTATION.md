# Point Value System Implementation

## Summary
Implemented a point value system to fix position sizing and P&L calculation issues. This normalizes all instruments to use micro contracts where **1 point ≈ $1 P&L**.

## The Problem
Previous system calculated P&L as: `(price_change) * position_size`

This caused massive position sizes and trillion-dollar P&Ls because:
- DAX prices are ~15,000-23,000
- With tight SLs (e.g., 0.1% = 15 points), position sizes became enormous
- Example: Risk $100 over 15 points = 6.67 units
- If 1 unit = 1 full contract = €25/point, this would be way too large

## The Solution
Added `point_value` to normalize contracts across all instruments:

### Position Sizing Formula
```
position_size = risk_amount / (risk_in_points * point_value)
```

### P&L Formula
```
pnl = price_change_in_points * point_value * position_size
```

### Point Values (Using Micro Contracts)
- **Crypto** (BTC, ETH): `point_value = 1.0`
  - 1 unit = 1 coin
  - 1 point move = $1 P&L per 1 coin

- **Indices** (DAX, S&P, Nasdaq): `point_value = 1.0`
  - 1 unit = 1 micro contract
  - 1 point move = ~$1 P&L per micro contract

- **Forex** (EURUSD, GBPUSD): `point_value = 0.1`
  - 1 unit = 1 micro lot (1,000 currency units)
  - 1 pip move = $0.10 P&L per micro lot

### Example: DAX Trade
```
Entry: 15,000
SL: 14,850 (150 points risk)
Account: $10,000
Risk: 1% = $100

Position sizing:
position_size = $100 / (150 points * $1/point) = 0.667 micro contracts

Price moves to 15,100 (+100 points):
pnl = 100 points * $1/point * 0.667 units = $66.70
```

## Compounding Feature
Added toggle for compounding returns:
- **OFF (default)**: Risk % of initial capital (fixed $ risk amount)
- **ON**: Risk % of current capital (grows/shrinks with account)

## Files Changed

### 1. Database Migration
- `migrations/add_point_value.sql` - SQL script to add column
- Default: 1.0 for crypto/indices
- Forex: 0.1 (micro lots)

### 2. Position Management
- `src/backtesting/position.py`:
  - Updated `PositionManager.__init__()` to accept `point_value` and `use_compounding`
  - Updated `calculate_position_size()` to use point value formula
  - Updated `Position` dataclass to store `point_value`
  - Updated `unrealized_pnl` property to use point value
  - Updated `realized_pnl` property to use point value
  - Updated `partial_close()` to use point value

### 3. Backtest Engine
- `src/backtesting/engine.py`:
  - Added `point_value` and `use_compounding` parameters to `__init__()`
  - Pass parameters to `PositionManager` initialization

### 4. UI Components
- `ui/components/backtest_config.py`:
  - Added "Compounding" checkbox next to risk input
  - Shows helpful tooltip explaining the difference

- `ui/components/analysis_section.py`:
  - Extract `point_value` from `symbol_metadata` during data loading
  - Pass `point_value` and `use_compounding` to `BacktestEngine`

## How to Apply Migration

**Option 1: Via Streamlit app**
The app will automatically use default point_value=1.0 if column doesn't exist yet. To add the column properly:

1. Access your database with a SQLite tool
2. Run the SQL from `migrations/add_point_value.sql`

**Option 2: Manual SQL**
```sql
-- Add column
ALTER TABLE symbol_metadata ADD COLUMN point_value REAL DEFAULT 1.0;

-- Set forex to 0.1
UPDATE symbol_metadata
SET point_value = 0.1
WHERE symbol LIKE '%USD%' OR symbol LIKE '%EUR%' OR symbol LIKE '%GBP%';
```

## Testing
Run a backtest on DAX with these parameters:
- Symbol: deuidxeur
- Timeframes: m5, h1
- Initial capital: $10,000
- Risk per trade: 1%
- Strategy: HTS Trend Follow

**Expected results:**
- Position sizes: 0.1-2.0 micro contracts (not millions)
- P&L per trade: $10-$200 range (not trillions)
- Drawdown: 5-20% (not 800,000%)
- Reasonable win/loss amounts

## Debug Output
Added debug logging to first 3 positions:
```
Position sizing: Risk $100.00 over 150.00 points
Point value: $1.0, Position size: 0.6667 units
Opened position #1: LONG 0.6667 units @ 15000.00
SL: 14850.00, TP: 15225.00, Risk: $100.00
```

This verifies the sizing is correct before running full backtest.
