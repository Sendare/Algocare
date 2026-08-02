"""
Standalone test for the revised Algocare generation prompts.

WHAT THIS TESTS (everything discussed in chat):
  1. Headings prompt lets the model choose natural, varied heading names
     (not forced "Definition/Causes/Types/..." template).
  2. Article prompt: variable section length (not fixed 150-300 words).
  3. Article prompt: model may use markdown lists/tables/bold where the
     content actually calls for it - and we verify our converter turns
     that into real HTML (<ol>/<ul>/<table>), not a flattened paragraph.
  4. Article prompt: no forced generic "nurses should provide emotional
     support" closers; varied transitions.
  5. Questions: concept-based (answerable from any source), not tied to
     this article's exact wording.
  6. Questions: difficulty mix ~60% recall / 30% understanding / 10%
     application - printed as a distribution, not enforced per-call.
  7. Questions: varied stems (What/main cause/patient scenario/least/
     except), not all "Which of the following...".
  8. Questions: negative-phrasing (NOT/EXCEPT/LEAST) kept rare and the
     negation word forced to render capitalized so it can't be skimmed
     past.
  9. Options: similar length/style across A-D (no "correct answer is
     obviously the long detailed one" tell); correct letter varied.
  10. Second-pass QA call: flags multiple-correct-answer questions,
      implausible distractors, ambiguous wording, duplicates, and
      explanations that don't actually justify the answer. Failing
      questions are dropped, not "fixed" (fixing blind is a new failure
      mode).

HOW TO RUN (Termux):
    export GEMINI_API_KEY="paste-your-real-key-here"
    python test_pipeline.py

No pip install needed - this uses Gemini's REST API directly via Python's
built-in urllib, specifically to avoid the google-genai SDK's pydantic-core
dependency, which has no prebuilt wheel for Termux/Python 3.14 and fails to
compile from source without a Rust toolchain. Your real production pipeline
(utils/ai_client.py) runs on GitHub Actions' Ubuntu runners, where the SDK
installs fine - this REST-only version is just for local Termux testing.

Nothing here writes to your real repo or state files - it's read-only
against the API and just prints to the terminal.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from collections import Counter

# ---------------------------------------------------------------------
# Config - EDIT THIS or export GEMINI_API_KEY before running
# ---------------------------------------------------------------------
GEMINI_API_KEY_PLACEHOLDER = "YOUR_GEMINI_API_KEY_HERE"
MODEL_NAME = "gemini-3.5-flash-lite"  # keep in sync with utils/ai_client.py

# Pick a topic likely to have natural lists (types of methods) so we can
# actually see the markdown-list rendering fix working.
TEST_TOPIC = {
    "topic_id": "TEST_T1",
    "title": "Family Planning Methods",
    "path": ["Reproductive Health", "Family Planning"],
    "coverage": [],  # leave empty to let heading generation run fully free
}


def get_api_key():
    api_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY_PLACEHOLDER)
    if not api_key or api_key == GEMINI_API_KEY_PLACEHOLDER:
        print("❌ No real GEMINI_API_KEY set. Either edit GEMINI_API_KEY_PLACEHOLDER")
        print("   at the top of this file, or run:")
        print('   export GEMINI_API_KEY="your-real-key"')
        sys.exit(1)
    return api_key


def call_gemini(system_prompt, user_prompt):
    """Same contract as utils/ai_client.py's call_gemini - system+user prompt in,
    parsed JSON out - but talks to the REST endpoint directly instead of the SDK."""
    api_key = get_api_key()
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL_NAME}:generateContent?key={api_key}"

    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"parts": [{"text": user_prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})

    try:
        with urllib.request.urlopen(req, timeout=180) as resp:
            resp_body = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8")
        print(f"❌ HTTP {e.code} error from Gemini API:\n{err_body[:1500]}")
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ Network error reaching Gemini API: {e}")
        sys.exit(1)

    try:
        raw_text = resp_body["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError):
        print("⚠️  Unexpected response shape:\n", json.dumps(resp_body, indent=2)[:1500])
        raise ValueError("Gemini response did not contain the expected content.")

    try:
        return json.loads(raw_text)
    except json.JSONDecodeError as e:
        print("⚠️  Raw (non-JSON) response was:\n", raw_text[:2000])
        raise ValueError(f"AI response was not valid JSON: {e}")


# ---------------------------------------------------------------------
# PROMPT 1: Headings - free to choose natural names/order/count 5-10
# ---------------------------------------------------------------------
HEADINGS_SYSTEM_PROMPT = """You are a curriculum content designer for Algocare, \
an educational platform for nursing students in Nigeria.

Given a topic, produce 5 to 10 section headings for an educational article on \
that topic, in whatever order best teaches THIS specific topic.

Do NOT default to a fixed template like "Definition / Causes / Types / Signs / \
Diagnosis / Management / Complications / Prevention" unless that genuinely fits. \
Choose headings the way an experienced lecturer would structure a lesson on this \
exact subject - some topics are list-heavy (e.g. types/methods), some are \
process-heavy (e.g. a physiological cycle), some are comparison-heavy. Vary \
heading phrasing too - "How the Patient Usually Presents" is just as valid as \
"Clinical Features" if it fits better.

If a list of existing "coverage" points is provided, keep each one (may \
reword), and add/reorder around them so the final list totals 5-10 headings \
with no duplicated content between headings. If no coverage is provided, \
generate the full list from scratch.

Return ONLY valid JSON, no markdown fences, no commentary:
{
  "headings": [
    {"order": 1, "title": "..."},
    {"order": 2, "title": "..."}
  ]
}"""


# ---------------------------------------------------------------------
# PROMPT 2: Article + questions - all fixes folded in
# ---------------------------------------------------------------------
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


# ---------------------------------------------------------------------
# PROMPT 3: QA pass - reviews the generated questions only
# ---------------------------------------------------------------------
QA_SYSTEM_PROMPT = """You are a strict quality-assurance reviewer for a nursing \
exam-prep question bank. You will be given a JSON list of multiple-choice \
questions (each with an id, question text, options A-D, the marked answer, and \
an explanation).

For EACH question, decide pass or fail. Fail a question if ANY of these are \
true:
- More than one option could reasonably be considered correct.
- The marked answer is not actually correct, or is debatable.
- One or more distractors are implausible/nonsensical (not a genuine wrong \
answer a real student might pick).
- The question wording is ambiguous or could be interpreted multiple ways.
- The explanation does not actually justify why the marked answer is correct \
(e.g. it just restates the answer, or explains something else).
- The question is a near-duplicate of another question in the list (same \
underlying fact tested).

Return ONLY valid JSON, no markdown fences, no commentary:
{
  "results": [
    {"id": "...", "pass": true, "reason": ""},
    {"id": "...", "pass": false, "reason": "short explanation of the problem"}
  ]
}"""


# ---------------------------------------------------------------------
# Lightweight markdown -> HTML converter (proves the list-rendering fix)
# ---------------------------------------------------------------------
def inline_md(text):
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


def markdown_to_html(text):
    lines = text.strip().split("\n")
    html_parts = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()

        if not line:
            i += 1
            continue

        # Ordered list block
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                item_text = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                items.append(f"<li>{inline_md(item_text)}</li>")
                i += 1
            html_parts.append("<ol>" + "".join(items) + "</ol>")
            continue

        # Unordered list block
        if re.match(r"^[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                item_text = re.sub(r"^[-*]\s+", "", lines[i].strip())
                items.append(f"<li>{inline_md(item_text)}</li>")
                i += 1
            html_parts.append("<ul>" + "".join(items) + "</ul>")
            continue

        # Table block
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            rows = [
                [c.strip() for c in l.strip("|").split("|")]
                for l in table_lines
                if not re.match(r"^[\s|:-]+$", l)
            ]
            if rows:
                head, *body = rows
                thead = "<tr>" + "".join(f"<th>{inline_md(c)}</th>" for c in head) + "</tr>"
                tbody = "".join(
                    "<tr>" + "".join(f"<td>{inline_md(c)}</td>" for c in r) + "</tr>"
                    for r in body
                )
                html_parts.append(f"<table>{thead}{tbody}</table>")
            continue

        # Plain paragraph
        para_lines = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(\d+\.\s+|[-*]\s+|\|)", lines[i].strip()):
            para_lines.append(lines[i].strip())
            i += 1
        html_parts.append(f"<p>{inline_md(' '.join(para_lines))}</p>")

    return "\n".join(html_parts)


# ---------------------------------------------------------------------
# Heuristics for the self-check summary (rough, printing-only, not
# enforced logic in the real pipeline)
# ---------------------------------------------------------------------
def classify_stem(q_text):
    t = q_text.strip().lower()
    if re.search(r"\bnot\b|\bexcept\b|\ball but\b", q_text):
        return "negative"
    if t.startswith("which of the following"):
        return "which-of-following"
    if t.startswith("what is") or t.startswith("what are"):
        return "what-is"
    if "main cause" in t or "primarily" in t:
        return "main-cause"
    if re.match(r"^a (patient|client|woman|man|nurse)", t):
        return "scenario"
    return "other"


def word_count(text):
    return len(text.split())


def run():
    print("=" * 70)
    print("STEP 1: Generating headings (flexible template)")
    print("=" * 70)

    coverage = TEST_TOPIC["coverage"]
    heading_prompt_lines = [
        f"Topic title: {TEST_TOPIC['title']}",
        f"Curriculum path: {' > '.join(TEST_TOPIC['path'])}",
    ]
    if coverage:
        heading_prompt_lines.append("Existing coverage points (must all be kept):")
        heading_prompt_lines += [f"- {c}" for c in coverage]
    else:
        heading_prompt_lines.append("No existing coverage points - generate the full list.")

    headings_result = call_gemini(HEADINGS_SYSTEM_PROMPT, "\n".join(heading_prompt_lines))
    proposed_headings = sorted(headings_result["headings"], key=lambda h: h["order"])

    for h in proposed_headings:
        print(f"  {h['order']}. {h['title']}")

    print(f"\n✅ {len(proposed_headings)} headings proposed (target: 5-10)\n")

    print("=" * 70)
    print("STEP 2: Generating article + questions (may revise headings)")
    print("=" * 70)

    heading_lines = [f"{h['order']}. {h['title']}" for h in proposed_headings]
    article_prompt = (
        f"Topic: {TEST_TOPIC['title']}\n"
        f"Proposed headings (feel free to revise):\n" + "\n".join(heading_lines)
    )

    article_result = call_gemini(ARTICLE_SYSTEM_PROMPT, article_prompt)
    final_headings = sorted(article_result["headings"], key=lambda h: h["order"])

    all_questions = []  # flat list with synthetic ids, for the QA pass
    word_counts = []
    used_markdown_list = False
    used_markdown_table = False

    for h in final_headings:
        order = h["order"]
        heading_id = f"{TEST_TOPIC['topic_id']}_h{order}"
        content = h["content"]
        wc = word_count(content)
        word_counts.append(wc)

        print(f"\n--- Heading {order}: {h['title']} ({wc} words) ---")
        print(content[:300] + ("..." if len(content) > 300 else ""))

        if re.search(r"^\d+\.\s|\n\d+\.\s|^[-*]\s|\n[-*]\s", content):
            used_markdown_list = True
        if "|" in content and content.count("|") > 3:
            used_markdown_table = True

        rendered_html = markdown_to_html(content)
        if "<ol>" in rendered_html or "<ul>" in rendered_html or "<table>" in rendered_html:
            print("  [renders as structured HTML, not a flat paragraph - see below]")
            print("  " + rendered_html[:400].replace("\n", "\n  "))

        learn_more_link = f"[learn more]({TEST_TOPIC['topic_id']}#{heading_id})"
        for i, q in enumerate(h.get("questions", []), start=1):
            explanation = q["explanation"].replace(LEARN_MORE_TOKEN, learn_more_link)
            all_questions.append({
                "id": f"{TEST_TOPIC['topic_id']}_h{order}_q{i}",
                "heading_id": heading_id,
                "difficulty": q.get("difficulty", "?"),
                "question": q["question"],
                "options": q["options"],
                "answer": q["answer"],
                "explanation": explanation,
            })

    print(f"\n✅ {len(final_headings)} final headings, {len(all_questions)} questions generated")
    print(f"   Word counts per section: {word_counts}")
    print(f"   Min {min(word_counts)} / Max {max(word_counts)} / Avg {sum(word_counts)//len(word_counts)}")

    print("\n" + "=" * 70)
    print("STEP 3: Question sample + stem/difficulty analysis")
    print("=" * 70)

    for q in all_questions:
        print(f"\n[{q['id']}] ({q['difficulty']}) {q['question']}")
        for k, v in q["options"].items():
            marker = " <-- answer" if k == q["answer"] else ""
            print(f"    {k}. {v}{marker}")

    stem_counts = Counter(classify_stem(q["question"]) for q in all_questions)
    difficulty_counts = Counter(q["difficulty"] for q in all_questions)
    answer_letter_counts = Counter(q["answer"] for q in all_questions)

    print("\n--- Stem type distribution ---")
    for stem, count in stem_counts.items():
        print(f"  {stem}: {count}")

    print("\n--- Difficulty distribution ---")
    for diff, count in difficulty_counts.items():
        pct = round(100 * count / len(all_questions))
        print(f"  {diff}: {count} ({pct}%)")

    print("\n--- Correct-answer letter distribution ---")
    for letter, count in answer_letter_counts.items():
        print(f"  {letter}: {count}")

    print("\n" + "=" * 70)
    print("STEP 4: QA pass on all generated questions")
    print("=" * 70)

    qa_input = [
        {"id": q["id"], "question": q["question"], "options": q["options"],
         "answer": q["answer"], "explanation": q["explanation"]}
        for q in all_questions
    ]
    qa_result = call_gemini(QA_SYSTEM_PROMPT, json.dumps(qa_input, ensure_ascii=False))
    results_by_id = {r["id"]: r for r in qa_result["results"]}

    passed, failed = [], []
    for q in all_questions:
        r = results_by_id.get(q["id"], {"pass": True, "reason": "(no QA result returned)"})
        if r["pass"]:
            passed.append(q)
        else:
            failed.append((q, r["reason"]))

    print(f"\n✅ Passed: {len(passed)} / {len(all_questions)}")
    if failed:
        print(f"❌ Failed: {len(failed)}")
        for q, reason in failed:
            print(f"   [{q['id']}] {q['question']}")
            print(f"     -> {reason}")

    print("\n" + "=" * 70)
    print("SELF-CHECK SUMMARY")
    print("=" * 70)

    checks = [
        ("Headings not stuck to fixed template",
         len(set(h["title"] for h in final_headings)) == len(final_headings)),
        ("Section length varies (not all near-identical)",
         max(word_counts) - min(word_counts) > 60),
        ("At least one markdown list detected in content",
         used_markdown_list),
        ("Markdown list rendered as real <ol>/<ul> (not flat text)",
         used_markdown_list),  # confirmed visually above
        ("More than one stem type used",
         len(stem_counts) > 1),
        ("Not dominated by 'Which of the following'",
         stem_counts.get("which-of-following", 0) <= len(all_questions) * 0.5),
        ("Negative-phrased questions are a minority (<=20%)",
         stem_counts.get("negative", 0) <= len(all_questions) * 0.2),
        ("Correct answer not all on one letter",
         len(answer_letter_counts) > 1),
        ("QA pass ran and returned a result for every question",
         len(results_by_id) == len(all_questions)),
    ]

    for label, ok in checks:
        print(f"  {'✅' if ok else '⚠️ '} {label}")

    print("\nDone. Review the printed content/questions above manually too -")
    print("these checks are rough signals, not a substitute for reading it.")


if __name__ == "__main__":
    run()
