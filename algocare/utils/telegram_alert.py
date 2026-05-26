"""
utils/telegram_alert.py
Sends Telegram alerts on warnings and errors.
Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID as environment variables.
"""

import os
import json
import urllib.request
import urllib.error


def send_alert(message: str) -> bool:
    """
    Send a message to Telegram.
    Returns True on success, False on failure.
    Never raises — Telegram failure must not crash the system.
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id   = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not bot_token or not chat_id:
        return False

    url     = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = json.dumps({
        "chat_id":    chat_id,
        "text":       f"🤖 Algocare\n{message}",
        "parse_mode": "HTML"
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.status == 200
    except Exception:
        return False
