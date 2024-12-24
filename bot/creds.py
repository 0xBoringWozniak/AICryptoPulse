import os

FASTAPI_BASE_URL = os.getenv("FASTAPI_BASE_URL", "http://api:8000") # default value is for docker-compose

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("Please set the TELEGRAM_BOT_TOKEN environment variable")
