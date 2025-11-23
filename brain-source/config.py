"""
Phase D Configuration
Secure settings for Email, Calendar, and Prompt Engine integration
"""
from pathlib import Path

# Token storage directory (git-ignored)
TOKEN_DIR = Path.home() / ".jarvis_tokens"
TOKEN_DIR.mkdir(exist_ok=True, mode=0o700)

# Google API Scopes
SCOPES_GMAIL = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.modify'
]

SCOPES_CALENDAR = [
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/calendar.events'
]

# Timezone
TIMEZONE_DEFAULT = "Europe/London"

# Token file paths
GMAIL_TOKEN_FILE = TOKEN_DIR / "gmail_token.json"
CALENDAR_TOKEN_FILE = TOKEN_DIR / "calendar_token.json"
CREDENTIALS_FILE = TOKEN_DIR / "credentials.json"

# Prompt Engine Settings
MAX_PROMPT_TOKENS = 8000
MODEL_OUTPUT_RESERVE = 4000
EMAIL_SNIPPET_MAX_LENGTH = 300

# Logging
ENABLE_DEBUG_LOGGING = False
MASK_SENSITIVE_DATA = True
