import json
import time
import sys
from pathlib import Path

from utils.ai_client import call_gemini

CURRICULUM_PATH = "curriculum.json"
HEADINGS_PATH = "data/topic_headings.json"
STATE_PATH = "state/generation_state.json"

MAX_RUNTIME_SECONDS = 240    # 4.5 min hard stop - stays under the 5 min ceiling

HEADINGS_SYSTEM_PROMPT = """You are a curriculum content designer for Algocare, \
an educational platform for nursing students in Nigeria.

Given a topic, produce a final list of 5 to 10 section headings for an \
educational article on that topic, ordered in a logical teaching sequence \
(e.g. definition -> underlying concepts -> types/classification -> causes -> \
assessment -> management -> complications - adjust order to fit what actually \
suits this specific topic).

If a list of existing "coverage" points is provided, treat them as a required \
foundation: keep each one (you may rephrase for clarity), do not drop any, and \
add or reorder additional headings around them so the FINAL combined list \
totals between 5 and 10 headings with no duplicated content between headings.

If no coverage is provided, generate the full list from scratch.

Return ONLY valid JSON, with no markdown fences and no commentary, in exactly \
this schema:
{
  "headings": [
    {"order": 1, "title": "..."},
    {"order": 2, "title": "..."}
  ]
}"""


def load_json(path, default):
    p = Path(path)
    if not p.exists():
        return default
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_all_topics(curriculum):
    topics = []
    for c in curriculum.get("curriculum", []):
        for u in c.get("units", []):
            for t in u.get("topics", []):
                topics.append({
                    "topic_id": t.get("topic_id"),
                    "title": t.get("title"),
                    "path": t.get("path"),
                    "coverage": t.get("coverage", []),
                })
    return topics


def generate_headings_for_topic(topic):
    """
    Calls Gemini to produce 5-10 section headings for this topic.

    Returns:
      {
        "headings": [{"heading_id": ..., "order": ..., "title": ...}, ...],
        "source": "coverage_augmented" | "ai_generated"
      }
    """
    coverage = topic.get("coverage") or []
    path_str = " > ".join(topic.get("path", [])) if topic.get("path") else ""

    user_prompt_lines = [
        f"Topic title: {topic.get('title')}",
        f"Curriculum path: {path_str}",
    ]
    if coverage:
        user_prompt_lines.append(
            "Existing coverage points (must all be kept, reworded if needed):"
        )
        for point in coverage:
            user_prompt_lines.append(f"- {point}")
    else:
        user_prompt_lines.append("No existing coverage points - generate the full list.")

    user_prompt = "\n".join(user_prompt_lines)

    result = call_gemini(HEADINGS_SYSTEM_PROMPT, user_prompt)

    headings = result.get("headings", [])
    if not (5 <= len(headings) <= 10):
        raise ValueError(f"Expected 5-10 headings, got {len(headings)}")

    topic_id = topic["topic_id"]
    formatted_headings = []
    for h in sorted(headings, key=lambda x: x["order"]):
        order = h["order"]
        formatted_headings.append({
            "heading_id": f"{topic_id}_h{order}",
            "order": order,
            "title": h["title"],
        })

    return {
        "headings": formatted_headings,
        "source": "coverage_augmented" if coverage else "ai_generated",
    }


def run():
    start_time = time.time()

    curriculum = load_json(CURRICULUM_PATH, {})
    headings_data = load_json(HEADINGS_PATH, {})
    state = load_json(STATE_PATH, {"headings_done": [], "articles_done": []})
    state.setdefault("headings_done", [])
    state.setdefault("articles_done", [])

    all_topics = get_all_topics(curriculum)
    done_ids = set(state["headings_done"])
    remaining = [t for t in all_topics if t["topic_id"] not in done_ids]

    print(f"Total topics : {len(all_topics)}")
    print(f"Already done : {len(done_ids)}")
    print(f"Remaining    : {len(remaining)}")

    if not remaining:
        print("✅ All topics already have headings. Nothing to do.")
        return

    processed_this_run = 0

    for topic in remaining:
        elapsed = time.time() - start_time
        if elapsed > MAX_RUNTIME_SECONDS:
            print(f"⏱️  Time limit reached ({elapsed:.0f}s). Stopping gracefully.")
            break

        topic_id = topic["topic_id"]

        try:
            result = generate_headings_for_topic(topic)
        except NotImplementedError as e:
            print(f"❌ {e}")
            sys.exit(1)
        except Exception as e:
            print(f"⚠️  Failed on {topic_id}: {e}. Skipping for this run.")
            continue

        # Save output immediately - not batched
        headings_data[topic_id] = result
        save_json(HEADINGS_PATH, headings_data)

        # Save state immediately - not batched
        state["headings_done"].append(topic_id)
        save_json(STATE_PATH, state)

        processed_this_run += 1
        print(f"✅ [{processed_this_run}] {topic_id} - headings saved.")

    print(f"\n🏁 Run complete. Processed {processed_this_run} topic(s) this run.")
    print(f"   Total done: {len(state['headings_done'])}/{len(all_topics)}")


if __name__ == "__main__":
    run()
