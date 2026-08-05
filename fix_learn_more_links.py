"""
Repairs the "[learn more](...)" link in every saved question's explanation.
The engagement rewrite pass wasn't instructed to preserve this exact
markdown snippet, so it was likely dropped or garbled for most rewritten
questions. This reconstructs the correct link deterministically from each
question's own topic_id/heading_id (both already stored) - no API calls,
free, safe to re-run anytime.

Run from the repo root: python fix_learn_more_links.py
"""
import json
import re
from pathlib import Path

QUESTIONS_DIR = Path("data/questions")

# Matches a trailing markdown link, correct or broken, if present
LEARN_MORE_PATTERN = re.compile(r"\s*\[[^\]]*\]\([^)]*\)\s*$")


def run():
    if not QUESTIONS_DIR.exists():
        print(f"❌ {QUESTIONS_DIR} not found - run this from the Algocare repo root.")
        return

    total_count = 0
    fixed_count = 0
    skipped_missing_ids = 0

    for qfile in sorted(QUESTIONS_DIR.glob("*.json")):
        try:
            questions = json.loads(qfile.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"⚠️  Skipping {qfile.name} - couldn't parse: {e}")
            continue

        file_changed = False
        for q in questions:
            total_count += 1
            topic_id = q.get("topic_id")
            heading_id = q.get("heading_id")
            if not topic_id or not heading_id:
                skipped_missing_ids += 1
                continue

            correct_link = f"[learn more]({topic_id}#{heading_id})"
            explanation = q.get("explanation", "")
            stripped = LEARN_MORE_PATTERN.sub("", explanation).rstrip()
            new_explanation = f"{stripped} {correct_link}"

            if new_explanation != explanation:
                q["explanation"] = new_explanation
                fixed_count += 1
                file_changed = True

        if file_changed:
            qfile.write_text(json.dumps(questions, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Total questions checked : {total_count}")
    print(f"Fixed                   : {fixed_count}")
    if skipped_missing_ids:
        print(f"⚠️  Skipped (missing topic_id/heading_id): {skipped_missing_ids}")
    print("\nNext: reset real_feel_state.json and rebuild pages so the fix")
    print("reaches docs/data/questions and the real-feel exams too.")


if __name__ == "__main__":
    run()
