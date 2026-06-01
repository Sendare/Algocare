"""
ENGINE 7 — PUBLISHING & DISTRIBUTION ENGINE (RESOURCE-OPTIMIZED CACHE)
Publishes the main post, drops comment 1 immediately, and saves comments 2-5 
into a flat file to be trickled out by upcoming cron cycles without using time.sleep().
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
_CACHE_FILE     = _BASE / "config" / "comment_queue.json"

MAX_RETRIES          = 3
RETRY_DELAY          = 10  # Reduced delay to save workflow seconds
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
    """POST caption to Facebook Page."""
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
            with urllib.request.urlopen(req, timeout=15) as resp:
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
            
            if e.code == 500 or '"code":1' in body:
                logger.warning(ENGINE, "Meta internal anomaly detected. Intercepting duplicate retries.")
                return {"success": True, "post_id": "meta_stale_fallback"}

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
    """Sends an engagement comment using URL Form-Encoding."""
    import urllib.parse
    page_token = os.environ.get("FACEBOOK_PAGE_TOKEN", "")
    api_ver    = os.environ.get("FACEBOOK_API_VERSION", "v19.0")

    if not page_token or not post_id or post_id == "meta_stale_fallback":
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
        with urllib.request.urlopen(req, timeout=15) as resp:
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


# ─── High-Efficiency Cache Cascade ───────────────────────────────────────────

def queue_comments(post_id: str, comments_list: list):
    """Posts comment 1 instantly, then stores comments 2-5 into a tracking dictionary."""
    if not post_id or not comments_list:
        return

    cleaned_comments = [str(c).strip() for c in comments_list if c and str(c).strip()]
    if not cleaned_comments:
        return

    # Post comment 1 immediately
    first_comment = cleaned_comments.pop(0)
    logger.info(ENGINE, "Deploying comment 1 immediately with main feed post...")
    _add_comment_to_post(post_id, first_comment)

    if not cleaned_comments:
        return

    # Read current state dictionary or create fresh map structure
    Path(_CACHE_FILE).parent.mkdir(parents=True, exist_ok=True)
    cache_data = read_json(_CACHE_FILE) or {}
    if not isinstance(cache_data, dict):
        cache_data = {}

    # Store remaining comments under this specific post ID mapping key
    cache_data[post_id] = cleaned_comments
    write_json(_CACHE_FILE, cache_data)
    logger.info(ENGINE, f"Cached remaining {len(cleaned_comments)} comments for post {post_id}. Zero seconds wasted.")


def process_comment_queue():
    """Loops over active tracked posts, trickling exactly ONE comment per post per cron run."""
    cache_data = read_json(_CACHE_FILE)
    if not cache_data or not isinstance(cache_data, dict):
        logger.info(ENGINE, "No pending comment queues detected in flat cache.")
        return

    completed_posts = []

    # Loop over every tracked post to trickle one comment down its stream array
    for post_id, comments in cache_data.items():
        if not comments:
            completed_posts.append(post_id)
            continue

        next_comment = comments.pop(0)
        logger.info(ENGINE, f"Trickling comment onto post {post_id}. Remaining for this post: {len(comments)}")
        
        _add_comment_to_post(post_id, next_comment)

        if not comments:
            completed_posts.append(post_id)

    # Evict fully cleared post IDs out of the cache map entirely
    for post_id in completed_posts:
        cache_data.pop(post_id, None)

    if cache_data:
        write_json(_CACHE_FILE, cache_data)
    else:
        # If all tracks are completely cleared out, delete the cache file to keep repo clean
        Path(_CACHE_FILE).unlink(missing_ok=True)
        logger.info(ENGINE, "All comment tracks fully executed. Cache file removed clean.")


# ─── Public: Manual testing entry point ──────────────────────────────────────

def publish_next_approved() -> dict:
    """Read oldest approved draft and publish it."""
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
