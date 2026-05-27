"""
utils/gemini_client.py
Patched Wrapper using Groq Cloud API for Algocare Engine 4 content pipelines.
Handles auth, rate limiting, retries, and OpenAI-style response normalization.
Bypasses Cloudflare block 1010 via explicit browser User-Agent headers.
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

# Rate limiting state (in-process, resets on restart — fine for our use case)
_call_timestamps: list = []
RATE_LIMIT_PER_MINUTE = 15


def _enforce_rate_limit():
    """Ensure we don't burst calls too quickly in stateless environments."""
    now = time.time()
    global _call_timestamps
    # Remove timestamps older than 60 seconds
    _call_timestamps = [t for t in _call_timestamps if now - t < 60]

    if len(_call_timestamps) >= RATE_LIMIT_PER_MINUTE:
        wait = 60 - (now - _call_timestamps[0]) + 1
        logger.info(ENGINE, f"Rate limit reached. Waiting {wait:.1f}s")
        time.sleep(wait)

    _call_timestamps.append(time.time())
    
    # 3-second safety delay to keep automated execution threads stable
    time.sleep(3)


def call(prompt: str, temperature: float = 0.85, max_retries: int = 3) -> str:
    """
    Send a prompt to Groq and return the text response.
    Returns empty string on complete failure after retries.
    """
    # 1. Look for GROQ_API_KEY first, fallback to GEMINI_API_KEY if reusing the env slot
    api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        logger.error(ENGINE, "GROQ_API_KEY or GEMINI_API_KEY not set in environment")
        return ""

    # 2. Select the top text model visible from your Groq dashboard screenshot
    model = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
    url = "https://api.groq.com/openai/v1/chat/completions"

    # 3. Format payload to comply with OpenAI/Groq Chat Completion specification
    payload = json.dumps({
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": temperature,
        "max_tokens": 1000,
    }).encode("utf-8")

    for attempt in range(1, max_retries + 1):
        try:
            _enforce_rate_limit()

            # 4. Request with browser User-Agent configuration to clear Cloudflare rules
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
                raw  = resp.read().decode("utf-8")
                data = json.loads(raw)

            # Extract text from OpenAI/Groq JSON response tree structure
            text = data["choices"][0]["message"]["content"].strip()

            if text:
                logger.info(ENGINE, f"Groq call success ({model}) (attempt {attempt})")
                return text
            else:
                logger.warning(ENGINE, f"Empty response from Groq (attempt {attempt})")

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            logger.warning(ENGINE, f"HTTP {e.code} on attempt {attempt}: {body[:200]}")

            if e.code == 429:
                # Server rate limits — back off incrementally
                wait = 30 * attempt
                logger.info(ENGINE, f"Server rate limit hit. Waiting {wait}s")
                time.sleep(wait)
            elif e.code >= 500:
                time.sleep(10 * attempt)
            else:
                # 4xx client anomalies (401 Bad Token, 400 Bad JSON) — skip retries
                break

        except Exception as e:
            logger.warning(ENGINE, f"Groq execution error on attempt {attempt}: {e}")
            time.sleep(10 * attempt)

    logger.error(ENGINE, f"Groq client call completely failed after {max_retries} attempts")
    return ""
