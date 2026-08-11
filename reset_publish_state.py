"""
Phase 2 of the safe regeneration reset. Run this ONLY after fetch_articles.py
has fully caught up (articles_done count == headings_done count). This script
checks that for you and refuses to proceed if it's not true yet.

Resets build_state.json (so build_pages.py re-renders every page from the
fresh article content) and real_feel_state.json + deletes the old real-feel
test files (so exams rebuild from the new, letter-balanced question pool
instead of leaving stale old exams sitting alongside new ones).

Run from the repo root: python reset_publish_state.py
"""
import json
import shutil
from pathlib import Path

GEN_STATE_PATH = Path("state/midwifery/generation_state.json")
BUILD_STATE_PATH = Path("state/midwifery/build_state.json")
REAL_FEEL_STATE_PATH = Path("state/midwifery/real_feel_state.json")
REAL_FEEL_TESTS_DIR = Path("docs/midwifery/data/real_feel_tests")



def run():
    if not GEN_STATE_PATH.exists():
        print(f"❌ {GEN_STATE_PATH} not found - run this from the Algocare repo root.")
        return

    with open(GEN_STATE_PATH, "r", encoding="utf-8") as f:
        gen_state = json.load(f)

    headings_total = len(gen_state.get("headings_done", []))
    articles_done = len(gen_state.get("articles_done", []))

    if articles_done < headings_total:
        print(f"❌ Not ready yet: only {articles_done}/{headings_total} articles regenerated.")
        print("   Keep running fetch_articles.py until articles_done reaches")
        print("   headings_done, then run this script again.")
        return

    if BUILD_STATE_PATH.exists():
        with open(BUILD_STATE_PATH, "r", encoding="utf-8") as f:
            build_state = json.load(f)
    else:
        build_state = {}
    build_state["published_done"] = []
    with open(BUILD_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(build_state, f, indent=2, ensure_ascii=False)

    real_feel_state = {"used_question_ids": [], "tests_built": 0}
    with open(REAL_FEEL_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(real_feel_state, f, indent=2, ensure_ascii=False)

    if REAL_FEEL_TESTS_DIR.exists():
        shutil.rmtree(REAL_FEEL_TESTS_DIR)
        print(f"✅ Deleted {REAL_FEEL_TESTS_DIR} (old exams + stale index removed)")

    print(f"✅ All {articles_done}/{headings_total} articles regenerated.")
    print(f"✅ Reset {BUILD_STATE_PATH} (published_done cleared)")
    print(f"✅ Reset {REAL_FEEL_STATE_PATH} (used_question_ids + tests_built cleared)")
    print("\nNext build_pages.py run(s) will re-render every page from the fresh")
    print("content and rebuild real-feel exams from the new question pool.")
    print("This will take several hourly runs to fully catch up on 1517 pages.")


if __name__ == "__main__":
    run()
