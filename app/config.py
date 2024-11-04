# app/config.py

import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Feature toggles
INVITE_CODE_ENABLED = os.getenv("INVITE_CODE_ENABLED", "false").lower() == "true"
INVITE_CODE = os.getenv("INVITE_CODE", "default-invite-code")
REGISTRATION_ENABLED = os.getenv("REGISTRATION_ENABLED", "true").lower() == "true"
EMAIL_AUTH_ENABLED = os.getenv("EMAIL_AUTH_ENABLED", "false").lower() == "true"
USERS_PER_PAGE = int(os.getenv("USERS_PER_PAGE", "10"))
DASHBOARD_TEXT = os.getenv("DASHBOARD_TEXT", "This is the admin dashboard.")
# Database settings
DB_URL = os.getenv("DB_URL", "sqlite://db.sqlite3")
