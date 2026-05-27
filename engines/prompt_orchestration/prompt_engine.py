"""
ENGINE 3 — PROMPT ORCHESTRATION ENGINE
Builds the final Gemini prompt from strategy + visual + rules.
Never calls APIs. Only outputs a ready-to-send prompt object.
Upgraded to inject dual-generation JSON schema instructions at runtime.
"""

import json
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import utils.logger as logger
from utils.file_store import read_json

ENGINE = "PromptOrchestrationEngine"

_BASE        = Path(__file__).resolve().parent.parent.parent
_PROMPTS_DIR = _BASE / "data" / "prompts"


# ─── Data Loaders ─────────────────────────────────────────────────────────────

def _load_base_rules() -> dict:
    return read_json(_PROMPTS_DIR / "base_rules.json") or {}

def _load_format_rules() -> dict:
    return read_json(_PROMPTS_DIR / "formats" / "format_rules.json") or {}


# ─── Prompt Assemblers ────────────────────────────────────────────────────────

def _build_system_block(base_rules: dict) -> str:
    lines = []
    lines.append(base_rules.get("system_identity", ""))
    lines.append("")
    lines.append("The content must feel: " + ", ".join(base_rules.get("tone_goals", [])) + ".")
    lines.append("The content must NOT feel: " + ", ".join(base_rules.get("tone_avoid", [])) + ".")
    lines.append("")
    lines.append(f"Writing style: {base_rules.get('writing_style', '')}.")
    return "\n".join(lines)


def _build_style_block(base_rules: dict) -> str:
    rules = base_rules.get("style_rules", [])
    return "STYLE RULES:\n" + "\n".join(f"- {r}" for r in rules)


def _build_safety_block(base_rules: dict) -> str:
    safety = base_rules.get("safety_rules", [])
    banned_words   = base_rules.get("banned_words", [])
    cautious       = base_rules.get("cautious_phrasing", [])
    banned_phrases = base_rules.get("banned_phrases", [])

    lines = ["SAFETY RULES:"]
    lines += [f"- {r}" for r in safety]
    lines.append("")
    lines.append("BANNED WORDS: " + ", ".join(banned_words))
    lines.append("CAUTIOUS PHRASING (use these instead): " + ", ".join(cautious))
    lines.append("")
    lines.append("BANNED PHRASES (never use):")
    lines += [f"- {p}" for p in banned_phrases]
    return "\n".join(lines)


def _build_output_block(base_rules: dict) -> str:
    rules = base_rules.get("output_rules", [])
    return "OUTPUT RULES:\n" + "\n".join(f"- {r}" for r in rules)


def _build_format_block(post_type: str, format_rules: dict) -> str:
    fmt = format_rules.get(post_type, {})
    if not fmt:
        return f"FORMAT: {post_type}"
    rules     = fmt.get("rules", [])
    max_lines = fmt.get("max_lines", 4)
    lines = [f"FORMAT: {post_type}"]
    lines.append(f"Maximum lines: {max_lines}")
    lines.append("Format rules:")
    lines += [f"- {r}" for r in rules]
    return "\n".join(lines)


def _build_context_block(strategy: dict) -> str:
    """Inject the actual topic context into the prompt."""
    lines = [
        "TOPIC CONTEXT:",
        f"Category: {strategy.get('category', '').replace('_', ' ').title()}",
        f"Subtopic: {strategy.get('subtopic', '')}",
        f"Psychological angle: {strategy.get('angle', '')}",
        f"Emotional mode: {strategy.get('emotion', '')}",
        f"Hook style: {strategy.get('hook_style', '')}",
        f"Content style: {strategy.get('content_style', '')}",
    ]

    cta = strategy.get("cta_type", "no_cta")
    if cta == "ask_question":
        lines.append("End with a gentle open question to the reader.")
    elif cta == "save_this":
        lines.append("The post should feel worth saving or remembering.")
    elif cta == "curiosity_continuation":
        lines.append("End in a way that leaves the reader wanting to know more.")
    else:
        lines.append("No call to action needed. End naturally.")

    return "\n".join(lines)


def _build_generation_instruction(post_type: str) -> str:
    return (
        f"\nNow write the {post_type} post and its accompanying comments.\n"
        "CRITICAL RESPONSE FORMAT INSTRUCTION:\n"
        "You must output your complete response as a single valid JSON object. "
        "Do not wrap your JSON in markdown code blocks (no ```json). "
        "The JSON object configuration structure must match this scheme exactly:\n"
        "{\n"
        '  "caption": "Your generated health post caption body text here matching all format rules",\n'
        '  "comments": [\n'
        '    "First natural, open-ended question or thought from the Page profile to spark discussion",\n'
        '    "Second casual follow-up point or lesser-known observation to drop later",\n'
        '    "Third practical question pushing users to share their everyday habits",\n'
        '    "Fourth helpful community-style comment emphasizing the main takeaway",\n'
        '    "Fifth question encouraging followers to drop their experiences in the thread"\n'
        "  ]\n"
        "}"
    )


# ─── Main Prompt Builder ──────────────────────────────────────────────────────

def build_prompt(strategy_object: dict, visual_object: dict = None) -> dict:
    """
    Main entry point.
    Receives strategy (Engine 2) + visual identity (Engine 6).
    Returns a prompt object ready for Engine 4 to execute.
    """
    if not strategy_object:
        logger.error(ENGINE, "Received empty strategy object")
        return {}

    base_rules   = _load_base_rules()
    format_rules = _load_format_rules()
    post_type    = strategy_object.get("post_type", "Quick Fact")

    # Assemble full text prompt
    sections = [
        _build_system_block(base_rules),
        "",
        _build_style_block(base_rules),
        "",
        _build_safety_block(base_rules),
        "",
        _build_output_block(base_rules),
        "",
        _build_format_block(post_type, format_rules),
        "",
        _build_context_block(strategy_object),
        _build_generation_instruction(post_type),
    ]

    full_prompt = "\n".join(sections)

    # Build image prompt if visual object provided (Phase 2 ready)
    image_prompt = None
    if visual_object:
        image_prompt = _build_image_prompt(visual_object)

    prompt_object = {
        "topic_id":       strategy_object.get("topic_id"),
        "provider":       "gemini",
        "generate_text":  True,
        "generate_image": False,   # Phase 2: set to True when image gen enabled
        "text_prompt":    full_prompt,
        "image_prompt":   image_prompt,
        "post_type":      post_type,
        "category":       strategy_object.get("category"),
        "subtopic":       strategy_object.get("subtopic"),
        "angle":          strategy_object.get("angle"),
        "emotion":        strategy_object.get("emotion"),
        "caption_length": strategy_object.get("caption_length"),
        "cta_type":       strategy_object.get("cta_type"),
        "prompt_built_at": datetime.now(timezone.utc).isoformat()
    }

    logger.info(ENGINE, f"Prompt built for: {post_type} | {strategy_object.get('subtopic')}")
    return prompt_object


def _build_image_prompt(visual_object: dict) -> str:
    """
    Modular image prompt builder.
    Phase 2 — not used yet but ready.
    """
    lines = [
        "[STYLE]",
        "Minimal medical sketch illustration. Thin clean lines. White background.",
        "",
        "[SUBJECT]",
        visual_object.get("visual_hint", visual_object.get("visual_subject", "")),
        "",
        "[MOOD]",
        f"Clean educational doodle. Soft {visual_object.get('color_accent', 'blue')} accent.",
        "",
        "[COMPOSITION]",
        visual_object.get("composition", "centered_object").replace("_", " "),
        "",
        "[BACKGROUND]",
        "Plain white minimal background. No text. No labels.",
        "",
        "[BRAND DNA]",
        "Simple cartoon softness. Educational feel. Lightweight and clean.",
        "Not realistic. Not cinematic. Not detailed anatomy.",
    ]
    return "\n".join(lines)
