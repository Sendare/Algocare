import json

FILE_PATH = "curriculum.json"


def inspect_tree_and_paths(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Error loading JSON: {e}")
        return

    curriculum = data.get("curriculum", [])

    print(
        "==============================================================="
    )
    print(
        "         CURRICULUM TREE & PATH HIERARCHY INSPECTOR            "
    )
    print(
        "===============================================================\n"
    )

    topics_with_paths = 0
    max_path_depth = 0
    unique_paths = set()
    total_topics = 0

    for c in curriculum:
        for u in c.get("units", []):
            for t in u.get("topics", []):
                total_topics += 1
                path_arr = t.get("path")
                if isinstance(path_arr, list) and len(path_arr) > 0:
                    topics_with_paths += 1
                    max_path_depth = max(max_path_depth, len(path_arr))
                    unique_paths.add(tuple(path_arr))

    print("1️⃣  `path` ARRAY STATS")
    print(
        f"   • Topics with `path` defined : {topics_with_paths} / {total_topics}"
    )
    print(f"   • Max `path` Depth           : {max_path_depth} steps")
    print(f"   • Unique Trajectories        : {len(unique_paths)}")

    print("\n2️⃣  SAMPLE VISUAL TREE MAP (First Course, First Unit)")
    print(
        "───────────────────────────────────────────────────────────────"
    )

    if curriculum:
        c = curriculum[0]
        print(f"📚 [{c.get('course_id')}] {c.get('course_name')}")
        units = c.get("units", [])
        if units:
            u = units[0]
            print(f"  └── 📖 Unit {u.get('unit_number')}: {u.get('unit_name')}")
            for t in u.get("topics", [])[:3]:
                path_str = (
                    f" (Path: {' > '.join(t['path'])})" if "path" in t else ""
                )
                print(f"      ├── 🔹 [{t.get('topic_id')}] {t.get('title')}{path_str}")
                if "coverage" in t:
                    for cov in t["coverage"][:2]:
                        print(f"      │   └── ▫️ {cov}")


inspect_tree_and_paths(FILE_PATH)
