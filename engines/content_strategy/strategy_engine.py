"""
ENGINE 2 — CONTENT STRATEGY ENGINE
Converts a topic object from Engine 1 into a content strategy blueprint.
Decides: how to present, what hook pattern, caption length, CTA, visual weight, rhythm.
Never writes text — only strategic instructions.
"""

import random
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import utils.logger as logger
from engines.memory.memory_engine import get_recent

ENGINE = "ContentStrategyEngine"


# ─── Rhythm Rules ─────────────────────────────────────────────────────────────
# Controls content pacing. After certain post types, a follow-up makes sense.

FOLLOWUP_MAP = {
    "Question":        {"needs_followup": True,  "followup_type": "Answer Reveal"},
    "Myth vs Reality": {"needs_followup": False, "followup_type": None},
    "Quick Fact":      {"needs_followup": False, "followup_type": None},
    "Body Reaction":   {"needs_followup": False, "followup_type": None},
    "Mini Steps":      {"needs_followup": False, "followup_type": None},
    "Tiny Warning":    {"needs_followup": False, "followup_type": None},
    "Small Mistake":   {"needs_followup": True,  "followup_type": "Simple Explanation"},
    "Hidden Cause":    {"needs_followup": True,  "followup_type": "Simple Explanation"},
    "Comparison":      {"needs_followup": False, "followup_type": None},
    "Habit Check":     {"needs_followup": False, "followup_type": None},
    "Everyday Observation": {"needs_followup": False, "followup_type": None},
    "Simple Explanation":   {"needs_followup": False, "followup_type": None},
    "This or That":    {"needs_followup": False, "followup_type": None},
    "Tiny Reminder":   {"needs_followup": False, "followup_type": None},
    "Answer Reveal":   {"needs_followup": False, "followup_type": None},
}


# ─── Caption Length Rules ─────────────────────────────────────────────────────

def _decide_caption_length(post_type: str, angle: str) -> str:
    """
    ultra_short = 1 line | short = 2 lines | medium = 3-4 lines
    """
    ultra_short_types  = {"Tiny Reminder", "Quick Fact", "Tiny Warning"}
    medium_types       = {"Mini Steps", "Myth vs Reality", "Comparison", "Simple Explanation"}
    high_detail_angles = {"Hidden Truth", "Contradiction", "Realization"}

    if post_type in ultra_short_types:
        return "ultra_short"
    if post_type in medium_types or angle in high_detail_angles:
        return "medium"
    return "short"


# ─── Hook Pattern Rules ───────────────────────────────────────────────────────

def _decide_hook_pattern(angle: str, hook_style: str) -> str:
    """Map psychological angle + hook style to a specific hook pattern."""
    angle_hook_map = {
        "Curiosity":          "open_loop",
        "Surprise":           "unexpected_truth",
        "Hidden Truth":       "hidden_reveal",
        "Contradiction":      "assumption_flip",
        "False Confidence":   "assumption_flip",
        "Realization":        "quiet_realization",
        "Relatability":       "familiar_moment",
        "Self-Recognition":   "familiar_moment",
        "Familiar Experience":"familiar_moment",
        "Overlooked Detail":  "quiet_observation",
        "Mild Concern":       "gentle_alert",
        "Tiny Discomfort":    "gentle_alert",
        "Satisfaction":       "positive_nudge",
        "Simplicity":         "clear_simple",
        "Pattern Recognition":"pattern_reveal",
    }
    return angle_hook_map.get(angle, "open_loop")


# ─── CTA Rules ────────────────────────────────────────────────────────────────

def _decide_cta(post_type: str, recent_ctas: list) -> str:
    """
    Choose CTA type. Rotate to avoid every post asking the same thing.
    Options: ask_question | save_this | no_cta | curiosity_continuation
    Heavy bias toward no_cta and ask_question — no spammy CTAs.
    """
    cta_options_by_type = {
        "Question":        ["no_cta", "ask_question"],
        "Answer Reveal":   ["no_cta", "save_this"],
        "Myth vs Reality": ["no_cta", "ask_question"],
        "Quick Fact":      ["no_cta", "save_this"],
        "Tiny Warning":    ["no_cta"],
        "Mini Steps":      ["save_this", "no_cta"],
        "Small Mistake":   ["no_cta", "ask_question"],
        "Body Reaction":   ["no_cta", "curiosity_continuation"],
        "Habit Check":     ["ask_question", "no_cta"],
        "Comparison":      ["no_cta", "ask_question"],
        "Everyday Observation": ["no_cta"],
        "Hidden Cause":    ["no_cta", "curiosity_continuation"],
        "Simple Explanation":   ["no_cta", "save_this"],
        "This or That":    ["ask_question", "no_cta"],
        "Tiny Reminder":   ["no_cta"],
    }
    options = cta_options_by_type.get(post_type, ["no_cta"])

    # Avoid repeating same CTA twice in a row
    if len(recent_ctas) > 0 and len(options) > 1:
        last = recent_ctas[-1]
        options = [o for o in options if o != last] or options

    return random.choice(options)


# ─── Visual Priority ──────────────────────────────────────────────────────────

def _decide_visual_weight(category: str, post_type: str) -> str:
    """Determine how visually important this post is. high | medium | low"""
    high_visual_cats = {
        "hands", "skin", "teeth", "eyes", "posture", "bathing",
        "feet", "hair", "hydration", "water", "breathing"
    }
    low_visual_types = {
        "Quick Fact", "Tiny Reminder", "Tiny Warning", "Answer Reveal"
    }
    if post_type in low_visual_types:
        return "low"
    if category in high_visual_cats:
        return "high"
    return "medium"


# ─── Content Style ────────────────────────────────────────────────────────────

def _decide_content_style(angle: str, emotion: str) -> str:
    """Label the overall content feel for prompt injection."""
    style_map = {
        "Calm curiosity":       "quiet_curiosity",
        "Quiet surprise":       "soft_reveal",
        "Light concern":        "gentle_alert",
        "Tiny fascination":     "light_wonder",
        "Gentle correction":    "calm_correction",
        "Relaxed explanation":  "simple_explain",
        "Casual observation":   "casual_observe",
    }
    return style_map.get(emotion, "quiet_curiosity")


# ─── Main Engine ──────────────────────────────────────────────────────────────

def build_strategy(topic_object: dict) -> dict:
    """
    Main entry point.
    Receives topic object from Engine 1.
    Returns strategy object for Engine 3.
    """
    if not topic_object:
        logger.error(ENGINE, "Received empty topic object")
        return {}

    category  = topic_object.get("category", "")
    subtopic  = topic_object.get("subtopic", "")
    angle     = topic_object.get("angle", "")
    emotion   = topic_object.get("emotion", "")
    hook_style = topic_object.get("hook_style", "")
    post_type = topic_object.get("post_type", "")

    recent_ctas = get_recent("cta")

    followup_info   = FOLLOWUP_MAP.get(post_type, {"needs_followup": False, "followup_type": None})
    caption_length  = _decide_caption_length(post_type, angle)
    hook_pattern    = _decide_hook_pattern(angle, hook_style)
    cta_type        = _decide_cta(post_type, recent_ctas)
    visual_weight   = _decide_visual_weight(category, post_type)
    content_style   = _decide_content_style(angle, emotion)

    strategy_object = {
        "topic_id":          topic_object.get("topic_id"),
        "category":          category,
        "subtopic":          subtopic,
        "angle":             angle,
        "emotion":           emotion,
        "hook_style":        hook_style,
        "post_type":         post_type,
        "visual_hint":       topic_object.get("visual_hint", ""),
        "priority_score":    topic_object.get("priority_score", 50),
        "content_style":     content_style,
        "hook_pattern":      hook_pattern,
        "caption_length":    caption_length,
        "cta_type":          cta_type,
        "visual_weight":     visual_weight,
        "followup_required": followup_info["needs_followup"],
        "followup_type":     followup_info["followup_type"],
        "strategy_built_at": datetime.now(timezone.utc).isoformat()
    }

    logger.info(ENGINE,
        f"Strategy built: {post_type} | {hook_pattern} | {caption_length} | cta={cta_type}")
    return strategy_object
