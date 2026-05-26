"""
ENGINE 6 — VISUAL IDENTITY ENGINE
Defines the visual language for each post.
Locked style: Minimal Medical Doodle.
Phase 1: outputs visual metadata injected into image prompts (future use).
Phase 2: actual image generation.
"""

import random
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import utils.logger as logger

ENGINE = "VisualIdentityEngine"

# ─── Locked Visual Identity ───────────────────────────────────────────────────
# These never change. This is the brand's visual DNA.

BRAND_STYLE = {
    "art_style":       "minimal_medical_sketch",
    "line_quality":    "thin_clean_lines",
    "background":      "white_clean",
    "detail_level":    "low",
    "character_style": "simple_cartoon",
    "text_overlay":    False,
    "color_palette":   ["white", "soft_blue", "teal", "soft_green"],
    "visual_density":  "low",
    "brand_name":      "Asiya"
}

# ─── Composition Options ──────────────────────────────────────────────────────

COMPOSITIONS = {
    "high":   ["center_closeup", "isolated_object", "simple_scene"],
    "medium": ["centered_object", "minimal_layout"],
    "low":    ["icon_only", "minimal_symbol"]
}

# ─── Color Mood Map ───────────────────────────────────────────────────────────

EMOTION_COLOR_MAP = {
    "Calm curiosity":       "soft_blue",
    "Quiet surprise":       "soft_teal",
    "Light concern":        "soft_amber",
    "Tiny fascination":     "soft_blue",
    "Gentle correction":    "soft_green",
    "Relaxed explanation":  "soft_blue",
    "Casual observation":   "soft_teal",
}

# ─── Category Subject Map ────────────────────────────────────────────────────
# Maps categories to visual subject focus for image prompts

CATEGORY_VISUAL_FOCUS = {
    "hands":           "hands and fingers",
    "skin":            "skin surface texture",
    "teeth":           "teeth and mouth area",
    "eyes":            "eyes and eyelids",
    "posture":         "body posture silhouette",
    "bathing":         "shower or bathroom setting",
    "feet":            "feet and toes",
    "hair":            "hair and scalp",
    "hydration":       "water glass or water droplets",
    "water":           "water droplets or glass",
    "breathing":       "lungs or breath visualization",
    "sleep":           "sleeping figure or pillow",
    "digestion":       "stomach or digestive area",
    "stomach":         "stomach area",
    "exercise":        "active body figure",
    "walking":         "feet and legs walking",
    "stress":          "head or brain with tension lines",
    "phones":          "hand holding phone",
    "food_hygiene":    "kitchen or food items",
    "sweat":           "skin with sweat droplets",
    "heat":            "sun or heat waves",
    "cold_weather":    "cold weather symbols or cracked skin",
    "hygiene":         "cleaning or hygiene items",
    "nails":           "close-up of fingernails",
    "ears":            "ear close-up",
    "nose":            "nose area",
    "lips":            "lips close-up",
    "tongue":          "mouth and tongue",
    "back":            "back and spine silhouette",
    "neck":            "neck and shoulder area",
    "brain":           "brain outline or head",
    "heart":           "heart outline",
    "blood_sugar":     "blood sugar graph or food items",
    "immune_system":   "shield or cell outline",
    "sun_exposure":    "skin under sun rays",
    "indoor_living":   "indoor room setting",
    "sitting":         "seated figure",
    "standing":        "standing figure",
    "eating_habits":   "plate and fork",
    "morning_habits":  "morning setting with sunlight",
    "night_habits":    "night scene with phone or pillow",
    "bathroom_habits": "bathroom setting",
    "kitchen_health":  "kitchen and food prep area",
    "muscles":         "muscle outline or arm",
    "joints":          "joint close-up",
    "headaches":       "head with tension lines",
    "fatigue":         "tired figure or drooping eyes",
    "air_quality":     "air particles or dust",
    "clothing_health": "clothing fabric or outfit",
    "everyday_body_reactions": "simple body silhouette",
    "bathroom_germs":  "bathroom with germ symbols",
    "screens_health":  "screen with eyes",
    "mouth_breath":    "mouth and breath cloud",
    "daily_energy":    "energy meter or figure",
    "small_hygiene_mistakes": "hygiene items"
}


# ─── Main Engine ──────────────────────────────────────────────────────────────

def build_visual_identity(strategy_object: dict) -> dict:
    """
    Receives strategy object from Engine 2.
    Returns visual identity object for Engine 3 image prompt building.
    """
    if not strategy_object:
        logger.error(ENGINE, "Received empty strategy object")
        return {}

    category      = strategy_object.get("category", "")
    subtopic      = strategy_object.get("subtopic", "")
    emotion       = strategy_object.get("emotion", "Calm curiosity")
    visual_weight = strategy_object.get("visual_weight", "medium")
    visual_hint   = strategy_object.get("visual_hint", "")

    # Select composition based on visual weight
    composition_options = COMPOSITIONS.get(visual_weight, COMPOSITIONS["medium"])
    composition         = random.choice(composition_options)

    # Select color accent based on emotion
    color_accent = EMOTION_COLOR_MAP.get(emotion, "soft_blue")

    # Get visual subject focus
    visual_subject = CATEGORY_VISUAL_FOCUS.get(category, subtopic)

    visual_object = {
        "topic_id":        strategy_object.get("topic_id"),
        "art_style":       BRAND_STYLE["art_style"],
        "line_quality":    BRAND_STYLE["line_quality"],
        "background":      BRAND_STYLE["background"],
        "color_accent":    color_accent,
        "color_palette":   BRAND_STYLE["color_palette"],
        "composition":     composition,
        "detail_level":    BRAND_STYLE["detail_level"],
        "character_style": BRAND_STYLE["character_style"],
        "text_overlay":    BRAND_STYLE["text_overlay"],
        "visual_density":  BRAND_STYLE["visual_density"],
        "visual_subject":  visual_subject,
        "visual_hint":     visual_hint,
        "subtopic":        subtopic,
        "visual_built_at": datetime.now(timezone.utc).isoformat()
    }

    logger.info(ENGINE, f"Visual identity built: {composition} | {color_accent} | subject={visual_subject}")
    return visual_object
