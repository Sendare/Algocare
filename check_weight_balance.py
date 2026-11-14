import json
import sys
from pathlib import Path

from utils.course_branch_map import get_course_branch_map

if len(sys.argv) < 2:
    print("Usage: python check_weight_balance.py <program>  (e.g. nursing, midwifery)")
    sys.exit(1)
PROGRAM = sys.argv[1]

CURRICULUM_PATH = f"curricula/{PROGRAM}.json"
QUESTIONS_DIR = Path(f"data/{PROGRAM}/questions")
WEIGHTS_PATH = Path(f"config/{PROGRAM}/weights.json")

COURSE_BRANCH_MAP = get_course_branch_map(PROGRAM)


def slugify(text):
    import re
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def load_json(path, default):
    p = Path(path)
    if not p.exists():
        return default
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_topic_to_course_slug(curriculum):
    """topic_id -> course_slug, using the same branch-name-then-slugify logic
    build_pages.py uses, so course_slug here always matches what build_pages.py
    will actually key course_pools by."""
    lookup = {}
    for c in curriculum.get("curriculum", []):
        course_id = c.get("course_id")
        course_name = COURSE_BRANCH_MAP.get(course_id, c.get("course_name"))
        course_slug = slugify(course_name)
        for u in c.get("units", []):
            for t in u.get("topics", []):
                lookup[t["topic_id"]] = course_slug
    return lookup


def count_questions_per_course(topic_to_slug):
    """Reads every data/{program}/questions/{topic_id}.json file (the raw
    per-topic output from fetch_articles.py - NOT docs/.../course_pools/,
    since this should reflect real content regardless of whether
    build_pages.py has published it yet) and tallies question counts per
    course_slug."""
    counts = {}
    if not QUESTIONS_DIR.exists():
        return counts

    for q_file in QUESTIONS_DIR.glob("*.json"):
        topic_id = q_file.stem
        course_slug = topic_to_slug.get(topic_id)
        if course_slug is None:
            continue
        questions = load_json(q_file, [])
        counts[course_slug] = counts.get(course_slug, 0) + len(questions)

    return counts


def run():
    curriculum = load_json(CURRICULUM_PATH, {})
    if not curriculum:
        print(f"⚠️  Could not load {CURRICULUM_PATH}. Nothing to do.")
        return

    topic_to_slug = build_topic_to_course_slug(curriculum)
    counts = count_questions_per_course(topic_to_slug)

    weights_config = load_json(WEIGHTS_PATH, {"courses": {}, "units": {}})
    targets = weights_config.get("courses", {})
    excluded = set(weights_config.get("excluded_from_real_feel", []))

    if not targets:
        print(f"⚠️  No 'courses' targets found in {WEIGHTS_PATH}. Nothing to correct.")
        return

    corrected = {}
    report_rows = []

    for course_slug, target in targets.items():
        count = counts.get(course_slug, 0)
        if count == 0:
            print(f"⚠️  '{course_slug}' has a target weight but 0 generated questions "
                  f"found - leaving its weight unchanged this run (would divide by zero).")
            corrected[course_slug] = target
            continue
        corrected_weight = target / count
        corrected[course_slug] = round(corrected_weight, 4)
        report_rows.append((course_slug, target, count, corrected_weight))

    # Estimate realized share: each course's total probability mass is
    # corrected_weight * count (questions_of_that_course * per-question_weight).
    # Comparing that mass across courses shows whether the correction actually
    # restores the intended target ratio.
    total_mass = sum(w * counts.get(slug, 0) for slug, w in corrected.items() if slug in counts)
    total_target = sum(targets.values())

    print(f"Program: {PROGRAM}\n")
    print(f"{'Course':<32} {'Target':>8} {'Questions':>10} {'New Weight':>11} {'Target %':>9} {'Realized %':>11}")
    print("-" * 85)
    for course_slug, target, count, corrected_weight in sorted(report_rows, key=lambda r: -r[1]):
        mass = corrected_weight * count
        realized_pct = (mass / total_mass * 100) if total_mass else 0
        target_pct = (target / total_target * 100) if total_target else 0
        flag = "  ⚠️ not in curriculum" if course_slug not in counts else ""
        print(f"{course_slug:<32} {target:>8} {count:>10} {corrected_weight:>11.4f} "
              f"{target_pct:>8.1f}% {realized_pct:>10.1f}%{flag}")

    if excluded:
        print(f"\nExcluded from real-feel entirely ({len(excluded)}): {', '.join(sorted(excluded))}")

    zero_question_excluded = [c for c in excluded if counts.get(c, 0) == 0]
    unmapped_excluded = [c for c in excluded if c not in counts and c not in zero_question_excluded]

    weights_config["courses"] = corrected
    save_json(WEIGHTS_PATH, weights_config)
    print(f"\n✅ Wrote volume-corrected weights back to {WEIGHTS_PATH}")
    print("   (Target values above are now overwritten - re-run this after any")
    print("   major content regeneration, since question counts per course will shift.)")


if __name__ == "__main__":
    run()
