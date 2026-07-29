import json

FILE_PATH = "curriculum.json"
OUTPUT_PATH = "curriculum_normalized.json"

COURSE_BRANCH_MAP = {
    # Anatomy & Physiology
    "GNS111": "Anatomy and Physiology",
    "GNS121": "Anatomy and Physiology",
    "GNS211": "Anatomy and Physiology",

    # Foundation of Nursing
    "GNS112": "Foundation of Nursing",
    "GNS122": "Foundation of Nursing",
    "GNS212": "Foundation of Nursing",
    "GNS221": "Foundation of Nursing",

    # Nursing Informatics
    "GNS113": "Nursing Informatics",

    # Microbiology
    "GST114": "Microbiology",

    # Medical/Surgical Nursing
    "GNS123": "Medical Surgical Nursing",
    "GNS213": "Medical Surgical Nursing",
    "GNS222": "Medical Surgical Nursing",
    "GNS311": "Medical Surgical Nursing",
    "GNS321": "Medical Surgical Nursing",

    # Primary Health Care
    "GNS124": "Primary Health Care",
    "GNS214": "Primary Health Care",

    # Pharmacology
    "GNS125": "Pharmacology",
    "GNS215": "Pharmacology",
    "GNS223": "Pharmacology",

    # Reproductive Health
    "GNS216": "Reproductive Health",
    "GNS226": "Reproductive Health",
    "GNS312": "Reproductive Health",

    # Research & Statistics
    "GNS217": "Research and Statistics",
    "GNS224": "Research and Statistics",

    # Community Health Nursing
    "GNS225": "Community Health Nursing",
    "GNS313": "Community Health Nursing",

    # Nutrition
    "GNS227": "Nutrition and Dietetics",

    # Mental Health
    "GNS314": "Mental Health Nursing",

    # Emergency & Disaster
    "GNS315": "Emergency and Disaster Nursing",

    # Quality & Safety
    "GST319": "Quality Improvement and Patient Safety",

    # Home Healthcare
    "GNS324": "Home Healthcare Nursing",

    # Management & Teaching
    "GST321": "Management and Teaching",

    # Health Economics
    "GST322": "Health Economics",
}


def normalize_path(topic, course_id, course_name):
    """
    Returns a normalized path as a list, in one of three ways:
      1. String path "A > B > C" -> split into ["A", "B", "C"]
      2. Already a list -> returned as-is
      3. Missing/blank -> backfilled as [branch_name, topic_title]
    """
    path = topic.get("path")

    if isinstance(path, str) and path.strip():
        return [p.strip() for p in path.split(">")]

    if isinstance(path, list) and len(path) > 0:
        return path

    # Blank/missing path -> deterministic backfill using the branch map
    branch = COURSE_BRANCH_MAP.get(course_id, course_name)
    return [branch, topic.get("title", "Untitled")]


def normalize_all_paths(file_path, output_path):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    fixed_count = 0
    backfilled_count = 0
    unmapped_courses = set()

    for c in data.get("curriculum", []):
        course_id = c.get("course_id")
        course_name = c.get("course_name")

        if course_id not in COURSE_BRANCH_MAP:
            unmapped_courses.add(course_id)

        for u in c.get("units", []):
            for t in u.get("topics", []):
                original = t.get("path")
                t["path"] = normalize_path(t, course_id, course_name)

                if isinstance(original, str) and original.strip():
                    fixed_count += 1
                elif not original:
                    backfilled_count += 1

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✅ Normalized paths written to {output_path}")
    print(f"   • String paths converted to arrays : {fixed_count}")
    print(f"   • Blank paths backfilled            : {backfilled_count}")

    if unmapped_courses:
        print(f"\n⚠️  Warning: {len(unmapped_courses)} course_id(s) not found in COURSE_BRANCH_MAP:")
        for cid in sorted(unmapped_courses):
            print(f"   - {cid}")
        print("   (Their topics were backfilled using course_name as branch instead.)")


if __name__ == "__main__":
    normalize_all_paths(FILE_PATH, OUTPUT_PATH)

