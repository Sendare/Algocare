import json
import random
import time
import sys
from pathlib import Path

from utils.ai_client import call_gemini

CURRICULUM_PATH = "curriculum.json"
HEADINGS_PATH = "data/topic_headings.json"
ARTICLES_DIR = "data/articles"
QUESTIONS_DIR = "data/questions"
STATE_PATH = "state/generation_state.json"

MAX_RUNTIME_SECONDS = 180    # 4.5 min hard stop - stays under the 5 min ceiling

# The AI never constructs the learn-more link itself - it just marks where one
# goes with this literal token, which the script replaces deterministically.
LEARN_MORE_TOKEN = "[[LEARN_MORE]]"

ARTICLE_SYSTEM_PROMPT = """You are an experienced nursing lecturer writing study \
content for Algocare, an educational platform for nursing students in Nigeria \

You will be given a topic and a proposed list of section headings. You may use \
these headings as-is, OR revise them: rename, reorder, merge, split, add, or \
remove headings if that produces a better lesson on this specific topic. Return \
5 to 10 final headings either way.

For EACH final heading, write:

1. "content": Write only as much as the heading naturally requires. Most \
sections will be 80-350 words - a simple definition might be short, a \
management section might be longer. Do not make every section a similar \
length. Vary sentence length and rhythm. Avoid repetitive transitions like \
"However," "In addition," "nurses should" "student nurses" "Furthermore," "It is important to..." appearing in \
almost every section. Do not end every section with a generic closer like \
"nurses should provide emotional support" or "patient education is essential" \
unless it's specifically relevant to THIS heading's content.

Choose the format that best teaches the concept - not everything needs to be a \
paragraph:
- If the heading is naturally a list (types, methods, causes, steps), write it \
as an actual markdown list: "1. **Name**: description" for ordered, or \
"- **Name**: description" for unordered.
- Use **bold** for key terms.
- Use a markdown table (| col | col |) only if comparing multiple items across \
the same attributes.
- Otherwise, write clear prose.

Include practical clinical/exam-relevant observations where genuinely relevant \
(a common misconception) - but \
don't force one into every heading if it doesn't fit naturally. Only mention \
scientific uncertainty if it genuinely exists for this specific fact - do not \
manufacture hedging language on settled topics.

2. "questions": exactly 2 multiple-choice questions per heading that test the \
underlying nursing CONCEPT that heading covers - not the specific wording of \
the paragraph you just wrote. A student who studied this same concept from a \
different textbook or article should still be able to answer correctly.

Question difficulty mix across the whole set (not necessarily each heading): \
roughly 65% straightforward recall, 30% basic understanding/reasoning, 5% \
simple application (e.g. "a patient with X is most likely to..."). Avoid \
narrow, obscure drug-specific edge-case recall (e.g. rare side effects of a \
single named drug) for recall-tier questions - keep those approachable so \
beginners aren't discouraged from daily practice. Questions should be exciting so any student will feel curious and happy to answer.

Vary question stems - do NOT start every question with "Which of the \
following...". Mix in: "What is...", "The main cause of X is...", "A patient \
with [scenario] is most likely to...", "Which symptom is most characteristic \
of...", etc.

You may occasionally (roughly 2 in 10 questions, not more) use a \
negative-framed question (NOT / EXCEPT / all BUT one). When you do, the \
negation word MUST appear in full capitals in the question text itself (e.g. \
"Which of the following is NOT a symptom of...") so it can't be skimmed past.

For every question:
- "difficulty": one of "recall", "understanding", "application"
- "question": the question text
- "options": an object with keys A, B, C, D - make all four options similar in \
length and grammatical structure. Do NOT make the correct option noticeably \
longer, more detailed, or more hedged than the distractors - that's a giveaway. \
Vary which letter (A/B/C/D) is correct across different questions; don't \
cluster correct answers on the same letter.
- "answer": the correct option key
- "explanation": 1-3 sentences, plain student-friendly language, explaining WHY \
that answer is correct (not just restating it). End every explanation with \
exactly this literal token on its own, nothing after it: [[LEARN_MORE]]
  Do not write an actual link yourself - the token is replaced programmatically.

Return ONLY valid JSON, no markdown fences, no commentary, in exactly this \
schema:
{
  "headings": [
    {
      "order": 1,
      "title": "...",
      "content": "...",
      "questions": [
        {"difficulty": "recall", "question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, "answer": "A", "explanation": "... [[LEARN_MORE]]"},
        {"difficulty": "understanding", "question": "...", "options": {"A": "...", "B": "...", "C": "...", "D": "..."}, "answer": "B", "explanation": "... [[LEARN_MORE]]"}
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


def shuffle_options(question):
    """
    Randomizes which letter (A-D) holds the correct answer. The AI is
    instructed to vary this itself, but reliably does not (observed ~80%
    clustering on one letter in testing) - this guarantees an even
    distribution regardless of what the model does, tracking the correct
    option by its original key (not its text) to avoid any risk of
    mismatching two options that happen to have identical wording.
    """
    keys = ["A", "B", "C", "D"]
    entries = [(k, question["options"][k], k == question["answer"]) for k in keys]
    random.shuffle(entries)

    new_options = {}
    new_answer = None
    for new_key, (_orig_key, value, is_correct) in zip(keys, entries):
        new_options[new_key] = value
        if is_correct:
            new_answer = new_key

    question["options"] = new_options
    question["answer"] = new_answer
    return question


def generate_article_and_questions(topic_id, headings_entry, topic_meta):
    """
    Calls Gemini ONCE for this topic, sending the proposed headings, and gets
    back a FINAL set of headings (which may differ from the proposal) plus
    content + 2 MCQs per heading. Heading IDs are derived fresh from the
    final order returned here - not from the original headings_entry - since
    the model is free to rename/reorder/add/remove headings.

    Returns (article_dict, questions_list).
    """
    proposed_headings = sorted(headings_entry["headings"], key=lambda h: h["order"])
    heading_lines = [f"{h['order']}. {h['title']}" for h in proposed_headings]
    user_prompt = (
        f"Topic: {topic_meta['title']}\n"
        f"Proposed headings (feel free to revise - rename, reorder, merge, "
        f"split, add, or remove as needed):\n" + "\n".join(heading_lines)
    )

    result = call_gemini(ARTICLE_SYSTEM_PROMPT, user_prompt)
    final_headings = sorted(result.get("headings", []), key=lambda h: h["order"])

    if not (5 <= len(final_headings) <= 10):
        raise ValueError(f"Expected 5-10 final headings, got {len(final_headings)} for {topic_id}")

    article_headings = []
    questions_list = []

    for h in final_headings:
        order = h["order"]
        heading_id = f"{topic_id}_h{order}"

        article_headings.append({
            "heading_id": heading_id,
            "order": order,
            "title": h["title"],
            "content": h["content"],
        })

        learn_more_link = f"[learn more]({topic_id}#{heading_id})"

        for i, q in enumerate(h.get("questions", []), start=1):
            explanation = q["explanation"].replace(LEARN_MORE_TOKEN, learn_more_link)
            question_obj = {
                "question_id": f"{topic_id}_h{order}_q{i}",
                "heading_id": heading_id,
                "article_id": topic_id,
                "topic_id": topic_id,
                "difficulty": q.get("difficulty", "recall"),
                "question": q["question"],
                "options": q["options"],
                "answer": q["answer"],
                "explanation": explanation,
            }
            questions_list.append(shuffle_options(question_obj))

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

        # Save article + questions immediately - not batched. This overwrites
        # any previous version of this topic's files, which is intentional
        # during a full regeneration pass.
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

