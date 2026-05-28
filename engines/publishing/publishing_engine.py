"""
ENGINE 7 — PUBLISHING & DISTRIBUTION ENGINE (FAST-STAGGER UPGRADE)
Publishes the main post, drops comment 1 immediately, then holds the runner
open to drop the remaining 4 comments over the next 8 minutes.
"""

import os
import json
import time
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import utils.logger as logger
from utils.file_store import read_json, write_json, list_json_files, timestamped_filename
from utils.telegram_alert import send_alert

ENGINE = "PublishingEngine"

_BASE           = Path(__file__).resolve().parent.parent.parent
_APPROVED_DIR   = _BASE / "approved"
_PUBLISHED_DIR  = _BASE / "published"
_FAILED_DIR     = _BASE / "failed"
_PUB_LOGS_DIR   = _BASE / "publish_logs"
_SAFE_MODE_FILE = _BASE / "config" / "safe_mode.json"

MAX_RETRIES          = 3
RETRY_DELAY          = 30
SAFE_MODE_THRESHOLD  = 5


# ─── Safe Mode ────────────────────────────────────────────────────────────────

def _get_failure_count() -> int:
    data = read_json(_SAFE_MODE_FILE)
    return data.get("consecutive_failures", 0) if data else 0

def _increment_failure_count():
    count = _get_failure_count() + 1
    write_json(_SAFE_MODE_FILE, {
        "consecutive_failures": count,
        "last_failure": datetime.now(timezone.utc).isoformat()
    })
    if count >= SAFE_MODE_THRESHOLD:
        msg = f"SAFE MODE ACTIVATED — {count} consecutive publish failures."
        logger.error(ENGINE, msg)
        send_alert(f"🔴 {msg}")

def _reset_failure_count():
    write_json(_SAFE_MODE_FILE, {"consecutive_failures": 0})

def _is_safe_mode() -> bool:
    return _get_failure_count() >= SAFE_MODE_THRESHOLD


# ─── Facebook API ─────────────────────────────────────────────────────────────

def _post_to_facebook(caption: str) -> dict:
    """POST caption to Facebook Page. Returns {"success": bool, "post_id": str}"""
    page_token = os.environ.get("FACEBOOK_PAGE_TOKEN", "")
    page_id    = os.environ.get("FACEBOOK_PAGE_ID", "")
    api_ver    = os.environ.get("FACEBOOK_API_VERSION", "v19.0")

    if not page_token or not page_id:
        return {"success": False, "reason": "Missing FACEBOOK_PAGE_TOKEN or FACEBOOK_PAGE_ID"}

    url     = f"https://graph.facebook.com/{api_ver}/{page_id}/feed"
    payload = json.dumps({
        "message":      caption,
        "access_token": page_token
    }).encode("utf-8")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data    = json.loads(resp.read().decode("utf-8"))
                post_id = data.get("id", "")
                if post_id:
                    return {"success": True, "post_id": post_id}
                return {"success": False, "reason": f"No post ID in response: {data}"}

        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="ignore")
            logger.warning(ENGINE, f"HTTP {e.code} attempt {attempt}: {body[:200]}")
            if e.code == 190:
                send_alert("🔴 Facebook token expired. Update your secrets.")
                return {"success": False, "reason": "token_expired"}
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
        except Exception as e:
            logger.warning(ENGINE, f"Publish attempt {attempt} error: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    return {"success": False, "reason": f"Failed after {MAX_RETRIES} attempts"}


def _add_comment_to_post(post_id: str, comment_text: str) -> bool:
    """Sends a matching algorithmic interaction comment using URL Form-Encoding."""
    page_token = os.environ.get("FACEBOOK_PAGE_TOKEN", "")
    api_ver    = os.environ.get("FACEBOOK_API_VERSION", "v19.0")

    if not page_token or not post_id:
        return False

    url = f"https://graph.facebook.com/{api_ver}/{post_id}/comments"
    
    payload_data = {
        "message": comment_text,
        "access_token": page_token
    }
    encoded_payload = urllib.parse.urlencode(payload_data).encode("utf-8")

    try:
        req = urllib.request.Request(
            url,
            data=encoded_payload,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return "id" in data
    except Exception as e:
        return False


# ─── Public: Auto workflow entry point ───────────────────────────────────────

def publish_caption(content) -> dict:
    """Direct publish — used by auto workflow."""
    if _is_safe_mode():
        return {"success": False, "reason": "safe_mode"}

    if isinstance(content, dict):
        caption = content.get("caption", "").strip()
    else:
        caption = str(content).strip()

    if not caption:
        return {"success": False, "reason": "empty_caption"}

    result = _post_to_facebook(caption)

    if result["success"]:
        _reset_failure_count()
        write_json(
            _PUB_LOGS_DIR / "success" / timestamped_filename("pub"),
            {"caption": caption[:200], "post_id": result["post_id"],
             "published_at": datetime.now(timezone.utc).isoformat()}
        )
        logger.info(ENGINE, f"Published main post: {result['post_id']}")
    else:
        _increment_failure_count()
        write_json(
            _PUB_LOGS_DIR / "failed" / timestamped_filename("fail"),
            {"caption": caption[:200], "reason": result["reason"],
             "failed_at": datetime.now(timezone.utc).isoformat()}
        )
        logger.error(ENGINE, f"Publish failed: {result['reason']}")

    return result


# ─── New Fast-Stagger Sequence Execution ──────────────────────────────────────

def queue_comments(post_id: str, comments_list: list):
    """
    Deploys all comments sequentially within a single runtime instance.
    Stagger: Comment 1 (Instant), Comment 2 (2m), Comment 3 (4m), Comment 4 (6m), Comment 5 (8m)
    """
    if not post_id or not comments_list:
        return

    cleaned_comments = [str(c).strip() for c in comments_list if c and str(c).strip()]
    if not cleaned_comments:
        return

    total_comments = len(cleaned_comments)
    logger.info(ENGINE, f"Starting Fast-Stagger deployment loop for {total_comments} comments under post {post_id}...")

    for index, comment in enumerate(cleaned_comments):
        # Stagger delay logic: 0 minutes for the first comment, then 120 seconds (2 minutes) for each next one
        if index > 0:
            delay_seconds = 120
            logger.info(ENGINE, f"Stagger engagement hold: Sleeping for {delay_seconds} seconds before dropping comment {index + 1}...")
            time.sleep(delay_seconds)

        logger.info(ENGINE, f"Deploying comment {index + 1}/{total_comments} to Facebook...")
        success = _add_comment_to_post(post_id, comment)

        if success:
            logger.info(ENGINE, f"Comment {index + 1} went live successfully.")
        else:
            logger.warning(ENGINE, f"Comment {index + 1} deployment encountered an issue or was filtered.")

    logger.info(ENGINE, "Fast-Stagger comment sequence execution completely finished.")


def process_comment_queue():
    """Legacy endpoint preserved for main.py compatibility. No-op configuration."""
    pass
