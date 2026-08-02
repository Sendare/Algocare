"""
Standalone test for the plain-language fix to the article/question prompt.

Tests across 3 topics deliberately chosen to mirror the exact patterns that
came back "too hard" in production:
  1. A physiology/mechanism topic (like the polyuria/hyperglycemia example)
  2. A nutrition topic (like the antioxidants example)
  3. A management topic (like the convoluted "controlling" example)

Also runs everything from earlier testing: heading flexibility, variable
section length, markdown list rendering, concept-based questions, difficulty
mix, stem variety, negative-question limits, balanced option length/letter,
text-match answer verification, and the QA pass.

NEW in this version: a heuristic flag for long stems (>20 words) or
"rather than"-style convoluted comparisons - content-agnostic checks, not a
real judgment of readability. Flagged questions are printed in full at the
end so you can read them yourself - this is a spotting tool, not a verdict.

HOW TO RUN (Termux):
    export GEMINI_API_KEY="paste-your-real-key-here"
    python test_pipeline.py

Uses Gemini's REST API directly via urllib - no pip install needed. Nothing
here writes to your real repo or state files.
"""

import json
import os
import re
import sys
import urllib.request
import urllib.error
from collections import Counter

GEMINI_API_KEY_PLACEHOLDER = "YOUR_GEMINI_API_KEY_HERE"
MODEL_NAME = "gemini-3.5-flash-lite"  # keep in sync with utils/ai_client.py

# 3 topics chosen to directly re-test the exact failure patterns flagged:
TEST_TOPICS = [
    {
        "topic_id": "TEST_T1",
        "title": "Diabetes Mellitus: Pathophysiology and Nursing Management",
        "path": ["Medical Surgical Nursing", "Endocrine Disorders"],
        "coverage": [],
    },
    {
        "topic_id": "TEST_T2",
        "title": "Micronutrients: Vitamins, Minerals, and Antioxidants",
        "path": ["Nutrition and Dietetics", "Micronutrients"],
        "coverage": [],
    },
    {
        "topic_id": "TEST_T3",
        "title": "Principles of Management: Planning, Organizing, and Controlling",
        "path": ["Management and Teaching", "Management Functions"],
        "coverage": [],
    },
]


def get_api_key():
    api_key = os.environ.get("GEMINI_API_KEY", GEMINI_API_KEY_PLACEHOLDER)
    if not api_key or api_key == GEMINI_API_KEY_PLACEHOLDER:
        print("❌ No real GEMINI_API_KEY set. Either edit GEMINI_API_KEY_PLACEHOLDER")
        print("   at the top of this file, or run:")
        print('   export GEMINI_API_KEY="your-real-key"')
        sys.exit(1)
    return api_key


def call_gemini(system_prompt, user_prompt):
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


HEADINGS_SYSTEM_PROMPT = """You are a curriculum content designer for Algocare, \
an educational platform for nursing students in Nigeria.

Given a topic, produce 5 to 10 section headings for an educational article on \
that topic, in whatever order best teaches THIS specific topic.

Do NOT default to a fixed template like "Definition / Causes / Types / Signs / \
Diagnosis / Management / Complications / Prevention" unless that genuinely fits. \
Choose headings the way an experienced lecturer would structure a lesson on this \
exact subject.

If a list of existing "coverage" points is provided, keep each one (may \
reword), and add/reorder around them so the final list totals 5-10 headings. \
If no coverage is provided, generate the full list from scratch.

Return ONLY valid JSON, no markdown fences, no commentary:
{
  "headings": [
    {"order": 1, "title": "..."},
    {"order": 2, "title": "..."}
  ]
}"""


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
sections will be 80-350 words. Do not make every section a similar length. \
Vary sentence length and rhythm. Avoid repetitive transitions like "However," \
"In addition," "Furthermore," "It is important to..." appearing in almost \
every section. Do not end every section with a generic closer like "nurses \
should provide emotional support" unless specifically relevant.

Choose the format that best teaches the concept:
- If the heading is naturally a list, write it as a markdown list: \
"1. **Name**: description" for ordered, or "- **Name**: description" for \
unordered.
- Use **bold** for key terms.
- Use a markdown table (| col | col |) only for comparing multiple items \
across the same attributes.
- Otherwise, write clear prose.

Include practical clinical/exam-relevant observations where genuinely \
relevant - but don't force one into every heading. Only mention scientific \
uncertainty if it genuinely exists for this specific fact.

2. "questions": exactly 2 multiple-choice questions per heading that test the \
underlying nursing CONCEPT that heading covers - not the specific wording of \
the paragraph you just wrote. A student who studied this same concept from a \
different textbook or article should still be able to answer correctly.

Question difficulty mix across the whole set: roughly 60% straightforward \
recall, 30% basic understanding/reasoning, 10% simple application. Avoid \
narrow, obscure drug-specific edge-case recall for recall-tier questions.

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
negation word MUST appear in full capitals in the question text itself.

For every question:
- "difficulty": one of "recall", "understanding", "application"
- "question": the question text
- "options": an array of exactly 4 option strings, in any order - do NOT \
label them A/B/C/D. Make all four similar in length and grammatical \
structure. Do NOT make the correct option noticeably longer or more \
detailed than the others.
- "answer": the correct option, copied EXACTLY (character-for-character) \
from one of the 4 strings in "options" above - not a letter, the literal \
matching text.
- "explanation": 1-3 sentences, plain student-friendly language, explaining \
WHY that answer is correct. Do not refer to option letters. End every \
explanation with exactly this literal token on its own: [[LEARN_MORE]]

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


QA_SYSTEM_PROMPT = """You are a strict quality-assurance reviewer for a nursing \
exam-prep question bank. You will be given a JSON list of multiple-choice \
questions (each with an id, question text, options A-D, the marked answer, and \
an explanation).

For EACH question, decide pass or fail. Fail a question if ANY of these are \
true: more than one option could be correct, the marked answer is wrong or \
debatable, a distractor is implausible/nonsensical, the wording is ambiguous, \
the explanation doesn't actually justify the answer, or it's a near-duplicate \
of another question in the list.

Return ONLY valid JSON, no markdown fences, no commentary:
{
  "results": [
    {"id": "...", "pass": true, "reason": ""},
    {"id": "...", "pass": false, "reason": "short explanation"}
  ]
}"""


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
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(f"<li>{inline_md(re.sub(r'^\\d+\\.\\s+', '', lines[i].strip()))}</li>")
                i += 1
            html_parts.append("<ol>" + "".join(items) + "</ol>")
            continue
        if re.match(r"^[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(f"<li>{inline_md(re.sub(r'^[-*]\\s+', '', lines[i].strip()))}</li>")
                i += 1
            html_parts.append("<ul>" + "".join(items) + "</ul>")
            continue
        para_lines = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(\d+\.\s+|[-*]\s+|\|)", lines[i].strip()):
            para_lines.append(lines[i].strip())
            i += 1
        html_parts.append(f"<p>{inline_md(' '.join(para_lines))}</p>")
    return "\n".join(html_parts)


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


def safe_preview(content):
    """Terminal-friendly preview. A raw markdown table row can be a single
    150-200+ character unbroken line - some mobile terminals (Termux
    included) visibly lag trying to wrap/redraw that on a narrow screen.
    This never prints a raw table line - just the intro text plus a row
    count, with the actual rendering still verified separately below."""
    lines = content.split("\n")
    table_row_count = sum(1 for l in lines if l.strip().startswith("|"))

    if table_row_count > 0:
        intro_lines = []
        for l in lines:
            if l.strip().startswith("|"):
                break
            intro_lines.append(l)
        intro = " ".join(intro_lines).strip()
        preview = intro[:200] + ("..." if len(intro) > 200 else "")
        return f"{preview}\n  [table with {table_row_count} row(s) follows - not printed raw to avoid terminal lag]"

    return content[:250] + ("..." if len(content) > 250 else "")


def flag_complexity_issues(question_text):
    """Content-agnostic heuristics only - NOT a real readability judgment.
    Flags the two specific patterns called out: long stems and 'rather than'
    style convoluted comparisons. Use this to find candidates to read, not
    as a verdict."""
    issues = []
    wc = word_count(question_text)
    if wc > 20:
        issues.append(f"long stem ({wc} words)")
    if re.search(r"\brather than\b", question_text, re.IGNORECASE):
        issues.append("convoluted 'rather than' comparison")
    return issues


def generate_for_topic(topic):
    print(f"\n{'='*70}\nTOPIC: {topic['title']}\n{'='*70}")

    heading_prompt_lines = [
        f"Topic title: {topic['title']}",
        f"Curriculum path: {' > '.join(topic['path'])}",
        "No existing coverage points - generate the full list.",
    ]
    headings_result = call_gemini(HEADINGS_SYSTEM_PROMPT, "\n".join(heading_prompt_lines))
    proposed_headings = sorted(headings_result["headings"], key=lambda h: h["order"])
    for h in proposed_headings:
        print(f"  {h['order']}. {h['title']}")

    heading_lines = [f"{h['order']}. {h['title']}" for h in proposed_headings]
    article_prompt = (
        f"Topic: {topic['title']}\n"
        f"Proposed headings (feel free to revise):\n" + "\n".join(heading_lines)
    )
    article_result = call_gemini(ARTICLE_SYSTEM_PROMPT, article_prompt)
    final_headings = sorted(article_result["headings"], key=lambda h: h["order"])

    topic_questions = []
    word_counts = []

    for h in final_headings:
        order = h["order"]
        heading_id = f"{topic['topic_id']}_h{order}"
        content = h["content"]
        wc = word_count(content)
        word_counts.append(wc)

        print(f"\n--- Heading {order}: {h['title']} ({wc} words) ---")
        print(safe_preview(content))

        rendered_html = markdown_to_html(content)
        if "<ol>" in rendered_html or "<ul>" in rendered_html:
            print("  [renders as a real list, not flat text]")
        if "<table>" in rendered_html:
            print("  [table renders correctly as real <table> HTML]")

        learn_more_link = f"[learn more]({topic['topic_id']}#{heading_id})"
        for i, q in enumerate(h.get("questions", []), start=1):
            raw_options = q.get("options", [])
            raw_answer = q.get("answer", "")
            normalized_answer = " ".join(str(raw_answer).strip().split()).lower()
            matches = [o for o in raw_options if " ".join(str(o).strip().split()).lower() == normalized_answer]
            if len(matches) != 1:
                print(f"   ⚠️  SKIPPED (answer text matched {len(matches)} options, expected 1): {q.get('question')}")
                continue

            import random as _random
            shuffled = raw_options[:]
            _random.shuffle(shuffled)
            letters = ["A", "B", "C", "D"]
            options_dict = {}
            answer_letter = None
            for letter, opt in zip(letters, shuffled):
                options_dict[letter] = opt
                if " ".join(str(opt).strip().split()).lower() == normalized_answer:
                    answer_letter = letter

            explanation = q["explanation"].replace(LEARN_MORE_TOKEN, learn_more_link)
            topic_questions.append({
                "id": f"{topic['topic_id']}_h{order}_q{i}",
                "topic": topic["title"],
                "difficulty": q.get("difficulty", "?"),
                "question": q["question"],
                "options": options_dict,
                "answer": answer_letter,
                "explanation": explanation,
            })

    print(f"\n✅ {len(final_headings)} headings, {len(topic_questions)} valid questions, "
          f"word counts {word_counts} (min {min(word_counts)}/max {max(word_counts)})")

    return topic_questions


def run():
    all_questions = []
    for topic in TEST_TOPICS:
        all_questions.extend(generate_for_topic(topic))

    print(f"\n{'='*70}\nCOMBINED ANALYSIS ({len(all_questions)} questions across {len(TEST_TOPICS)} topics)\n{'='*70}")

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

    print(f"\n{'='*70}\nCOMPLEXITY CHECK - flagged questions (read these yourself)\n{'='*70}")
    flagged = []
    for q in all_questions:
        issues = flag_complexity_issues(q["question"])
        if issues:
            flagged.append((q, issues))

    if not flagged:
        print("None flagged by the heuristic (long stem / 'rather than' phrasing).")
        print("Still worth reading a few questions above yourself to judge tone.")
    else:
        for q, issues in flagged:
            print(f"\n[{q['id']}] ({', '.join(issues)}) — topic: {q['topic']}")
            print(f"  {q['question']}")

    print(f"\n{'='*70}\nQA PASS\n{'='*70}")
    qa_input = [
        {"id": q["id"], "question": q["question"], "options": q["options"],
         "answer": q["answer"], "explanation": q["explanation"]}
        for q in all_questions
    ]
    qa_result = call_gemini(QA_SYSTEM_PROMPT, json.dumps(qa_input, ensure_ascii=False))
    results_by_id = {r["id"]: r for r in qa_result["results"]}

    passed = sum(1 for q in all_questions if results_by_id.get(q["id"], {}).get("pass", True))
    print(f"\n✅ Passed: {passed} / {len(all_questions)}")
    for q in all_questions:
        r = results_by_id.get(q["id"])
        if r and not r["pass"]:
            print(f"   [{q['id']}] {q['question']}\n     -> {r['reason']}")

    print(f"\n{'='*70}\nSUMMARY\n{'='*70}")
    print(f"  Total questions: {len(all_questions)}")
    print(f"  Flagged for complexity review: {len(flagged)} ({round(100*len(flagged)/len(all_questions))}%)")
    print(f"  QA pass rate: {passed}/{len(all_questions)}")
    print("\nRead the flagged questions above (if any) and a sample of the")
    print("unflagged ones too - this heuristic catches length/phrasing patterns")
    print("only, not actual jargon density. Your own read is the real test.")


if __name__ == "__main__":
    run()
