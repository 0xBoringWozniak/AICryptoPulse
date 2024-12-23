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
