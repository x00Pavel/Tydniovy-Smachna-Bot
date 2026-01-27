import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "./credentials.json")
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID")
TIMEZONE = os.getenv("TIMEZONE", "UTC")
DATABASE_PATH = os.getenv("DATABASE_PATH", "./meals.db")
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# Webhook configuration (optional - if not set, falls back to polling)
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., "https://example.com"
WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET")  # Optional secret token for webhook security

# Validate required variables
if not TELEGRAM_BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN not set in environment variables")
if not GOOGLE_SHEET_ID:
    raise ValueError("GOOGLE_SHEET_ID not set in environment variables")
if not Path(GOOGLE_CREDENTIALS_PATH).exists():
    raise ValueError(f"Google credentials file not found at {GOOGLE_CREDENTIALS_PATH}")
