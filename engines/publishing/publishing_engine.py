"""
ENGINE 7 — PUBLISHING & DISTRIBUTION ENGINE
Handles formatting, publishing to Facebook, retries, safe mode, logging.
Upgraded with a 1-minute console heartbeat trickle loop to beat the Meta reach 
algorithm without triggering a silent runner termination on GitHub Actions.

Two modes:
  publish_caption(content)  — used by auto workflow (Engine 8) [Accepts str or dict]
  publish_next_approved()   — used for manual Termux testing
"""

import os
import json
import time
import urllib.request
import urllib.error
from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import utils.logger as logger
from utils.file_store import read_json, write_json, list_json_files, timestamped_filename
from utils.telegram_alert import send_alert

ENGINE = "PublishingEngine"

_BASE          = Path(__file__).resolve().parent.parent.parent
_APPROVED_DIR  = _BASE / "approved"
_PUBLISHED_DIR = _BASE / "published"
_FAILED_DIR    = _BASE / "failed"
_PUB_LOGS_DIR  = _BASE / "publish_logs"
_SAFE_MODE_FILE = _BASE / "config" / "safe_mode.json"

MAX_RETRIES          = 3
RETRY_DELAY          = 30
SAFE_MODE_THRESHOLD  = 5
COMMENT_DELAY        = 530 
#seconds = 9 minutes


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
    """
    POST caption to Facebook Page.
    Returns {"success": bool, "post_id": str, "reason": str}
    """
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
                msg = "Facebook token expired. Update FACEBOOK_PAGE_TOKEN in GitHub Secrets."
                send_alert(f"🔴 {msg}")
                return {"success": False, "reason": "token_expired"}

            if attempt < MAX_RETRIES:
                logger.info(ENGINE, f"Retrying in {RETRY_DELAY}s...")
                time.sleep(RETRY_DELAY)

        except Exception as e:
            logger.warning(ENGINE, f"Publish attempt {attempt} error: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    return {"success": False, "reason": f"Failed after {MAX_RETRIES} attempts"}


def _add_comment_to_post(post_id: str, comment_text: str) -> bool:
    """Sends a matching algorithmic interaction comment under the created post."""
    page_token = os.environ.get("FACEBOOK_PAGE_TOKEN", "")
    api_ver    = os.environ.get("FACEBOOK_API_VERSION", "v19.0")

    url = f"https://graph.facebook.com/{api_ver}/{post_id}/comments"
    payload = json.dumps({
        "message":      comment_text,
        "access_token": page_token
    }).encode("utf-8")

    try:
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return "id" in data
    except Exception as e:
        logger.warning(ENGINE, f"Failed to post algorithmic background comment: {e}")
        return False


# ─── Public: Auto workflow entry point ───────────────────────────────────────

def publish_caption(content) -> dict:
    """
    Direct publish — used by auto workflow (no draft files involved).
    Accepts raw caption string or dictionary containing {"caption": "...", "comments": []}
    Returns {"success": bool, "post_id": str, "reason": str}
    """
    if _is_safe_mode():
        msg = "Safe mode active. Publishing paused."
        logger.error(ENGINE, msg)
        return {"success": False, "reason": "safe_mode"}

    # Separate comments array from main post caption if data dictionary is provided
    comments_list = []
    if isinstance(content, dict):
        caption = content.get("caption", "").strip()
        comments_list = content.get("comments", [])
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
        logger.info(ENGINE, f"Published: {result['post_id']}")

    else:
        _increment_failure_count()
        write_json(
            _PUB_LOGS_DIR / "failed" / timestamped_filename("fail"),
            {"caption": caption[:200], "reason": result["reason"],
             "failed_at": datetime.now(timezone.utc).isoformat()}
        )
        logger.error(ENGINE, f"Publish failed: {result['reason']}")

    return result


# ─── Public: Manual testing entry point ──────────────────────────────────────

def publish_next_approved() -> dict:
    """
    Read oldest approved draft and publish it.
    Used for manual Termux testing only.
    """
    if _is_safe_mode():
        return {"status": "safe_mode", "reason": "Safe mode active"}

    approved = list_json_files(_APPROVED_DIR)
    if not approved:
        logger.info(ENGINE, "No approved posts found")
        return {"status": "no_posts"}

    draft_path = approved[0]
    draft_data = read_json(draft_path)
    if not draft_data:
        draft_path.unlink(missing_ok=True)
        return {"status": "failed", "reason": "Unreadable draft"}

    caption = draft_data.get("caption", "").strip() if isinstance(draft_data, dict) else ""
    if not caption:
        draft_path.unlink(missing_ok=True)
        return {"status": "failed", "reason": "No caption in draft"}

    result = publish_caption(draft_data if isinstance(draft_data, dict) and "comments" in draft_data else caption)

    if result["success"]:
        if isinstance(draft_data, dict):
            draft_data.update({
                "status":          "published",
                "facebook_post_id": result["post_id"],
                "published_at":    datetime.now(timezone.utc).isoformat()
            })
        write_json(_PUBLISHED_DIR / draft_path.name, draft_data)
        draft_path.unlink(missing_ok=True)
        return {"status": "published", "facebook_post_id": result["post_id"]}
    else:
        if isinstance(draft_data, dict):
            draft_data.update({"status": "failed", "reason": result["reason"]})
        write_json(_FAILED_DIR / draft_path.name, draft_data)
        draft_path.unlink(missing_ok=True)
        return {"status": "failed", "reason": result["reason"]}


# ─── Public: Delayed Trickle Operations ──────────────────────────────────────

def trickle_comments_only(post_id: str, comments_list: list):
    """
    Handles dropping algorithmic interaction comments sequentially.
    Uses a 1-minute heartbeat sub-loop to prevent GitHub Actions from 
    canceling the run due to silence.
    """
    if not post_id or not comments_list:
        return

    logger.info(ENGINE, f"Starting trickle for {len(comments_list)} comments.")
    for index, comment in enumerate(comments_list):
        if not comment or not str(comment).strip():
            continue

        if index > 0:
            total_wait_minutes = COMMENT_DELAY // 60
            logger.info(ENGINE, f"Starting {total_wait_minutes}-minute delay before comment {index + 1}...")

            # Break down 10 minutes into 1-minute intervals with live console prints
            for minute in range(1, total_wait_minutes + 1):
                time.sleep(60)
                logger.info(ENGINE, f"  [Heartbeat] Waiting... ({minute}/{total_wait_minutes} minutes elapsed)")

        logger.info(ENGINE, f"Dropping automated comment {index + 1}/{len(comments_list)}...")
        success = _add_comment_to_post(post_id, str(comment).strip())
        if success:
            logger.info(ENGINE, f"Comment {index + 1} posted successfully.")
        else:
            logger.error(ENGINE, "Trickle loop stopped early due to an API transmission error.")
            break
