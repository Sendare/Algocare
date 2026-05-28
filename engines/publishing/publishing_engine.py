"""
ENGINE 7 — PUBLISHING & DISTRIBUTION ENGINE
Handles formatting, publishing to Facebook, retries, safe mode, and file logging.
Upgraded to instantly post the 1st comment and queue the remaining 4 comments.

Three major public entry points:
  1. publish_caption(content)   — used by auto workflow (Engine 8) to post main feed
  2. process_comment_queue()    — called by main.py to trickle one comment per cron run
  3. publish_next_approved()    — used for manual Termux terminal testing
"""

import os
import json
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

_BASE           = Path(__file__).resolve().parent.parent.parent
_APPROVED_DIR   = _BASE / "approved"
_PUBLISHED_DIR  = _BASE / "published"
_FAILED_DIR     = _BASE / "failed"
_PUB_LOGS_DIR   = _BASE / "publish_logs"
_SAFE_MODE_FILE = _BASE / "config" / "safe_mode.json"
_QUEUE_FILE     = _BASE / "config" / "comment_queue.json"

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
                import time
                time.sleep(RETRY_DELAY)
        except Exception as e:
            logger.warning(ENGINE, f"Publish attempt {attempt} error: {e}")
            if attempt < MAX_RETRIES:
                import time
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
        logger.warning(ENGINE, f"Failed to post comment: {e}")
        return False


# ─── Public: Auto workflow entry point ───────────────────────────────────────

def publish_caption(content) -> dict:
    """Direct publish — used by auto workflow (no draft files involved)."""
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


# ─── Public: Zero-Sleep Queue Operations ─────────────────────────────────────

def queue_comments(post_id: str, comments_list: list):
    """
    Splits the comment list: instantly fires comment 1, 
    and queues up the remaining comments (2-5) into flat file storage.
    """
    if not post_id or not comments_list:
        return

    cleaned_comments = [str(c).strip() for c in comments_list if c and str(c).strip()]
    if not cleaned_comments:
        return

    # 1. INSTANT DEPLOYMENT: Pop and post the very first comment right now
    first_comment = cleaned_comments.pop(0)
    logger.info(ENGINE, f"Deploying comment 1 immediately with main feed post...")
    instant_success = _add_comment_to_post(post_id, first_comment)
    
    if instant_success:
        logger.info(ENGINE, "Comment 1 dropped successfully on Facebook.")
    else:
        # Fallback: if instant delivery fails, add it back to front of queue so it isn't lost
        cleaned_comments.insert(0, first_comment)
        logger.warning(ENGINE, "Instant comment failed to deploy. Appending back into queue.")

    if not cleaned_comments:
        return

    # Ensure config/ folder path directory exists dynamically
    Path(_QUEUE_FILE).parent.mkdir(parents=True, exist_ok=True)

    # Read current queue state or initialize fresh list structure
    queue_data = read_json(_QUEUE_FILE) or []
    
    # Append remaining structured record objects
    for comment in cleaned_comments:
        queue_data.append({
            "post_id": post_id,
            "comment_text": comment,
            "queued_at": datetime.now(timezone.utc).isoformat()
        })

    write_json(_QUEUE_FILE, queue_data)
    logger.info(ENGINE, f"Successfully saved remaining {len(cleaned_comments)} interaction comments into flat storage file.")


def process_comment_queue():
    """Processes exactly ONE comment from the queue per execution. Completely eliminates sleeps."""
    queue_data = read_json(_QUEUE_FILE)
    if not queue_data or not isinstance(queue_data, list):
        logger.info(ENGINE, "Comment queue is empty. No tasks to process.")
        return

    # Pop oldest item in queue (FIFO stack configuration)
    next_item = queue_data.pop(0)
    post_id = next_item.get("post_id")
    comment_text = next_item.get("comment_text")

    logger.info(ENGINE, f"Processing item from queue. Remaining in backup: {len(queue_data)}")
    logger.info(ENGINE, f"Dropping comment for post {post_id}...")
    
    success = _add_comment_to_post(post_id, comment_text)
    
    if success:
        logger.info(ENGINE, "Queue item posted successfully to Facebook Page.")
        # Update queue tracking file with remaining entries
        write_json(_QUEUE_FILE, queue_data)
    else:
        logger.error(ENGINE, "Failed to deliver queue item. Retaining item in queue for next cycle retry.")


# ─── Public: Manual testing entry point ──────────────────────────────────────

def publish_next_approved() -> dict:
    """Read oldest approved draft and publish it (Used for local Termux tests)."""
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

    result = publish_caption(draft_data)

    if result["success"]:
        if isinstance(draft_data, dict):
            draft_data.update({
                "status":          "published",
                "facebook_post_id": result["post_id"],
                "published_at":    datetime.now(timezone.utc).isoformat()
            })
        write_json(_PUBLISHED_DIR / draft_path.name, draft_data)
        
        # Split and process using the unified split method logic
        if isinstance(draft_data, dict) and "comments" in draft_data:
            queue_comments(result["post_id"], draft_data["comments"])
            
        draft_path.unlink(missing_ok=True)
        return {"status": "published", "facebook_post_id": result["post_id"]}
    else:
        if isinstance(draft_data, dict):
            draft_data.update({"status": "failed", "reason": result["reason"]})
        write_json(_FAILED_DIR / draft_path.name, draft_data)
        draft_path.unlink(missing_ok=True)
        return {"status": "failed", "reason": result["reason"]}
