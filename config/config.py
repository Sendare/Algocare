"""
Algocare / Asiya — Central Configuration
All keys, paths, and settings in one place.
"""

import os
from pathlib import Path

# ─── BASE PATHS ───────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR         = BASE_DIR / "data"
TOPICS_DIR       = DATA_DIR / "topics"
STRATEGY_DIR     = DATA_DIR / "strategy"
PROMPTS_DIR      = DATA_DIR / "prompts"
VISUAL_RULES_DIR = DATA_DIR / "visual_rules"

DRAFTS_DIR    = BASE_DIR / "drafts"
APPROVED_DIR  = BASE_DIR / "approved"
PUBLISHED_DIR = BASE_DIR / "published"
FAILED_DIR    = BASE_DIR / "failed"

LOGS_DIR          = BASE_DIR / "logs"
PUBLISH_LOGS_DIR  = BASE_DIR / "publish_logs"
WORKFLOW_LOGS_DIR = BASE_DIR / "workflow_logs"

MEMORY_DIR = BASE_DIR / "engines" / "memory"

# ─── API KEYS (set as environment variables, never hardcode) ──────────────────
GEMINI_API_KEY    = os.environ.get("GEMINI_API_KEY", "")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID", "")
FACEBOOK_PAGE_TOKEN = os.environ.get("FACEBOOK_PAGE_TOKEN", "")
FACEBOOK_PAGE_ID    = os.environ.get("FACEBOOK_PAGE_ID", "")

# ─── GEMINI SETTINGS ──────────────────────────────────────────────────────────
GEMINI_MODEL        = "gemini-2.0-flash"
GEMINI_MAX_TOKENS   = 1000
GEMINI_TEMPERATURE  = 0.85
GEMINI_MAX_RETRIES  = 3
GEMINI_RETRY_DELAY  = 10   # seconds between retries
GEMINI_RATE_LIMIT   = 15   # calls per minute (free tier)

# ─── SYSTEM SETTINGS ─────────────────────────────────────────────────────────
POSTS_PER_DAY_MIN   = 3
POSTS_PER_DAY_MAX   = 5
SAFE_MODE_THRESHOLD = 5    # consecutive failures before safe mode activates
MAX_PUBLISH_RETRIES = 3
PUBLISH_RETRY_DELAY = 30   # seconds

# ─── DRAFT SETTINGS ───────────────────────────────────────────────────────────
DRAFT_STATUS_DRAFT    = "draft"
DRAFT_STATUS_APPROVED = "approved"
DRAFT_STATUS_PUBLISHED = "published"
DRAFT_STATUS_FAILED   = "failed"

# ─── FACEBOOK SETTINGS ────────────────────────────────────────────────────────
FACEBOOK_API_VERSION = "v19.0"
FACEBOOK_BASE_URL    = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}"
