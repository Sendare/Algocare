"""
ENGINE 1 — TOPIC INTELLIGENCE ENGINE
Selects a unique, high-quality topic combination and returns a structured topic object.
Flow: Load databases → Select category → Select subtopic → Select angle →
      Select post type → Select hook/emotion → Check memory → Score → Return object.
"""

import random
import hashlib
from datetime import datetime, timezone
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import utils.logger as logger
from utils.file_store import read_json
from engines.memory.memory_engine import (
    combination_exists, get_recent
)

ENGINE = "TopicIntelligenceEngine"

_BASE      = Path(__file__).resolve().parent.parent.parent
_DATA_DIR  = _BASE / "data" / "topics"

MAX_ATTEMPTS = 50  # max tries before giving up on finding unique combo


# ─── Data Loaders ─────────────────────────────────────────────────────────────

def _load_topics() -> dict:
    data = read_json(_DATA_DIR / "topics.json")
    if not data:
        logger.error(ENGINE, "topics.json missing or empty")
        return {}
    return data


def _load_angles() -> dict:
    data = read_json(_DATA_DIR / "angles.json")
    if not data:
        logger.error(ENGINE, "angles.json missing or empty")
        return {}
    return data


def _load_post_types() -> list:
    data = read_json(_DATA_DIR / "post_types.json")
    if not data:
        logger.error(ENGINE, "post_types.json missing or empty")
        return []
    return data.get("post_types", [])


# ─── Sub-engines ──────────────────────────────────────────────────────────────

def _select_category(topics: dict, recent_categories: list) -> str:
    """
    Choose a category, deprioritizing recently used ones.
    Uses weighted random: recent categories get weight 1, others get weight 3.
    """
    all_categories = list(topics.keys())
    recent_set     = set(recent_categories[-5:])  # last 5 categories

    weights = [1 if cat in recent_set else 3 for cat in all_categories]
    chosen  = random.choices(all_categories, weights=weights, k=1)[0]
    return chosen


def _select_subtopic(topics: dict, category: str) -> str:
    """Pick a random subtopic from the selected category."""
    subtopics = topics.get(category, [])
    if not subtopics:
        logger.error(ENGINE, f"No subtopics found for category: {category}")
        return ""
    return random.choice(subtopics)


def _select_angle(angles: list, recent_angles: list) -> str:
    """Choose psychological angle, deprioritizing recently used ones."""
    recent_set = set(recent_angles[-4:])
    weights    = [1 if a in recent_set else 3 for a in angles]
    return random.choices(angles, weights=weights, k=1)[0]


def _select_post_type(post_types: list, recent_types: list) -> str:
    """Choose post type, deprioritizing recently used ones."""
    recent_set = set(recent_types[-4:])
    weights    = [1 if t in recent_set else 3 for t in post_types]
    return random.choices(post_types, weights=weights, k=1)[0]


def _select_emotion(emotional_modes: list) -> str:
    return random.choice(emotional_modes)


def _select_hook(hook_styles: list) -> str:
    return random.choice(hook_styles)


def _generate_visual_hint(category: str, subtopic: str) -> str:
    """Generate a simple visual hint string. Used later for image prompts."""
    return f"{subtopic} related to {category.replace('_', ' ')}"


def _score_topic(category: str, subtopic: str, angle: str, post_type: str,
                 recent_categories: list, recent_angles: list) -> int:
    """
    Score 0-100 based on:
    - Freshness (40pts): how recently category/angle were used
    - Angle strength (30pts): some angles drive more engagement
    - Visual potential (20pts): how visualizable the topic is
    - Format fit (10pts): static scoring per post type
    """
    score = 0

    # Freshness (40pts)
    cat_recency   = recent_categories[-8:] if recent_categories else []
    angle_recency = recent_angles[-6:] if recent_angles else []

    if category not in cat_recency:
        score += 25
    elif cat_recency[-1] != category:
        score += 15
    else:
        score += 5

    if angle not in angle_recency:
        score += 15
    else:
        score += 5

    # Angle strength (30pts) — higher engagement angles score more
    high_engagement_angles = {
        "Curiosity", "Surprise", "Hidden Truth", "Contradiction",
        "Realization", "False Confidence"
    }
    medium_engagement_angles = {
        "Relatability", "Self-Recognition", "Familiar Experience",
        "Overlooked Detail", "Mild Concern"
    }
    if angle in high_engagement_angles:
        score += 30
    elif angle in medium_engagement_angles:
        score += 20
    else:
        score += 10

    # Visual potential (20pts)
    high_visual = {
        "hands", "skin", "teeth", "eyes", "posture", "bathing",
        "feet", "hair", "hydration", "water", "breathing"
    }
    medium_visual = {
        "sleep", "digestion", "stomach", "exercise", "walking",
        "eating_habits", "morning_habits", "night_habits"
    }
    if category in high_visual:
        score += 20
    elif category in medium_visual:
        score += 13
    else:
        score += 7

    # Format fit (10pts)
    strong_formats = {"Question", "Body Reaction", "Myth vs Reality", "Quick Fact"}
    if post_type in strong_formats:
        score += 10
    else:
        score += 6

    return min(score, 100)


def _generate_topic_id(category: str, subtopic: str) -> str:
    """Generate a short readable topic ID."""
    raw  = f"{category}_{subtopic}"
    hash_part = hashlib.md5(raw.encode()).hexdigest()[:6].upper()
    cat_code  = category[:3].upper()
    return f"{cat_code}_{hash_part}"


# ─── Main Engine ──────────────────────────────────────────────────────────────

def generate_topic() -> dict:
    """
    Main entry point. Returns a structured topic object ready for Engine 2.
    Tries up to MAX_ATTEMPTS to find a unique combination.
    """
    topics     = _load_topics()
    angle_data = _load_angles()
    post_types = _load_post_types()

    if not topics or not angle_data or not post_types:
        logger.error(ENGINE, "Cannot generate topic — data files missing")
        return {}

    angles         = angle_data.get("psychological_angles", [])
    emotional_modes = angle_data.get("emotional_modes", [])
    hook_styles    = angle_data.get("hook_styles", [])

    recent_categories = get_recent("category")
    recent_angles     = get_recent("angle")
    recent_post_types = get_recent("post_type")

    for attempt in range(1, MAX_ATTEMPTS + 1):
        category  = _select_category(topics, recent_categories)
        subtopic  = _select_subtopic(topics, category)
        angle     = _select_angle(angles, recent_angles)
        post_type = _select_post_type(post_types, recent_post_types)

        if not subtopic:
            continue

        if combination_exists(category, subtopic, angle, post_type):
            logger.debug(ENGINE, f"Combination exists, retrying (attempt {attempt})")
            continue

        # Found a unique combination
        emotion      = _select_emotion(emotional_modes)
        hook         = _select_hook(hook_styles)
        visual_hint  = _generate_visual_hint(category, subtopic)
        priority     = _score_topic(category, subtopic, angle, post_type,
                                    recent_categories, recent_angles)
        topic_id     = _generate_topic_id(category, subtopic)

        topic_object = {
            "topic_id":     topic_id,
            "category":     category,
            "subtopic":     subtopic,
            "angle":        angle,
            "emotion":      emotion,
            "hook_style":   hook,
            "post_type":    post_type,
            "visual_hint":  visual_hint,
            "priority_score": priority,
            "generated_at": datetime.now(timezone.utc).isoformat()
        }

        logger.info(ENGINE, f"Topic generated: [{category}] {subtopic} | {angle} | {post_type} | score={priority}")
        return topic_object

    logger.error(ENGINE, f"Could not find unique combination after {MAX_ATTEMPTS} attempts")
    return {}
