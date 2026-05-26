"""
ENGINE 5 — LIGHTWEIGHT MEMORY ENGINE
Tracks used topic combinations to prevent repetition.
Each posted combination gets a permanent ID — never repeats.
Also tracks recent categories, angles, and formats for rotation.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import utils.logger as logger
from utils.file_store import read_json, write_json

ENGINE = "MemoryEngine"

_BASE       = Path(__file__).resolve().parent.parent.parent
_MEMORY_DIR = _BASE / "engines" / "memory"
_MEMORY_DIR.mkdir(parents=True, exist_ok=True)

USED_COMBINATIONS_FILE = _MEMORY_DIR / "used_combinations.json"
RECENT_HISTORY_FILE    = _MEMORY_DIR / "recent_history.json"

# How many recent items to track per field (for rotation logic)
RECENT_WINDOW = 10


# ─── Combination ID ────────────────────────────────────────────────────────────

def _make_combination_id(category: str, subtopic: str, angle: str, post_type: str) -> str:
    """
    Generate a unique permanent ID for a topic combination.
    Format: USED_CATEGORY_SUBTOPIC_ANGLE_POSTTYPE
    All uppercased, spaces replaced with hyphens, fields separated by underscores.
    """
    def clean(s: str) -> str:
        return s.upper().replace(" ", "-").replace("_", "-")

    return f"USED_{clean(category)}_{clean(subtopic)}_{clean(angle)}_{clean(post_type)}"


def combination_exists(category: str, subtopic: str, angle: str, post_type: str) -> bool:
    """Return True if this exact combination has been used before."""
    combo_id = _make_combination_id(category, subtopic, angle, post_type)
    used = _load_used_combinations()
    return combo_id in used


def record_combination(category: str, subtopic: str, angle: str, post_type: str):
    """Permanently record a used combination. Called after post is published."""
    combo_id = _make_combination_id(category, subtopic, angle, post_type)
    used     = _load_used_combinations()

    if combo_id not in used:
        used[combo_id] = {
            "category":  category,
            "subtopic":  subtopic,
            "angle":     angle,
            "post_type": post_type,
            "recorded_at": datetime.now(timezone.utc).isoformat()
        }
        write_json(USED_COMBINATIONS_FILE, used)
        logger.info(ENGINE, f"Combination recorded: {combo_id}")
    else:
        logger.warning(ENGINE, f"Combination already existed: {combo_id}")


def _load_used_combinations() -> dict:
    data = read_json(USED_COMBINATIONS_FILE)
    if data is None:
        return {}
    return data


# ─── Recent History (for rotation) ────────────────────────────────────────────

def get_recent(field: str) -> list:
    """Get recent values for a field: 'category', 'angle', 'post_type', 'hook_style'."""
    history = _load_recent_history()
    return history.get(field, [])


def update_recent(field: str, value: str):
    """Add a value to the recent history for a field."""
    history = _load_recent_history()
    if field not in history:
        history[field] = []
    history[field].append(value)
    # Keep only the last N items
    history[field] = history[field][-RECENT_WINDOW:]
    write_json(RECENT_HISTORY_FILE, history)


def _load_recent_history() -> dict:
    data = read_json(RECENT_HISTORY_FILE)
    if data is None:
        return {}
    return data


# ─── Stats ────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    used    = _load_used_combinations()
    history = _load_recent_history()
    return {
        "total_combinations_used": len(used),
        "recent_categories": history.get("category", []),
        "recent_angles":     history.get("angle", []),
        "recent_post_types": history.get("post_type", [])
    }
