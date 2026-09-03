import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

STATIC_DIR = BASE_DIR / "static"
DATA_DIR = Path(
    os.getenv("DATA_DIR", str(BASE_DIR / "data"))
)
DB_PATH = Path(
    os.getenv(
        "DATABASE_PATH",
        str(DATA_DIR / "invoice_ledger.db")
    )
)

DIFY_API_BASE_URL = os.getenv(
    "DIFY_API_BASE_URL",
    ""
).rstrip("/")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")
DIFY_ORDER_API_KEY = os.getenv(
    "DIFY_ORDER_API_KEY",
    ""
)
DIFY_USER = os.getenv(
    "DIFY_USER",
    "invoice-ledger-local"
)

DINGTALK_WEBHOOK = os.getenv(
    "DINGTALK_WEBHOOK",
    ""
).strip()
DINGTALK_SECRET = os.getenv(
    "DINGTALK_SECRET",
    ""
).strip()

APP_USERNAME = os.getenv("APP_USERNAME", "").strip()
APP_PASSWORD = os.getenv("APP_PASSWORD", "")
APP_SESSION_SECRET = os.getenv(
    "APP_SESSION_SECRET",
    ""
)
APP_SESSION_HOURS = max(
    1,
    int(os.getenv("APP_SESSION_HOURS", "12"))
)
APP_COOKIE_SECURE = (
    os.getenv("APP_COOKIE_SECURE", "false").lower()
    == "true"
)
SESSION_COOKIE_NAME = "ledger_session"

REMINDER_HOUR = int(os.getenv("REMINDER_HOUR", "9"))
REMINDER_MINUTE = int(os.getenv("REMINDER_MINUTE", "0"))
REMINDER_JOB_ID = "daily-dingtalk-reminder"
ENABLE_SCHEDULER = (
    os.getenv("ENABLE_SCHEDULER", "true").lower()
    == "true"
)
