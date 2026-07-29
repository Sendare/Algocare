import json


class CurriculumEngine:

    def __init__(self, file_path="curriculum.json"):
        with open(file_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)
        self.curriculum = self.data.get("curriculum", [])

    # 1. FETCH BY EXACT IDs
    def get_course(self, course_id):
        """Fetch a specific course by ID (e.g., 'GNS111')"""
        for c in self.curriculum:
            if c.get("course_id").upper() == course_id.upper():
                return c
        return None

    def get_unit(self, course_id, unit_number):
        """Fetch a specific unit by course ID and unit number"""
        course = self.get_course(course_id)
        if course:
            for u in course.get("units", []):
                if u.get("unit_number") == unit_number:
                    return u
        return None

    def get_topic(self, topic_id):
        """Fetch a topic directly by its ID (e.g., 'GNS111_U1_T1')"""
        for c in self.curriculum:
            for u in c.get("units", []):
                for t in u.get("topics", []):
                    if t.get("topic_id") == topic_id:
                        return t
        return None

    # 2. SEARCH BY KEYWORD (Title, Coverage, or Path)
    def search_topics(self, keyword):
        """Search across all 2,021 topics for a matching keyword"""
        results = []
        kw = keyword.lower()
        for c in self.curriculum:
            for u in c.get("units", []):
                for t in u.get("topics", []):
                    title_match = kw in t.get("title", "").lower()
                    path_match = any(
                        kw in p.lower() for p in t.get("path", [])
                    )
                    cov_match = any(
                        kw in cov.lower() for cov in t.get("coverage", [])
                    )

                    if title_match or path_match or cov_match:
                        results.append(
                            {
                                "course_id": c.get("course_id"),
                                "unit_number": u.get("unit_number"),
                                "topic_id": t.get("topic_id"),
                                "title": t.get("title"),
                                "topic_type": t.get("topic_type"),
                                "path": t.get("path", []),
                                "coverage": t.get("coverage", []),
                            }
                        )
        return results

    # 3. FILTER BY TAXONOMY (topic_type)
    def get_topics_by_type(self, topic_type):
        """Extract all topics matching a type (e.g., 'drug', 'procedure', 'organ')"""
        results = []
        for c in self.curriculum:
            for u in c.get("units", []):
                for t in u.get("topics", []):
                    if t.get("topic_type") == topic_type:
                        results.append(
                            {
                                "course_id": c.get("course_id"),
                                "topic_id": t.get("topic_id"),
                                "title": t.get("title"),
                            }
                        )
        return results

    # 4. FLAT EXPORT FOR DB/VECTOR SEARCH
    def flatten_all_topics(self):
        """Flattens all 2,021 topics into standard key-value records for indexing or DB ingestion"""
        flat_list = []
        for c in self.curriculum:
            for u in c.get("units", []):
                for t in u.get("topics", []):
                    flat_list.append(
                        {
                            "course_id": c.get("course_id"),
                            "course_name": c.get("course_name"),
                            "group": c.get("group"),
                            "unit_number": u.get("unit_number"),
                            "unit_name": u.get("unit_name"),
                            "topic_id": t.get("topic_id"),
                            "order": t.get("order", None),
                            "title": t.get("title"),
                            "topic_type": t.get("topic_type"),
                            "path": t.get("path", []),
                            "coverage": t.get("coverage", []),
                        }
                    )
        return flat_list


# --- EXAMPLES OF HOW AN AI / BACKEND CALLS THIS ---
if __name__ == "__main__":
    engine = CurriculumEngine("curriculum.json")

    print("--- 1. Fetch Topic by ID ---")
    topic = engine.get_topic("GNS111_U1_T1")
    print(f"Result: {topic}\n")

    print("--- 2. Search Keyword 'Infection' ---")
    search_results = engine.search_topics("Infection")
    print(f"Found {len(search_results)} matching topics across curriculum.")
    for res in search_results[:3]:  # Print first 3 matches
        print(f" • [{res['course_id']}] {res['title']} ({res['topic_type']})")

    print("\n--- 3. Fetch All 'procedure' Topics ---")
    procedures = engine.get_topics_by_type("procedure")
    print(f"Total Procedures Found: {len(procedures)}")

    print("\n--- 4. Flatten All Topics ---")
    all_flat = engine.flatten_all_topics()
    print(f"Successfully flattened {len(all_flat)} topics for DB/AI ingestion.")
