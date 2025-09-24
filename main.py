from src.database import create_db_connection
from src.data_fetcher import read_symbol_metadata, fetch_all_market_data

def main():
    """Main function to orchestrate data fetching"""
    try:
        # Establish database connection with SSL certificate
        engine = create_db_connection()
        print("Database connection established successfully")
        # Read symbol metadata to discover available market data tables
        metadata_df = read_symbol_metadata(engine)
        # Fetch all market data tables based on metadata information
        market_data = fetch_all_market_data(engine, metadata_df)

        return market_data, metadata_df

    except Exception as e:
        print(f"Error: {str(e)}")
        return None, None

if __name__ == "__main__":
    market_data, metadata = main()