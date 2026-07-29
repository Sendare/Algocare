import json

FILE_PATH = "curriculum.json"


def inspect_curriculum(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ File not found at {file_path}")
        return
    except json.JSONDecodeError as e:
        print(
            f"❌ JSON Syntax Error (File might still be truncated or malformed):\n   {e}"
        )
        return

    meta = data.get("meta", {})
    curriculum = data.get("curriculum", [])

    print("============== CURRICULUM INSPECTION REPORT ==============")
    print(f"\n--- 📌 METADATA ---")
    print(f"• Target Date       : {meta.get('target_date', 'N/A')}")
    print(f"• Declared Topics   : {meta.get('total_topics', 'N/A')}")

    print(
        f"\n--- 📚 COURSES OVERVIEW ({len(curriculum)} Courses Found) ---"
    )

    grand_total_units = 0
    grand_total_topics = 0
    topic_types = set()

    for course in curriculum:
        c_id = course.get("course_id", "N/A")
        c_name = course.get("course_name", "N/A")
        group = course.get("group", "Unassigned")
        units = course.get("units", [])

        grand_total_units += len(units)
        course_topic_count = sum(len(u.get("topics", [])) for u in units)
        grand_total_topics += course_topic_count

        for u in units:
            for t in u.get("topics", []):
                if "topic_type" in t:
                    topic_types.add(t["topic_type"])

        print(
            f"[{c_id:<7}] {c_name:<35} | Group: {group:<12} | Units: {len(units):>2} | Topics: {course_topic_count:>3}"
        )

    print(f"\n--- ⚙️ SUMMARY ---")
    print(f"• Total Units  : {grand_total_units}")
    print(f"• Total Topics : {grand_total_topics}")
    print(f"• Topic Types  : {list(topic_types)}")
    print("==========================================================")


inspect_curriculum(FILE_PATH)
