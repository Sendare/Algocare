import json
import time
import sys
from pathlib import Path

from utils.ai_client import call_gemini

CURRICULUM_PATH = "curriculum.json"
HEADINGS_PATH = "data/topic_headings.json"
ARTICLES_DIR = "data/articles"
QUESTIONS_DIR = "data/questions"
STATE_PATH = "state/generation_state.json"

MAX_RUNTIME_SECONDS =  180 

   # 4.5 min hard stop - stays under the 5 min ceiling

# The AI never constructs the learn-more link itself - it just marks where one
# goes with this literal token, which the script replaces deterministically.
LEARN_MORE_TOKEN = "[[LEARN_MORE]]"

ARTICLE_SYSTEM_PROMPT = """You are an expert nursing educator writing study \
content for Algocare, an educational platform for nursing students in Nigeria.

You will be given a topic and its ordered list of section headings. For EACH \
heading, write:

1. "content": clear, accurate educational text (150-300 words) suitable for \
nursing students preparing for exams.

2. "questions": exactly 2 multiple-choice questions based ONLY on the content \
you just wrote for that heading (not on outside knowledge), so a student who \
read that heading could answer them.

Each question needs:
- "question": the question text
- "options": an object with keys A, B, C, D
- "answer": the correct option key (one of A/B/C/D)
- "explanation": 1-3 sentences in plain, student-friendly language explaining \
why that answer is correct. End every explanation with exactly this literal \
token on its own, with nothing after it: [[LEARN_MORE]]
  Do not attempt to write an actual link or heading reference yourself - the \
token is a placeholder that will be replaced programmatically.

Return ONLY valid JSON, no markdown fences, no commentary, in exactly this \
schema:
{
  "headings": [
    {
      "order": 1,
      "content": "...",
      "questions": [
        {"question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, "answer": "A", "explanation": "... [[LEARN_MORE]]"},
        {"question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, "answer": "B", "explanation": "... [[LEARN_MORE]]"}
      ]
    }
  ]
}"""


def load_json(path, default):
    p = Path(path)
    if not p.exists():
        return default
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_topic_lookup(curriculum):
    """topic_id -> {title, path} - needed here since topic_headings.json only
    stores headings/source, not the topic's title/path."""
    lookup = {}
    for c in curriculum.get("curriculum", []):
        for u in c.get("units", []):
            for t in u.get("topics", []):
                lookup[t.get("topic_id")] = {
                    "title": t.get("title"),
                    "path": t.get("path", []),
                }
    return lookup


def generate_article_and_questions(topic_id, headings_entry, topic_meta):
    """
    Calls Gemini ONCE for this topic, sending all its headings together, and
    gets back content + 2 MCQs per heading - generated from the same content,
    so the learn-more link always points to material that answers the question.

    Returns (article_dict, questions_list).
    """
    headings = headings_entry["headings"]  # [{heading_id, order, title}, ...]

    heading_lines = [f"{h['order']}. {h['title']}" for h in headings]
    user_prompt = (
        f"Topic: {topic_meta['title']}\n"
        f"Headings:\n" + "\n".join(heading_lines)
    )

    result = call_gemini(ARTICLE_SYSTEM_PROMPT, user_prompt)
    ai_headings = {h["order"]: h for h in result.get("headings", [])}

    article_headings = []
    questions_list = []

    for h in headings:
        order = h["order"]
        heading_id = h["heading_id"]
        ai_heading = ai_headings.get(order)

        if ai_heading is None:
            raise ValueError(f"AI response missing heading order {order} for {topic_id}")

        article_headings.append({
            "heading_id": heading_id,
            "order": order,
            "title": h["title"],
            "content": ai_heading["content"],
        })

        learn_more_link = f"[learn more]({topic_id}#{heading_id})"

        for i, q in enumerate(ai_heading.get("questions", []), start=1):
            explanation = q["explanation"].replace(LEARN_MORE_TOKEN, learn_more_link)
            questions_list.append({
                "question_id": f"{topic_id}_h{order}_q{i}",
                "heading_id": heading_id,
                "article_id": topic_id,
                "topic_id": topic_id,
                "question": q["question"],
                "options": q["options"],
                "answer": q["answer"],
                "explanation": explanation,
            })

    article_dict = {
        "article_id": topic_id,
        "topic_id": topic_id,
        "title": topic_meta["title"],
        "path": topic_meta["path"],
        "headings": article_headings,
    }

    return article_dict, questions_list


def run():
    start_time = time.time()

    curriculum = load_json(CURRICULUM_PATH, {})
    topic_lookup = build_topic_lookup(curriculum)

    headings_data = load_json(HEADINGS_PATH, {})
    state = load_json(STATE_PATH, {"headings_done": [], "articles_done": []})
    state.setdefault("headings_done", [])
    state.setdefault("articles_done", [])

    done_ids = set(state["articles_done"])
    # Only topics that already have headings ready are eligible for article generation
    eligible_ids = [tid for tid in headings_data.keys() if tid not in done_ids]

    print(f"Topics with headings ready : {len(headings_data)}")
    print(f"Articles already done      : {len(done_ids)}")
    print(f"Remaining                 : {len(eligible_ids)}")

    if not eligible_ids:
        print("✅ No eligible topics awaiting article generation. Nothing to do.")
        return

    processed_this_run = 0

    for topic_id in eligible_ids:
        elapsed = time.time() - start_time
        if elapsed > MAX_RUNTIME_SECONDS:
            print(f"⏱️  Time limit reached ({elapsed:.0f}s). Stopping gracefully.")
            break

        topic_meta = topic_lookup.get(topic_id)
        if topic_meta is None:
            print(f"⚠️  {topic_id} not found in curriculum.json. Skipping.")
            continue

        try:
            article, questions = generate_article_and_questions(
                topic_id, headings_data[topic_id], topic_meta
            )
        except Exception as e:
            print(f"⚠️  Failed on {topic_id}: {e}. Skipping for this run.")
            continue

        # Save article + questions immediately - not batched
        save_json(f"{ARTICLES_DIR}/{topic_id}.json", article)
        save_json(f"{QUESTIONS_DIR}/{topic_id}.json", questions)

        # Save state immediately - not batched
        state["articles_done"].append(topic_id)
        save_json(STATE_PATH, state)

        processed_this_run += 1
        print(f"✅ [{processed_this_run}] {topic_id} - article + questions saved.")

    print(f"\n🏁 Run complete. Processed {processed_this_run} topic(s) this run.")
    print(f"   Total done: {len(state['articles_done'])}/{len(headings_data)}")


if __name__ == "__main__":
    run()
