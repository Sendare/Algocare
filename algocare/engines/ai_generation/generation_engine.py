"""
ENGINE 4 — AI GENERATION ENGINE
Executes AI API calls using prompt objects from Engine 3.
Handles retries, validation, normalization.
Returns clean generated content.
"""

import re
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import utils.logger as logger
from utils.gemini_client import call as gemini_call

ENGINE = "AIGenerationEngine"

_BASE     = Path(__file__).resolve().parent.parent.parent
_LOGS_DIR = _BASE / "logs"

# ─── Output Validator ─────────────────────────────────────────────────────────

BANNED_WORDS   = [
    "cure", "guaranteed", "detox", "miracle",
    "permanently fixes", "prevents all disease",
    "surprising", "completely", "incredibly",
    "significantly", "truly"
]
BANNED_PHRASES = [
    "did you know", "many people", "experts say", "studies show",
    "it is important to", "in today's world", "you should always",
    "as we all know", "health is wealth"
]
BANNED_PATTERNS = [
    r"#\w+",              # hashtags
    r"\*\*.*?\*\*",       # markdown bold
    r"^Caption:",         # label
    r"^Title:",           # label
]


def _validate_output(text: str, post_type: str) -> tuple:
    """
    Returns (is_valid: bool, reason: str)
    """
    if not text or len(text.strip()) < 10:
        return False, "Output too short or empty"

    if len(text) > 800:
        return False, f"Output too long: {len(text)} chars"

    text_lower = text.lower()

    for word in BANNED_WORDS:
        if word.lower() in text_lower:
            return False, f"Banned word detected: {word}"

    for phrase in BANNED_PHRASES:
        if phrase.lower() in text_lower:
            return False, f"Banned phrase detected: {phrase}"

    for pattern in BANNED_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE | re.MULTILINE):
            return False, f"Banned pattern detected: {pattern}"

    # Check line count vs post type expectations
    lines      = [l for l in text.strip().split("\n") if l.strip()]
    line_count = len(lines)

    if post_type == "Tiny Reminder" and line_count > 3:
        return False, f"Too many lines for Tiny Reminder: {line_count}"

    return True, "ok"


def _clean_output(text: str) -> str:
    """Remove any common AI artifacts from output."""
    text = text.strip()
    # Remove surrounding quotes if present
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()
    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1].strip()
    # Remove "Caption:" label if Gemini added it anyway
    text = re.sub(r"^(Caption|Post|Content|Text):\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


# ─── Main Engine ──────────────────────────────────────────────────────────────

def generate(prompt_object: dict) -> dict:
    """
    Main entry point.
    Receives prompt object from Engine 3.
    Returns generated content object.
    """
    if not prompt_object:
        logger.error(ENGINE, "Received empty prompt object")
        return {"status": "failed", "reason": "empty_prompt_object"}

    if not prompt_object.get("generate_text", True):
        logger.info(ENGINE, "Text generation not requested, skipping")
        return {"status": "skipped", "reason": "not_requested"}

    text_prompt = prompt_object.get("text_prompt", "")
    post_type   = prompt_object.get("post_type", "")
    topic_id    = prompt_object.get("topic_id", "")

    if not text_prompt:
        logger.error(ENGINE, "text_prompt is empty in prompt object")
        return {"status": "failed", "reason": "empty_prompt"}

    start_time = datetime.now(timezone.utc)
    raw_text   = ""

    # Gemini generates with built-in retry (gemini_client handles retries internally)
    raw_text = gemini_call(text_prompt)

    if not raw_text:
        logger.error(ENGINE, f"Gemini returned empty response for topic {topic_id}")
        return {
            "status":   "failed",
            "topic_id": topic_id,
            "reason":   "empty_gemini_response"
        }

    cleaned = _clean_output(raw_text)
    is_valid, reason = _validate_output(cleaned, post_type)

    if not is_valid:
        logger.warning(ENGINE, f"Output validation failed: {reason} | topic={topic_id}")
        # Attempt one more Gemini call with stricter instruction
        stricter_prompt = text_prompt + "\n\nIMPORTANT: Keep it under 3 lines. No labels. Plain text only."
        raw_text2       = gemini_call(stricter_prompt)
        if raw_text2:
            cleaned2     = _clean_output(raw_text2)
            is_valid2, _ = _validate_output(cleaned2, post_type)
            if is_valid2:
                cleaned  = cleaned2
                is_valid = True
                reason   = "ok (retry)"

    end_time    = datetime.now(timezone.utc)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    result = {
        "status":           "success" if is_valid else "failed",
        "topic_id":         topic_id,
        "caption":          cleaned if is_valid else "",
        "raw_output":       raw_text,
        "post_type":        post_type,
        "category":         prompt_object.get("category"),
        "subtopic":         prompt_object.get("subtopic"),
        "angle":            prompt_object.get("angle"),
        "emotion":          prompt_object.get("emotion"),
        "cta_type":         prompt_object.get("cta_type"),
        "caption_length":   prompt_object.get("caption_length"),
        "validation":       reason,
        "provider":         "gemini",
        "generation_time_ms": duration_ms,
        "generated_at":     end_time.isoformat()
    }

    if is_valid:
        logger.info(ENGINE, f"Generation success: {topic_id} | {duration_ms}ms")
    else:
        logger.error(ENGINE, f"Generation failed validation: {topic_id} | {reason}")

    return result
