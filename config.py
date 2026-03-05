"""
config.py — All settings for Social Team AI Agent
==================================================
Fill in your values below, then deploy.
"""

import os

# ── Telegram ─────────────────────────────────────────────
# Get from @BotFather → /newbot
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# Your personal Telegram Chat ID — get from @userinfobot
MANAGER_CHAT_ID = int(os.getenv("MANAGER_CHAT_ID", "0"))

# Team Telegram group chat ID (negative number) — optional
# Add your bot to the group, then get the ID from @userinfobot
TEAM_GROUP_ID = os.getenv("TEAM_GROUP_ID", "")

# Team member Chat IDs (for individual reminders) — optional
# Each person messages @userinfobot to get their ID
TEAM_CHAT_IDS = {
    "Ana Lima":   os.getenv("CHAT_ID_ANA", ""),
    "Raj Kumar":  os.getenv("CHAT_ID_RAJ", ""),
    "Mia Nguyen": os.getenv("CHAT_ID_MIA", ""),
    "Jun Chen":   os.getenv("CHAT_ID_JUN", ""),
}

# ── Claude API ───────────────────────────────────────────
# Get from console.anthropic.com → API Keys
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "YOUR_CLAUDE_API_KEY_HERE")
CLAUDE_MODEL   = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 1000

# ── Google Sheets ────────────────────────────────────────
# Sheet ID is the long string in the URL:
# docs.google.com/spreadsheets/d/[SHEET_ID]/edit
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "YOUR_SHEET_ID_HERE")

# Service Account JSON key (from Google Cloud Console)
# Either set the path to the file OR paste the JSON as env var
GOOGLE_SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")  # JSON string (for Railway)

# ── Schedule ─────────────────────────────────────────────
DAILY_BRIEF_HOUR = int(os.getenv("DAILY_BRIEF_HOUR", "9"))  # 24h format
TIMEZONE = os.getenv("TIMEZONE", "Asia/Kuala_Lumpur")

# ── KPI Thresholds ───────────────────────────────────────
KPI_CRITICAL_BELOW = float(os.getenv("KPI_CRITICAL_BELOW", "0.50"))  # Below 50% = critical
KPI_WARNING_BELOW  = float(os.getenv("KPI_WARNING_BELOW",  "0.70"))  # Below 70% = warning

# ── Team Context ─────────────────────────────────────────
TEAM_MEMBERS = {
    "Ana Lima":   "Facebook & Instagram manager",
    "Raj Kumar":  "TikTok & YouTube specialist",
    "Mia Nguyen": "Telegram & WhatsApp community manager",
    "Jun Chen":   "Twitter/X & data analytics",
}

PLATFORMS = ["Facebook", "Instagram", "Telegram", "WhatsApp", "TikTok", "YouTube", "Twitter/X"]
