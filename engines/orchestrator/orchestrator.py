"""
ENGINE 8 — ORCHESTRATOR ENGINE
Central controller. Coordinates all engines sequentially.
Controls, never thinks. Business logic stays in individual engines.
Upgraded to pipeline complex multi-comment data payloads safely.
"""

from pathlib import Path
from datetime import datetime, timezone

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
import utils.logger as logger
from utils.file_store import write_json, list_json_files, read_json, timestamped_filename
from utils.telegram_alert import send_alert

from engines.topic_intelligence.topic_engine    import generate_topic
from engines.content_strategy.strategy_engine   import build_strategy
from engines.visual_identity.visual_engine      import build_visual_identity
from engines.prompt_orchestration.prompt_engine import build_prompt
from engines.ai_generation.generation_engine    import generate
from engines.memory.memory_engine               import (
    record_combination, update_recent, get_stats
)
from engines.publishing.publishing_engine       import publish_caption

ENGINE = "Orchestrator"

_BASE              = Path(__file__).resolve().parent.parent.parent
_PUBLISHED_DIR     = _BASE / "published"
_WORKFLOW_LOGS_DIR = _BASE / "workflow_logs"


# ─── Workflow ID ──────────────────────────────────────────────────────────────

def _make_workflow_id() -> str:
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"WF_{ts}"


def _log_workflow(workflow_id: str, state: dict, folder: str = "completed"):
    path = _WORKFLOW_LOGS_DIR / folder / f"{workflow_id}.json"
    write_json(path, state)


# ─── Workflow: Full Auto (generate + publish in one shot) ─────────────────────

def run_auto_workflow() -> dict:
    """
    Full automation pipeline used by GitHub Actions.
    Engine 1 → 2 → 6 → 3 → 4 → publish → memory update.
    No human approval step.
    """
    workflow_id = _make_workflow_id()
    started_at  = datetime.now(timezone.utc).isoformat()
    state       = {
        "workflow_id": workflow_id,
        "type":        "auto",
        "started_at":  started_at
    }

    logger.info(ENGINE, f"=== AUTO WORKFLOW START: {workflow_id} ===")

    # ── Engine 1: Topic Intelligence
    logger.info(ENGINE, "Engine 1: Topic Intelligence")
    topic_object = generate_topic()
    if not topic_object:
        state.update({"status": "failed", "failed_engine": "TopicIntelligenceEngine"})
        _log_workflow(workflow_id, state, "failed")
        send_alert("🔴 Workflow failed at Engine 1 (Topic Intelligence)")
        return state

    # ── Engine 2: Content Strategy
    logger.info(ENGINE, "Engine 2: Content Strategy")
    strategy_object = build_strategy(topic_object)
    if not strategy_object:
        state.update({"status": "failed", "failed_engine": "ContentStrategyEngine"})
        _log_workflow(workflow_id, state, "failed")
        send_alert("🔴 Workflow failed at Engine 2 (Content Strategy)")
        return state

    # ── Engine 6: Visual Identity
    logger.info(ENGINE, "Engine 6: Visual Identity")
    visual_object = build_visual_identity(strategy_object)

    # ── Engine 3: Prompt Orchestration
    logger.info(ENGINE, "Engine 3: Prompt Orchestration")
    prompt_object = build_prompt(strategy_object, visual_object)
    if not prompt_object:
        state.update({"status": "failed", "failed_engine": "PromptOrchestrationEngine"})
        _log_workflow(workflow_id, state, "failed")
        send_alert("🔴 Workflow failed at Engine 3 (Prompt Orchestration)")
        return state

    # ── Engine 4: AI Generation
    logger.info(ENGINE, "Engine 4: AI Generation")
    generation_result = generate(prompt_object)
    if generation_result.get("status") != "success":
        reason = generation_result.get("reason", "unknown")
        state.update({"status": "failed", "failed_engine": "AIGenerationEngine", "reason": reason})
        _log_workflow(workflow_id, state, "failed")
        send_alert(f"🔴 Workflow failed at Engine 4 (AI Generation): {reason}")
        return state

    caption = generation_result.get("caption", "")
    comments = generation_result.get("comments", [])

    # Bundle caption data alongside the comment arrays to run the trickle loop cleanly
    publishing_payload = {
        "caption": caption,
        "comments": comments
    }

    # ── Engine 7: Publish directly
    logger.info(ENGINE, "Engine 7: Publishing with Delayed Comments Loop")
    publish_result = publish_caption(publishing_payload)

    if publish_result.get("success"):
        # ── Update memory after successful publish
        record_combination(
            topic_object.get("category", ""),
            topic_object.get("subtopic", ""),
            topic_object.get("angle", ""),
            topic_object.get("post_type", "")
        )
        update_recent("category", topic_object.get("category", ""))
        update_recent("angle",    topic_object.get("angle", ""))
        update_recent("post_type", topic_object.get("post_type", ""))
        update_recent("cta",      strategy_object.get("cta_type", ""))

        # ── Archive published record
        published_record = {
            "status":          "published",
            "workflow_id":     workflow_id,
            "topic_id":        topic_object.get("topic_id"),
            "category":        topic_object.get("category"),
            "subtopic":        topic_object.get("subtopic"),
            "angle":           topic_object.get("angle"),
            "post_type":       topic_object.get("post_type"),
            "emotion":         topic_object.get("emotion"),
            "caption":         caption,
            "comments_seeded": comments,
            "facebook_post_id": publish_result.get("post_id"),
            "published_at":    datetime.now(timezone.utc).isoformat(),
            "generation_time_ms": generation_result.get("generation_time_ms", 0)
        }
        ts       = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        pub_path = _PUBLISHED_DIR / f"{ts}_{topic_object.get('topic_id', 'unknown')}.json"
        write_json(pub_path, published_record)

        end_time = datetime.now(timezone.utc).isoformat()
        state.update({
            "status":          "published",
            "facebook_post_id": publish_result.get("post_id"),
            "caption":         caption,
            "topic_id":        topic_object.get("topic_id"),
            "completed_at":    end_time
        })
        _log_workflow(workflow_id, state, "completed")

        send_alert(f"✅ Posted:\n{caption[:120]}")
        logger.info(ENGINE, f"=== WORKFLOW COMPLETE: {workflow_id} ===")
        return state

    else:
        reason = publish_result.get("reason", "unknown")
        state.update({"status": "failed", "failed_engine": "PublishingEngine", "reason": reason})
        _log_workflow(workflow_id, state, "failed")
        send_alert(f"🔴 Publish failed: {reason}")
        return state


# ─── Workflow: Generate Only (Termux testing) ─────────────────────────────────

def run_generate_workflow() -> dict:
    """Generate and write to /drafts/ — for local testing only."""
    topic_object    = generate_topic()
    if not topic_object:
        return {"status": "failed"}
    strategy_object = build_strategy(topic_object)
    visual_object   = build_visual_identity(strategy_object)
    prompt_object   = build_prompt(strategy_object, visual_object)
    result          = generate(prompt_object)

    if result.get("status") == "success":
        update_recent("category", topic_object.get("category", ""))
        update_recent("angle",    topic_object.get("angle", ""))
        update_recent("post_type", topic_object.get("post_type", ""))

    return {
        "status":          result.get("status"),
        "caption_preview": result.get("caption", "")[:100],
        "topic_id":        topic_object.get("topic_id")
    }


# ─── Workflow: Publish Only (Termux testing) ──────────────────────────────────

def run_publish_workflow() -> dict:
    """Publish next approved post — for local testing only."""
    from engines.publishing.publishing_engine import publish_next_approved
    result = publish_next_approved()
    return {"status": result.get("status"), "result": result}


# ─── Stats ────────────────────────────────────────────────────────────────────

def get_system_stats() -> dict:
    memory_stats    = get_stats()
    published_count = len(list(_PUBLISHED_DIR.glob("*.json")))
    draft_count     = len(list((_BASE / "drafts").glob("*.json")))
    approved_count  = len(list((_BASE / "approved").glob("*.json")))
    return {
        "drafts_waiting":   draft_count,
        "approved_waiting": approved_count,
        "total_published":  published_count,
        "memory":           memory_stats
    }
