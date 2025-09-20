import ssl
from sqlalchemy import create_engine
from config import DATABASE_URL, DATABASE_CA_CERT_PATH

def create_db_connection():
    """Create database connection with SSL certificate"""
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_REQUIRED
    ssl_context.load_verify_locations(DATABASE_CA_CERT_PATH)

    engine = create_engine(
        DATABASE_URL,
        connect_args={
            "sslmode": "require",
            "sslcert": None,
            "sslkey": None,
            "sslrootcert": DATABASE_CA_CERT_PATH
        }
    )
    return engine