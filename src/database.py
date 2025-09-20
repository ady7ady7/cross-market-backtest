import ssl
from sqlalchemy import create_engine
from config import DATABASE_URL, DATABASE_CA_CERT_PATH

def create_db_connection():
    """Create database connection with SSL certificate"""

    # Debug: Check if URL is provided
    if not DATABASE_URL:
        raise ValueError("DATABASE_URL environment variable is not set")

    # Debug: Show URL format (hide password for security)
    masked_url = DATABASE_URL
    if '@' in masked_url:
        parts = masked_url.split('@')
        if ':' in parts[0]:
            user_pass = parts[0].split(':')
            if len(user_pass) > 1:
                masked_url = f"{user_pass[0]}:***@{parts[1]}"
    print(f"Connecting with URL format: {masked_url}")

    # Convert common URL formats to SQLAlchemy format
    url = DATABASE_URL
    if url.startswith('postgres://'):
        url = url.replace('postgres://', 'postgresql://', 1)
        print("Converted postgres:// to postgresql://")

    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.load_verify_locations(DATABASE_CA_CERT_PATH)

    try:
        engine = create_engine(
            url,
            connect_args={
                "sslmode": "require",
                "sslcert": None,
                "sslkey": None,
                "sslrootcert": DATABASE_CA_CERT_PATH
            }
        )
        return engine
    except Exception as e:
        print(f"SQLAlchemy URL parsing failed: {str(e)}")
        print(f"URL format being used: {url.split('@')[0]}@***")
        raise