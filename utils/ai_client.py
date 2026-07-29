import os
import json
from google import genai
from google.genai import types

# Confirm this is the exact model string you want before running at scale.
MODEL_NAME = "gemini-3.5-flash-lite"


def get_client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")
    return genai.Client(api_key=api_key)


def call_gemini(system_prompt, user_prompt):
    """
    Calls Gemini with a system instruction + user prompt, forcing JSON-mode
    output via response_mime_type so the model can't wrap the reply in
    markdown fences or add commentary around it.

    Returns the parsed JSON object (dict/list). Raises ValueError if the
    response isn't valid JSON, so callers can treat that as a failed
    topic and move on rather than crashing the whole run.
    """
    client = get_client()

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
        ),
    )

    raw_text = (response.text or "").strip()

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"AI response was not valid JSON: {e}\nRaw response: {raw_text[:500]}")
