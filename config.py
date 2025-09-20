import os

DATABASE_URL = os.getenv('DATABASE_URL', '')
DATABASE_CA_CERT_PATH = os.getenv('DATABASE_CA_CERT_PATH', 'certs/ca-certificate.crt')