"""
ENGINE 8 — ORCHESTRATOR ENGINE
Coordinates structural data transit between Topic, Strategy, Visual, Prompt, 
AI Generation, and Publishing components. Decoupled to push data records instantly.
"""

import sys
import uuid
from pathlib import Path
from datetime import datetime, timezone

# Resolve project root dynamically to guarantee cross-module cross-imports function cleanly
_ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(_ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(_ROOT_DIR))

import utils.logger as logger
from utils.file_store import write_json, read_json
from utils.telegram_alert import send_alert

# ─── REAL FILENAME MATCHING IMPORTS ──────────────────────────────────────────
from engines.topic_intelligence.topic_engine import generate_topic
from engines.content_strategy.strategy_engine import build_strategy
from engines.visual_identity.visual_engine import build_visual_identity
from engines.prompt_orchestration.prompt_engine import build_prompt
from engines.ai_generation.generation_engine import generate
from engines.publishing.publishing_engine import publish_caption, queue_comments
from engines.memory.memory_engine import record_combination, update_recent

ENGINE = "Orchestrator"
_BASE = Path(__file__).resolve().parent.parent.parent
_PUBLISHED_DIR = _BASE / "published"
_HISTORY_FILE = _BASE / "logs" / "workflow_history.json"

def _make_workflow_id() -> str:
    return f"WF_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"

def _log_workflow(workflow_id: str, state_data: dict, status: str):
    """Saves workflow status records directly into the history logs."""
    try:
        history_path = Path(_HISTORY_FILE)
        history_path.parent.mkdir(parents=True, exist_ok=True)
        history = read_json(history_path) or {}
        history[workflow_id] = state_data
        write_json(history_path, history)
    except Exception as e:
        logger.error(ENGINE, f"Failed to record state profile payload: {e}")

def run_auto_workflow() -> dict:
    """
    Full automation pipeline used by GitHub Actions.
    Engine 1 → 2 → 6 → 3 → 4 → publish → memory update → Queue injection.
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

    # Bundle only the text message caption for the immediate Meta post run
    publishing_payload = {
        "caption": caption,
        "comments": []
    }

    # ── Engine 7: Publish Main Post
    logger.info(ENGINE, "Engine 7: Publishing Main Caption")
    publish_result = publish_caption(publishing_payload)

    if publish_result.get("success"):
        # Save memory logs immediately to stay updated with Git pushes
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

        # Archive published profile configuration
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
        _PUBLISHED_DIR.mkdir(parents=True, exist_ok=True)
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
        send_alert(f"✅ Published main content successfully. Logs committed.")

        # ─── INJECT REMAINING ENGAGEMENT STRINGS INTO ZERO-SLEEP STORAGE FILE
        if comments:
            logger.info(ENGINE, "Injecting interaction content into backend queue flat file...")
            queue_comments(publish_result.get("post_id"), comments)

        logger.info(ENGINE, f"=== WORKFLOW COMPLETE: {workflow_id} ===")
        return state

    else:
        reason = publish_result.get("reason", "unknown")
        state.update({"status": "failed", "failed_engine": "PublishingEngine", "reason": reason})
        _log_workflow(workflow_id, state, "failed")
        send_alert(f"🔴 Publish failed: {reason}")
        return state


def run_manual_workflow() -> dict:
    """Fallback structural draft generation used for local testing pipelines."""
    logger.info(ENGINE, "Running manual staging sequence (Draft generation only)...")
    return {"status": "staged"}
