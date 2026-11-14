import json
import os
import urllib.error
import urllib.request

# Confirm this is the exact model string you want before running at scale.
MODEL_NAME = "gemini-3.5-flash-lite"

# Talks to the REST API directly instead of the google-genai SDK. This avoids
# the SDK's pydantic-core dependency (no prebuilt wheel on some environments,
# e.g. Termux/Python 3.14) and keeps this file dependency-free (stdlib only).

_API_KEYS = None
_CURRENT_KEY_INDEX = 0


def _load_api_keys():
    """
    Reads keys from GEMINI_API_KEYS as a comma-separated list (preferred -
    one secret holding all fallback keys), falling back to a single
    GEMINI_API_KEY for backward compatibility. First key is tried first;
    the rest are only used if an earlier key hits a quota/rate limit.
    """
    multi = os.environ.get("GEMINI_API_KEYS", "")
    keys = [k.strip() for k in multi.split(",") if k.strip()]
    if not keys:
        single = os.environ.get("GEMINI_API_KEY", "").strip()
        if single:
            keys = [single]
    if not keys:
        raise RuntimeError(
            "No Gemini API key(s) found. Set GEMINI_API_KEYS (comma-separated) "
            "or GEMINI_API_KEY."
        )
    return keys


def _get_keys():
    global _API_KEYS
    if _API_KEYS is None:
        _API_KEYS = _load_api_keys()
    return _API_KEYS


def _request_once(system_prompt, user_prompt):
    """Makes one request, rotating through GEMINI_API_KEYS on quota/rate-limit
    errors. Returns the raw text response. Raises RuntimeError for anything
    that isn't recoverable by trying a different key."""
    global _CURRENT_KEY_INDEX
    keys = _get_keys()

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }
    data = json.dumps(payload).encode("utf-8")

    last_error_text = None
    attempts = 0
    start_index = _CURRENT_KEY_INDEX
    resp_body = None

    while attempts < len(keys):
        key_index = (start_index + attempts) % len(keys)
        api_key = keys[key_index]
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{MODEL_NAME}:generateContent?key={api_key}"
        )
        req = urllib.request.Request(
            url, data=data, headers={"Content-Type": "application/json"}
        )

        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                resp_body = json.loads(resp.read().decode("utf-8"))
            _CURRENT_KEY_INDEX = key_index  # start from this key next call
            break
        except urllib.error.HTTPError as e:
            body_text = e.read().decode("utf-8", errors="replace")
            is_quota_error = e.code == 429
            if not is_quota_error:
                try:
                    status = json.loads(body_text).get("error", {}).get("status", "")
                    is_quota_error = status == "RESOURCE_EXHAUSTED"
                except Exception:
                    pass

            if is_quota_error:
                print(f"⚠️  Key #{key_index + 1}/{len(keys)} hit a quota/rate limit. Trying next key...")
                last_error_text = body_text
                attempts += 1
                continue

            raise RuntimeError(f"Gemini API returned HTTP {e.code}: {body_text[:500]}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"Network error reaching Gemini API: {e}")
    else:
        raise RuntimeError(
            f"All {len(keys)} Gemini API key(s) hit quota/rate limits. "
            f"Last error: {last_error_text}"
        )

    try:
        return resp_body["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        raise ValueError(f"Unexpected Gemini response shape: {json.dumps(resp_body)[:500]}")


def call_gemini(system_prompt, user_prompt, _is_retry=False):
    """
    Calls Gemini with a system instruction + user prompt, forcing JSON-mode
    output via response_mime_type. Returns the parsed JSON object (dict/list).

    Two layers of resilience against occasional malformed output:
    - strict=False on json.loads() tolerates raw control characters (e.g. an
      unescaped literal newline inside a string) that would otherwise fail
      strict JSON parsing - a standard, safe stdlib option, not a workaround.
    - If parsing still fails, the whole request is retried ONCE with a fresh
      call, since these are usually one-off generation slips rather than a
      prompt problem - a second attempt often just succeeds.

    Raises ValueError if the response still isn't valid JSON after the
    retry, so callers can treat that as a failed topic and move on.
    """
    raw_text = _request_once(system_prompt, user_prompt)

    try:
        return json.loads(raw_text, strict=False)
    except json.JSONDecodeError as e:
        if not _is_retry:
            print("⚠️  Malformed JSON response, retrying once...")
            return call_gemini(system_prompt, user_prompt, _is_retry=True)
        raise ValueError(f"AI response was not valid JSON after retry: {e}\nRaw response: {raw_text[:500]}")
