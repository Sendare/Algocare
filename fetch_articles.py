import json
import random
import re
import time
import sys
from pathlib import Path

from utils.ai_client import call_gemini

if len(sys.argv) < 2:
    print("Usage: python fetch_articles.py <program>  (e.g. nursing, midwifery)")
    sys.exit(1)
PROGRAM = sys.argv[1]

CURRICULUM_PATH = f"curricula/{PROGRAM}.json"
HEADINGS_PATH = f"data/{PROGRAM}/topic_headings.json"
ARTICLES_DIR = f"data/{PROGRAM}/articles"
QUESTIONS_DIR = f"data/{PROGRAM}/questions"
STATE_PATH = f"state/{PROGRAM}/generation_state.json"

# 3 Gemini calls per topic (article/questions, engagement, QA) - each topic
# takes roughly 3x as long as a single-call pipeline, so fewer topics
# complete per run. Bumped from 180s for headroom under the 6-min workflow
# timeout.
MAX_RUNTIME_SECONDS = 240

LEARN_MORE_TOKEN = "[[LEARN_MORE]]"

ARTICLE_SYSTEM_PROMPT = """You are an experienced nursing lecturer writing study \
content for Algocare, an educational platform for nursing students in Nigeria \
preparing for the NMCN CBT exam.

You will be given a topic and a proposed list of section headings. You may use \
these headings as-is, OR revise them: rename, reorder, merge, split, add, or \
remove headings if that produces a better lesson on this specific topic. Return \
5 to 10 final headings either way.

For EACH final heading, write:

1. "content": Write only as much as the heading naturally requires. Most \
sections will be 80-350 words - a simple definition might be short, a \
management section might be longer. Do not make every section a similar \
length. Vary sentence length and rhythm. Avoid repetitive transitions like \
"However," "In addition," "Furthermore," "It is important to..." appearing in \
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
(a common misconception, an exam pitfall, a Nigerian clinical context) - but \
don't force one into every heading if it doesn't fit naturally. Only mention \
scientific uncertainty if it genuinely exists for this specific fact - do not \
manufacture hedging language on settled topics.

2. "questions": exactly 2 multiple-choice questions per heading that test the \
underlying nursing CONCEPT that heading covers - not the specific wording of \
the paragraph you just wrote. A student who studied this same concept from a \
different textbook or article should still be able to answer correctly.

Question difficulty mix across the whole set (not necessarily each heading): \
roughly 60% straightforward recall, 30% basic understanding/reasoning, 10% \
simple application (e.g. "a patient with X is most likely to..."). Avoid \
narrow, obscure drug-specific edge-case recall (e.g. rare side effects of a \
single named drug) for recall-tier questions - keep those approachable so \
beginners aren't discouraged from daily practice.

CRITICAL - keep the LANGUAGE simple regardless of difficulty tier: write \
every question and option in the same plain, direct language a Nigerian \
nursing lecturer uses quizzing students out loud in class - NOT the dense \
phrasing of a research journal or postgraduate exam. "Difficulty" should \
come from WHAT is being asked, never from how complicated the sentence is. \
Avoid unnecessary technical/Latin vocabulary beyond terms already used and \
explained in the article content itself. Avoid convoluted comparative \
phrasing like "Why is X considered Y rather than Z" - prefer short, concrete \
phrasing.

Examples of rewriting an overly academic question into an appropriately \
simple one:
- Too hard: "What mechanism directly causes polyuria in a patient with \
uncontrolled hyperglycemia?" -> Better: "Why does a patient with very high \
blood sugar urinate more often?"
- Too hard: "How do the antioxidants found naturally in fresh fruits \
primarily protect human cells?" -> Better: "How do antioxidants in fruit \
help protect the body's cells?"
- Too hard: "Why is controlling considered a feedback loop rather than \
merely a punitive measure?" -> Better: "Why is 'controlling' in management \
more about improvement than punishment?"

If a stem runs longer than about 20 words, or uses a word a first-year \
student wouldn't say out loud, simplify it.

Vary question stems - do NOT start every question with "Which of the \
following...". Mix in: "What is...", "The main cause of X is...", "A patient \
with [scenario] is most likely to...", "Which symptom is most characteristic \
of...", etc.

You may occasionally (roughly 1 in 10 questions, not more) use a \
negative-framed question (NOT / EXCEPT / all BUT one). When you do, the \
negation word MUST appear in full capitals in the question text itself (e.g. \
"Which of the following is NOT a symptom of...") so it can't be skimmed past.

For every question:
- "difficulty": one of "recall", "understanding", "application"
- "question": the question text
- "options": an array of exactly 4 option strings, in any order - do NOT \
label them A/B/C/D yourself, that is assigned programmatically afterward. \
Make all four similar in length and grammatical structure. Do NOT make the \
correct option noticeably longer, more detailed, or more hedged than the \
others - that's a giveaway.
- "answer": the correct option, copied EXACTLY (character-for-character) from \
one of the 4 strings in "options" above - not a letter, not a paraphrase, the \
literal matching text. This is verified programmatically, so it must match \
one option exactly.
- "explanation": 1-3 sentences, plain student-friendly language, explaining WHY \
that answer is correct (not just restating it). Do not refer to option \
letters (A/B/C/D) anywhere in the explanation - letters don't exist yet at \
generation time and are assigned after. End every explanation with exactly \
this literal token on its own, nothing after it: [[LEARN_MORE]]
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
        {"difficulty": "recall", "question": "...", "options": ["...", "...", "...", "..."], "answer": "...", "explanation": "... [[LEARN_MORE]]"},
        {"difficulty": "understanding", "question": "...", "options": ["...", "...", "...", "..."], "answer": "...", "explanation": "... [[LEARN_MORE]]"}
      ]
    }
  ]
}"""


ENGAGEMENT_SYSTEM_PROMPT = """You are a product-focused nursing education \
writer for Algocare, a CBT practice app used daily by nursing students in \
Nigeria on their phones.

Your business goal: students should WANT to open this app and answer \
questions every single day, the way they'd check a habit-tracking app - not \
dread it. A student who feels stupid or overwhelmed will quit and never come \
back; a student who feels "I can do this, and I'm learning" will return daily. \
Give students what makes them WANT to keep coming back, not what a \
postgraduate exam board would consider rigorous.

You will receive a list of already-written multiple-choice questions (each \
with an id, the question text, 4 options, which one is correct, and its \
explanation).

For EACH question, decide: would a first-year Nigerian nursing student, \
studying casually on their phone between classes, find this approachable and \
feel good attempting it - even if they get it wrong? Rewrite the question if \
ANY of these are true:
- It uses dense/academic vocabulary beyond plain spoken classroom language
- The stem is long, convoluted, or hard to read on a small phone screen
- Getting it wrong would feel demoralizing rather than like a normal part of \
learning
- The explanation doesn't teach warmly - it should feel like a patient \
tutor, not a textbook

When rewriting, you MUST preserve exactly: the underlying nursing concept \
being tested, and which fact is correct. Never change what's true - only how \
it's said.

For every question return:
- "id": the same id you were given
- "needs_rewrite": true or false
- "question": the (possibly rewritten) question text
- "options": the (possibly rewritten) 4 options as an array, in any order
- "answer": the correct option, copied EXACTLY from one of the 4 "options" \
strings
- "explanation": the (possibly rewritten) explanation - warm, encouraging, \
plain language
- "approachability_score": your honest estimate, 1-5, of how confident and \
motivated a first-year student would feel attempting this (5 = very \
approachable, 1 = intimidating)

Return ONLY valid JSON, no markdown fences, no commentary:
{"questions": [{"id": "...", "needs_rewrite": true, "question": "...", "options": ["...","...","...","..."], "answer": "...", "explanation": "...", "approachability_score": 4}]}"""


QA_SYSTEM_PROMPT = """You are a strict quality-assurance reviewer for a nursing \
exam-prep question bank. You will be given a JSON list of multiple-choice \
questions (each with an id, question text, options A-D, the marked answer, and \
an explanation).

For EACH question, actually work through whether the marked answer is \
correct YOURSELF first - reason about the underlying nursing fact before \
deciding anything. Write that reasoning down BEFORE you decide pass or fail, \
not after - if you decide first and reason afterward, you can end up \
reasoning your way to the right answer too late to change a verdict you \
already committed to.

Fail a question if, after your own reasoning, ANY of these are true: more \
than one option could be correct, the marked answer is wrong or debatable, a \
distractor is implausible/nonsensical, the wording is ambiguous, the \
explanation doesn't actually justify the answer, or it's a near-duplicate of \
another question in the list.

Return ONLY valid JSON, no markdown fences, no commentary. Write "reasoning" \
BEFORE "pass" for every question, in this exact field order:
{
  "results": [
    {"id": "...", "reasoning": "brief step-by-step check of whether the marked answer is actually correct, done BEFORE deciding", "pass": true, "reason": ""},
    {"id": "...", "reasoning": "...", "pass": false, "reason": "one clear sentence summarizing the problem"}
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


def _normalize(text):
    """Whitespace/case-insensitive comparison, so a trivial formatting
    difference doesn't cause a false mismatch - the displayed text still
    uses the original, un-normalized string from the options list."""
    return " ".join(str(text).strip().split()).lower()


def finalize_options(raw_options, raw_answer):
    """
    Takes an unlabeled 4-option array + the stated answer TEXT, verifies the
    answer matches exactly one option, then shuffles and assigns A-D itself -
    so letter position is never something the model has to get right, and
    can never carry over an internal inconsistency undetected.

    Returns (options_dict, answer_letter) on success, or None if the answer
    text didn't match exactly one option.
    """
    if not isinstance(raw_options, list) or len(raw_options) != 4:
        return None

    normalized_answer = _normalize(raw_answer)
    matches = [opt for opt in raw_options if _normalize(opt) == normalized_answer]
    if len(matches) != 1:
        return None

    shuffled = raw_options[:]
    random.shuffle(shuffled)

    letters = ["A", "B", "C", "D"]
    options_dict = {}
    answer_letter = None
    for letter, opt in zip(letters, shuffled):
        options_dict[letter] = opt
        if _normalize(opt) == normalized_answer:
            answer_letter = letter

    return options_dict, answer_letter


def generate_article_and_questions(topic_id, headings_entry, topic_meta):
    """
    Calls Gemini for this topic, sending the proposed headings, and gets
    back a FINAL set of headings (which may differ from the proposal) plus
    content + 2 MCQs per heading. Heading IDs are derived fresh from the
    final order returned here.

    Returns (article_dict, questions_list, skipped_count) - questions_list
    at this point has only been through text-match verification, not yet
    the engagement or QA passes.
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
    skipped_count = 0

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
            finalized = finalize_options(q.get("options", []), q.get("answer", ""))
            if finalized is None:
                skipped_count += 1
                print(f"   ⚠️  Skipped malformed question ({topic_id} h{order} q{i}): "
                      f"answer text didn't match exactly one option.")
                continue

            options_dict, answer_letter = finalized
            explanation = q["explanation"].replace(LEARN_MORE_TOKEN, learn_more_link)

            questions_list.append({
                "question_id": f"{topic_id}_h{order}_q{i}",
                "heading_id": heading_id,
                "article_id": topic_id,
                "topic_id": topic_id,
                "difficulty": q.get("difficulty", "recall"),
                "question": q["question"],
                "options": options_dict,
                "answer": answer_letter,
                "explanation": explanation,
            })

    article_dict = {
        "article_id": topic_id,
        "topic_id": topic_id,
        "title": topic_meta["title"],
        "path": topic_meta["path"],
        "headings": article_headings,
    }

    return article_dict, questions_list, skipped_count


LEARN_MORE_PATTERN = re.compile(r"\s*\[[^\]]*\]\([^)]*\)\s*$")


def run_engagement_pass(questions_list):
    """
    Sends this topic's questions through a dedicated approachability rewrite
    pass - kept separate from correctness, since 'make it friendlier' and
    'is this factually right' are different jobs. Modifies questions_list
    in place. Returns (rewritten_count, skipped_bad_rewrite_count).

    The trailing "[learn more](...)" link is stripped out before sending the
    explanation to the model, and the correct link (reconstructed from
    topic_id/heading_id, never trusted from the model) is always reattached
    to whatever comes back - the model never sees it, so it can't lose it.
    """
    if not questions_list:
        return 0, 0

    input_list = []
    for q in questions_list:
        stripped_explanation = LEARN_MORE_PATTERN.sub("", q["explanation"]).rstrip()
        input_list.append({
            "id": q["question_id"],
            "question": q["question"],
            "options": list(q["options"].values()),
            "correct_answer_text": q["options"][q["answer"]],
            "explanation": stripped_explanation,
        })

    try:
        result = call_gemini(ENGAGEMENT_SYSTEM_PROMPT, json.dumps(input_list, ensure_ascii=False))
    except Exception as e:
        print(f"   ⚠️  Engagement pass failed ({e}). Keeping original questions for this topic.")
        return 0, 0

    by_id = {r["id"]: r for r in result.get("questions", [])}

    rewritten_count = 0
    skipped_bad_rewrite = 0

    for q in questions_list:
        r = by_id.get(q["question_id"])
        if r is None or not r.get("needs_rewrite"):
            continue

        finalized = finalize_options(r.get("options", []), r.get("answer", ""))
        if finalized is None:
            skipped_bad_rewrite += 1
            continue  # keep the original question unchanged if the rewrite's answer doesn't verify

        options_dict, answer_letter = finalized
        rewritten_explanation = LEARN_MORE_PATTERN.sub("", r["explanation"]).rstrip()
        correct_link = f"[learn more]({q['topic_id']}#{q['heading_id']})"

        q["question"] = r["question"]
        q["options"] = options_dict
        q["answer"] = answer_letter
        q["explanation"] = f"{rewritten_explanation} {correct_link}"
        rewritten_count += 1

    return rewritten_count, skipped_bad_rewrite


def run_qa_pass(questions_list):
    """
    Sends this topic's questions through correctness QA. Returns a NEW list
    containing only the questions that passed, plus the drop count. Failing
    questions are dropped, not "fixed" - an unverified fix is a new failure
    mode, not a correction.
    """
    if not questions_list:
        return questions_list, 0

    qa_input = [
        {"id": q["question_id"], "question": q["question"], "options": q["options"],
         "answer": q["answer"], "explanation": q["explanation"]}
        for q in questions_list
    ]

    try:
        result = call_gemini(QA_SYSTEM_PROMPT, json.dumps(qa_input, ensure_ascii=False))
    except Exception as e:
        print(f"   ⚠️  QA pass failed ({e}). Keeping all questions unverified for this topic.")
        return questions_list, 0

    results_by_id = {r["id"]: r for r in result.get("results", [])}

    passed_questions = []
    dropped_count = 0
    for q in questions_list:
        r = results_by_id.get(q["question_id"])
        if r is None or r.get("pass", True):
            passed_questions.append(q)
        else:
            dropped_count += 1
            print(f"   ⚠️  QA dropped ({q['question_id']}): {r.get('reason', 'no reason given')}")

    return passed_questions, dropped_count


def run():
    start_time = time.time()

    curriculum = load_json(CURRICULUM_PATH, {})
    topic_lookup = build_topic_lookup(curriculum)

    headings_data = load_json(HEADINGS_PATH, {})
    state = load_json(STATE_PATH, {"headings_done": [], "articles_done": []})
    state.setdefault("headings_done", [])
    state.setdefault("articles_done", [])

    done_ids = set(state["articles_done"])
    eligible_ids = [tid for tid in headings_data.keys() if tid not in done_ids]

    print(f"Program                    : {PROGRAM}")
    print(f"Topics with headings ready : {len(headings_data)}")
    print(f"Articles already done      : {len(done_ids)}")
    print(f"Remaining                 : {len(eligible_ids)}")

    if not eligible_ids:
        print("✅ No eligible topics awaiting article generation. Nothing to do.")
        return

    processed_this_run = 0
    total_skipped_verification = 0
    total_rewritten = 0
    total_qa_dropped = 0

    for topic_id in eligible_ids:
        elapsed = time.time() - start_time
        if elapsed > MAX_RUNTIME_SECONDS:
            print(f"⏱️  Time limit reached ({elapsed:.0f}s). Stopping gracefully.")
            break

        topic_meta = topic_lookup.get(topic_id)
        if topic_meta is None:
            print(f"⚠️  {topic_id} not found in curriculum. Skipping.")
            continue

        try:
            article, questions, skipped = generate_article_and_questions(
                topic_id, headings_data[topic_id], topic_meta
            )
        except Exception as e:
            print(f"⚠️  Failed on {topic_id}: {e}. Skipping for this run.")
            continue

        rewritten, skipped_rewrite = run_engagement_pass(questions)
        questions, qa_dropped = run_qa_pass(questions)

        total_skipped_verification += skipped + skipped_rewrite
        total_rewritten += rewritten
        total_qa_dropped += qa_dropped

        save_json(f"{ARTICLES_DIR}/{topic_id}.json", article)
        save_json(f"{QUESTIONS_DIR}/{topic_id}.json", questions)

        state["articles_done"].append(topic_id)
        save_json(STATE_PATH, state)

        processed_this_run += 1
        print(f"✅ [{processed_this_run}] {topic_id} - {len(questions)} question(s) saved "
              f"(rewritten: {rewritten}, QA dropped: {qa_dropped}).")

    print(f"\n🏁 Run complete. Processed {processed_this_run} topic(s) this run.")
    print(f"   Total done: {len(state['articles_done'])}/{len(headings_data)}")
    print(f"   Rewritten for approachability: {total_rewritten}")
    print(f"   Dropped (failed verification or QA): {total_skipped_verification + total_qa_dropped}")


if __name__ == "__main__":
    run()
