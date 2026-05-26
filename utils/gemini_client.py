"""
utils/gemini_client.py
Single Gemini API wrapper for all engines.
Handles auth, rate limiting, retries, and response normalization.
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

ENGINE = "GeminiClient"

# Rate limiting state (in-process, resets on restart — fine for our use case)
_call_timestamps: list = []
RATE_LIMIT_PER_MINUTE = 15


def _enforce_rate_limit():
    """Ensure we don't exceed 15 calls/minute (Gemini free tier)."""
    now = time.time()
    # Remove timestamps older than 60 seconds
    global _call_timestamps
    _call_timestamps = [t for t in _call_timestamps if now - t < 60]

    if len(_call_timestamps) >= RATE_LIMIT_PER_MINUTE:
        wait = 60 - (now - _call_timestamps[0]) + 1
        logger.info(ENGINE, f"Rate limit reached. Waiting {wait:.1f}s")
        time.sleep(wait)

    _call_timestamps.append(time.time())


def call(prompt: str, temperature: float = 0.85, max_retries: int = 3) -> str:
    """
    Send a prompt to Gemini and return the text response.
    Returns empty string on complete failure after retries.
    """
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.error(ENGINE, "GEMINI_API_KEY not set in environment")
        return ""

    model   = os.environ.get("gemini-2.5-flash", "gemini-1.5-flash", GEMINI_MODEL)
    url     = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature":    temperature,
            "maxOutputTokens": 1000,
        }
    }).encode("utf-8")

    for attempt in range(1, max_retries + 1):
        try:
            _enforce_rate_limit()

            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )

            with urllib.request.urlopen(req, timeout=30) as resp:
                raw  = resp.read().decode("utf-8")
                data = json.loads(raw)

            # Extract text from Gemini response structure
            text = (
                data.get("candidates", [{}])[0]
                    .get("content", {})
                    .get("parts", [{}])[0]
                    .get("text", "")
                    .strip()
            )

            if text:
                logger.info(ENGINE, f"Gemini call success (attempt {attempt})")
                return text
            else:
                logger.warning(ENGINE, f"Empty response from Gemini (attempt {attempt})")

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            logger.warning(ENGINE, f"HTTP {e.code} on attempt {attempt}: {body[:200]}")

            if e.code == 429:
                # Rate limited by server — wait longer
                wait = 30 * attempt
                logger.info(ENGINE, f"Server rate limit. Waiting {wait}s")
                time.sleep(wait)
            elif e.code >= 500:
                time.sleep(10 * attempt)
            else:
                # 4xx that isn't 429 — not worth retrying
                break

        except Exception as e:
            logger.warning(ENGINE, f"Gemini call error on attempt {attempt}: {e}")
            time.sleep(10 * attempt)

    logger.error(ENGINE, f"Gemini call failed after {max_retries} attempts")
    return ""
