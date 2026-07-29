from collections import Counter
import json

FILE_PATH = "curriculum.json"


def inspect_full_structure(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return

    print(
        "==============================================================="
    )
    print(
        "            FULL CURRICULUM SCHEMA & TOPOLOGY INSPECTOR        "
    )
    print(
        "===============================================================\n"
    )

    # 1. ROOT
    print("1️⃣  ROOT STRUCTURE")
    print(f"   Root Keys Present: {list(data.keys())}")

    # 2. METADATA
    print("\n2️⃣  METADATA NODE (`meta`)")
    meta = data.get("meta", {})
    for k, v in meta.items():
        print(f"   • {k:<16}: ({type(v).__name__}) {v}")

    # 3. COURSES
    courses = data.get("curriculum", [])
    print(f"\n3️⃣  COURSES LEVEL ({len(courses)} Courses)")

    course_keys = set()
    groups = Counter()
    priorities = Counter()

    for c in courses:
        course_keys.update(c.keys())
        if "group" in c:
            groups[c["group"]] += 1
        if "priority" in c:
            priorities[c["priority"]] += 1

    print(f"   Course Object Keys: {list(course_keys)}")
    print(f"   Groups Found      : {dict(groups)}")
    print(f"   Priorities Found  : {dict(priorities)}")

    # 4. UNITS
    print("\n4️⃣  UNITS LEVEL")
    unit_keys = set()
    total_units = 0

    for c in courses:
        for u in c.get("units", []):
            total_units += 1
            unit_keys.update(u.keys())

    print(f"   Total Units Analyzed: {total_units}")
    print(f"   Unit Object Keys    : {list(unit_keys)}")

    # 5. TOPICS & FIELD FREQUENCY
    print("\n5️⃣  TOPICS LEVEL & FIELD DISCOVERY")
    topic_key_counts = Counter()
    topic_types = Counter()
    total_topics = 0
    path_count = 0
    coverage_count = 0

    for c in courses:
        for u in c.get("units", []):
            for t in u.get("topics", []):
                total_topics += 1
                topic_key_counts.update(t.keys())

                if "topic_type" in t:
                    topic_types[t["topic_type"]] += 1
                if "path" in t:
                    path_count += 1
                if "coverage" in t:
                    coverage_count += 1

    print(f"   Total Topics Analyzed: {total_topics}\n")
    print("   Field Frequency across Topics:")
    for k, count in topic_key_counts.items():
        pct = (count / total_topics) * 100
        req = "Required (100%)" if count == total_topics else f"Optional ({pct:.1f}%)"
        print(f"   • {k:<16}: Present in {count}/{total_topics} [{req}]")

    print("\n   Optional Array Fields:")
    print(
        f"   • path      : Present in {path_count}/{total_topics} topics"
    )
    print(
        f"   • coverage  : Present in {coverage_count}/{total_topics} topics"
    )

    # 6. TAXONOMY DISTRIBUTION
    print("\n6️⃣  TOPIC TYPE TAXONOMY DISTRIBUTION (Top 10)")
    for t_type, count in topic_types.most_common(10):
        print(f"   • {t_type:<25}: {count}")

    print(
        "\n==============================================================="
    )


inspect_full_structure(FILE_PATH)


