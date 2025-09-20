import pandas as pd

def read_symbol_metadata(engine):
    """Read symbol metadata to get information about available tables"""
    print("Reading symbol metadata...")
    query = "SELECT * FROM symbol_metadata"
    metadata_df = pd.read_sql(query, engine)
    print(f"Found {len(metadata_df)} symbols in metadata")
    print("\nMetadata preview:")
    print(metadata_df.head(10))
    return metadata_df

def fetch_market_data(engine, table_name, symbol):
    """Fetch market data for a specific table"""
    print(f"\nFetching data for {symbol} from table: {table_name}")
    query = f"SELECT * FROM {table_name} ORDER BY timestamp"
    df = pd.read_sql(query, engine)
    print(f"Loaded {len(df)} records")

    print(f"\nFirst 10 rows of {symbol}:")
    print(df.head(10))

    print(f"\nLast 10 rows of {symbol}:")
    print(df.tail(10))

    return df

def fetch_all_market_data(engine, metadata_df):
    """Fetch all market data tables based on metadata"""
    market_data = {}

    for _, row in metadata_df.iterrows():
        symbol = row['symbol']
        table_name = row['table_name']

        try:
            df = fetch_market_data(engine, table_name, symbol)
            market_data[table_name] = df
            print(f"✓ Successfully loaded {symbol}")
        except Exception as e:
            print(f"✗ Error loading {symbol}: {str(e)}")

    print(f"\nSummary: Successfully loaded {len(market_data)} out of {len(metadata_df)} tables")
    return market_data