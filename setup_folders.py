import os
import json

# Folders to ensure exist (new + pre-existing, safe to re-run)
FOLDERS = [
    "data",
    "data/articles",
    "data/questions",
    "state",
    "drafts",
    "approved",
    "failed",
    "published",
    "publish_logs",
    "workflow_logs",
    "logs",
]

# Files to initialize with empty/default JSON if they don't exist yet
FILES = {
    "data/topic_headings.json": {},
    "data/keyword_index.json": {},
    "state/generation_state.json": {
        "headings_done": [],
        "articles_done": []
    },
    "state/build_state.json": {
        "last_built_article_id": None,
        "last_build_time": None
    },
}


def setup_folders():
    created_folders = []
    skipped_folders = []

    for folder in FOLDERS:
        if not os.path.exists(folder):
            os.makedirs(folder)
            created_folders.append(folder)
        else:
            skipped_folders.append(folder)

    created_files = []
    skipped_files = []

    for filepath, default_content in FILES.items():
        if not os.path.exists(filepath):
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(default_content, f, indent=2)
            created_files.append(filepath)
        else:
            skipped_files.append(filepath)

    print("=========================================")
    print("       ALGOCARE FOLDER/FILE SETUP        ")
    print("=========================================\n")

    print(f"📁 Folders created ({len(created_folders)}):")
    for f in created_folders:
        print(f"   + {f}")

    print(f"\n📁 Folders already existed ({len(skipped_folders)}):")
    for f in skipped_folders:
        print(f"   = {f}")

    print(f"\n📄 Files created ({len(created_files)}):")
    for f in created_files:
        print(f"   + {f}")

    print(f"\n📄 Files already existed ({len(skipped_files)}):")
    for f in skipped_files:
        print(f"   = {f}")

    print("\n✅ Setup complete.")


if __name__ == "__main__":
    setup_folders()

