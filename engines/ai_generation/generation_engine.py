"""
ENGINE 4 — AI GENERATION ENGINE
Executes AI API calls using prompt objects from Engine 3.
Handles retries, validation, normalization.
Upgraded to safely handle JSON dictionaries for caption + multi-comment workflows.
"""

import re
import json
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
    """Remove any common AI artifacts from output strings."""
    text = text.strip()
    # Remove surrounding quotes if present
    if text.startswith('"') and text.endswith('"'):
        text = text[1:-1].strip()
    if text.startswith("'") and text.endswith("'"):
        text = text[1:-1].strip()
    # Remove metadata labels if added by the provider
    text = re.sub(r"^(Caption|Post|Content|Text):\s*", "", text, flags=re.IGNORECASE)
    return text.strip()


# ─── Main Engine ──────────────────────────────────────────────────────────────

def generate(prompt_object: dict) -> dict:
    """
    Main entry point.
    Receives prompt object from Engine 3.
    Parses complex JSON outputs containing both post captions and arrays of comments.
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
    
    # Execute AI prompt through our standard Groq Client tool
    raw_response = gemini_call(text_prompt)

    if not raw_response:
        logger.error(ENGINE, f"Provider returned empty response for topic {topic_id}")
        return {
            "status":   "failed",
            "topic_id": topic_id,
            "reason":   "empty_api_response"
        }

    # Safe extraction parsing block to handle dict objects returned directly by utils.gemini_client
    caption_text = ""
    comments_list = []

    if isinstance(raw_response, dict):
        caption_text = raw_response.get("caption", "")
        comments_list = raw_response.get("comments", [])
    else:
        # Fallback security check in case raw text slipped through
        try:
            parsed = json.loads(raw_response)
            caption_text = parsed.get("caption", "")
            comments_list = parsed.get("comments", [])
        except Exception:
            caption_text = raw_response

    cleaned_caption = _clean_output(caption_text)
    is_valid, reason = _validate_output(cleaned_caption, post_type)

    # Perform validation checks on every generated trickle comment for safety compliance
    validated_comments = []
    if is_valid and comments_list:
        for comment in comments_list:
            cleaned_comm = _clean_output(str(comment))
            comm_valid, _ = _validate_output(cleaned_comm, "Comment")
            if comm_valid:
                validated_comments.append(cleaned_comm)

    end_time    = datetime.now(timezone.utc)
    duration_ms = int((end_time - start_time).total_seconds() * 1000)

    result = {
        "status":           "success" if is_valid else "failed",
        "topic_id":         topic_id,
        "caption":          cleaned_caption if is_valid else "",
        "comments":         validated_comments if is_valid else [],
        "raw_output":       str(raw_response),
        "post_type":        post_type,
        "category":         prompt_object.get("category"),
        "subtopic":         prompt_object.get("subtopic"),
        "angle":            prompt_object.get("angle"),
        "emotion":          prompt_object.get("emotion"),
        "cta_type":         prompt_object.get("cta_type"),
        "caption_length":   prompt_object.get("caption_length"),
        "validation":       reason,
        "provider":         "groq_json",
        "generation_time_ms": duration_ms,
        "generated_at":     end_time.isoformat()
    }

    if is_valid:
        logger.info(ENGINE, f"Generation success: {topic_id} | {duration_ms}ms")
    else:
        logger.error(ENGINE, f"Generation failed validation: {topic_id} | {reason}")

    return result
