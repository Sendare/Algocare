"""
Phase 1 of the safe regeneration reset. Run this FIRST, once.

Clears state/generation_state.json's articles_done list so every topic
becomes eligible for fresh article+question generation, while leaving
headings_done untouched (headings are not being regenerated).

Run from the repo root: python reset_articles_state.py
"""
import json
from pathlib import Path

STATE_PATH = Path("state/generation_state.json")


def run():
    if not STATE_PATH.exists():
        print(f"❌ {STATE_PATH} not found - run this from the Algocare repo root.")
        return

    with open(STATE_PATH, "r", encoding="utf-8") as f:
        state = json.load(f)

    headings_done = state.get("headings_done", [])
    old_articles_done = state.get("articles_done", [])

    state["articles_done"] = []

    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    print(f"✅ Reset {STATE_PATH}")
    print(f"   headings_done kept as-is : {len(headings_done)} topics")
    print(f"   articles_done cleared    : was {len(old_articles_done)}, now 0")
    print(f"\nAll {len(headings_done)} topics are now eligible for article+question regeneration.")
    print("Let fetch_articles.py run until articles_done reaches the same count as")
    print("headings_done. Do NOT run reset_publish_state.py until then - it will")
    print("refuse to proceed early anyway, but don't reset build_state.json or")
    print("real_feel_state.json by hand in the meantime.")


if __name__ == "__main__":
    run()
