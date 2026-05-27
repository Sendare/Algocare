"""
utils/gemini_client.py
Multi-Comment Generation Engine using Groq Cloud API.
Generates a structured payload containing a post caption and 5 distinct conversational comments.
"""

import os
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import utils.logger as logger

ENGINE = "GroqClient"
_call_timestamps: list = []
RATE_LIMIT_PER_MINUTE = 15


def _enforce_rate_limit():
    now = time.time()
    global _call_timestamps
    _call_timestamps = [t for t in _call_timestamps if now - t < 60]

    if len(_call_timestamps) >= RATE_LIMIT_PER_MINUTE:
        wait = 60 - (now - _call_timestamps[0]) + 1
        logger.info(ENGINE, f"Rate limit reached. Waiting {wait:.1f}s")
        time.sleep(wait)

    _call_timestamps.append(time.time())
    time.sleep(3)


def call(prompt: str, temperature: float = 0.85, max_retries: int = 3) -> dict:
    """
    Send a prompt to Groq requesting a JSON response with 'caption' and an array of 5 'comments'.
    Returns a dictionary {"caption": "...", "comments": ["...", "...", ...]}
    """
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.error(ENGINE, "GROQ_API_KEY or GEMINI_API_KEY not set in environment")
        return {"caption": "", "comments": []}

    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    url = "https://api.groq.com/openai/v1/chat/completions"

    structured_prompt = (
        f"{prompt}\n\n"
        "CRITICAL: You must respond ONLY with a raw JSON object. Do not include markdown code blocks or text outside the JSON.\n"
        "The JSON object must have exactly these fields:\n"
        "{\n"
        '  "caption": "Your generated health post content here",\n'
        '  "comments": [\n'
        '    "First natural question/thought to spark debate",\n'
        '    "Second follow-up angle or common misconception to drop later",\n'
        '    "Third conversational point about daily habits related to the topic",\n'
        '    "Fourth helpful community-style tip or observation",\n'
        '    "Fifth question pushing users to share their own experiences"\n'
        "  ]\n"
        "}"
    )

    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": structured_prompt}],
        "temperature": temperature,
        "max_tokens": 1500,
        "response_format": {"type": "json_object"}
    }).encode("utf-8")

    for attempt in range(1, max_retries + 1):
        try:
            _enforce_rate_limit()

            req = urllib.request.Request(
                url,
                data=payload,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                },
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                raw = resp.read().decode("utf-8")
                data = json.loads(raw)

            raw_json_string = data["choices"][0]["message"]["content"].strip()
            parsed_content = json.loads(raw_json_string)

            caption = parsed_content.get("caption", "").strip()
            comments = parsed_content.get("comments", [])

            if caption:
                logger.info(ENGINE, f"Groq Multi-Comment JSON generation success (attempt {attempt})")
                return {"caption": caption, "comments": comments[:5]}

        except Exception as e:
            logger.warning(ENGINE, f"Groq parsing error on attempt {attempt}: {e}")
            time.sleep(5 * attempt)

    logger.error(ENGINE, f"Groq client call completely failed after {max_retries} attempts")
    return {"caption": "", "comments": []}
