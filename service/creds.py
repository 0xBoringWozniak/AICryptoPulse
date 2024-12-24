import os

# Mongo URI to connect in format
# mongodb://<user>:<password>@<host>:<port>
#
# from .env.example
# DB_USER=myuser
# DB_PASS=secret123
# DB_HOST=mongo_db
# DB_PORT=27017

DB_USER = os.getenv('DB_USER', 'admin')
DB_PASS = os.getenv('DB_PASS', 'secret')
DB_HOST = os.getenv('DB_HOST', 'mongo_db')  # via docker-compose network
DB_PORT = os.getenv('DB_PORT', '27017')


OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is not set")


AWS_S3_API_KEY = os.getenv('AWS_ACCESS_KEY_ID')
AWS_S3_API_SECRET = os.getenv('AWS_SECRET_ACCESS_KEY')
if not AWS_S3_API_KEY or not AWS_S3_API_SECRET:
    raise ValueError("AWS_S3_API_KEY or AWS_S3_API_SECRET environment variables are not set")
