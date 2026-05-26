"""
utils/logger.py
Shared structured logger for all Algocare engines.
Every engine imports and uses this — never print() directly.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_LOGS_DIR = Path(__file__).resolve().parent.parent / "logs"
_LOGS_DIR.mkdir(parents=True, exist_ok=True)
_LOG_FILE = _LOGS_DIR / "algocare.log"

LEVELS = {"DEBUG": 0, "INFO": 1, "WARNING": 2, "ERROR": 3}


def _write(level: str, engine: str, message: str, data: dict = None):
    entry = {
        "ts":      datetime.now(timezone.utc).isoformat(),
        "level":   level,
        "engine":  engine,
        "message": message,
    }
    if data:
        entry["data"] = data

    line = json.dumps(entry, ensure_ascii=False)
    print(line, flush=True)

    try:
        with open(_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception as e:
        print(f"[LOGGER] Could not write to log file: {e}", file=sys.stderr)

    if LEVELS.get(level, 0) >= LEVELS["WARNING"]:
        _send_telegram(level, engine, message)


def _send_telegram(level: str, engine: str, message: str):
    try:
        from utils.telegram_alert import send_alert
        send_alert(f"[{level}] {engine}: {message}")
    except Exception:
        pass


def debug(engine: str, message: str, data: dict = None):
    _write("DEBUG", engine, message, data)

def info(engine: str, message: str, data: dict = None):
    _write("INFO", engine, message, data)

def warning(engine: str, message: str, data: dict = None):
    _write("WARNING", engine, message, data)

def error(engine: str, message: str, data: dict = None):
    _write("ERROR", engine, message, data)
