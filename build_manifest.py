import json
from pathlib import Path

ARTICLES_DIR = Path("data/articles")
QUESTIONS_DIR = Path("data/questions")
MANIFEST_PATH = Path("data/manifest.json")


def build_manifest():
    topics = []

    if not ARTICLES_DIR.exists():
        print("⚠️  No articles directory found yet.")
        return

    for article_file in sorted(ARTICLES_DIR.glob("*.json")):
        topic_id = article_file.stem

        with open(article_file, "r", encoding="utf-8") as f:
            article = json.load(f)

        question_file = QUESTIONS_DIR / f"{topic_id}.json"
        question_count = 0
        if question_file.exists():
            with open(question_file, "r", encoding="utf-8") as f:
                question_count = len(json.load(f))

        topics.append({
            "topic_id": topic_id,
            "title": article.get("title"),
            "path": article.get("path", []),
            "heading_count": len(article.get("headings", [])),
            "question_count": question_count,
        })

    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump({"topics": topics}, f, indent=2, ensure_ascii=False)

    print(f"✅ Manifest written: {len(topics)} topic(s) -> {MANIFEST_PATH}")


if __name__ == "__main__":
    build_manifest()
