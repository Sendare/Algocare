"""
ONE-TIME migration: moves the existing flat single-program layout into a
program-namespaced layout under "nursing", and creates the new top-level
program-picker homepage.

Run this via GitHub Actions (workflow_dispatch), NOT locally - a local
sparse checkout won't see most of the files that need to move, and would
silently leave the real repo content untouched while reporting success.

After this runs once successfully, delete restructure_once.yml - it's a
one-off, not something that should ever run twice.
"""
import shutil
from pathlib import Path

PROGRAM = "nursing"

MOVES = [
    ("curriculum.json", f"curricula/{PROGRAM}.json"),
    ("data/topic_headings.json", f"data/{PROGRAM}/topic_headings.json"),
    ("data/articles", f"data/{PROGRAM}/articles"),
    ("data/questions", f"data/{PROGRAM}/questions"),
    ("state/generation_state.json", f"state/{PROGRAM}/generation_state.json"),
    ("state/build_state.json", f"state/{PROGRAM}/build_state.json"),
    ("state/real_feel_state.json", f"state/{PROGRAM}/real_feel_state.json"),
    ("config/weights.json", f"config/{PROGRAM}/weights.json"),
    ("config/real_feel_config.json", f"config/{PROGRAM}/real_feel_config.json"),
]

PICKER_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Algocare — Choose Your Program</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css">
</head>
<body>
<div class="topbar">
  <div class="brand"><span class="pulse-dot"></span>Algocare</div>
</div>
<div class="container">
  <h1>Choose your program</h1>
  <p style="color: var(--ink-soft); margin-top: -8px;">Select the exam track you're studying for.</p>
  <div class="branch-group">
    <div class="topic-card">
      <div><div class="topic-title">Basic Nursing</div>
      <div class="topic-meta">Articles, practice tests, real-feel exams</div></div>
      <div class="topic-actions"><a href="nursing/index.html">Open →</a></div>
    </div>
    <!-- When a new program launches, add a matching block here, e.g.:
    <div class="topic-card">
      <div><div class="topic-title">Basic Midwifery</div>
      <div class="topic-meta">Articles, practice tests, real-feel exams</div></div>
      <div class="topic-actions"><a href="midwifery/index.html">Open →</a></div>
    </div>
    -->
  </div>
</div>
</body>
</html>
"""


def run():
    for src, dst in MOVES:
        src_path = Path(src)
        dst_path = Path(dst)
        if not src_path.exists():
            print(f"⚠️  Skipping {src} - not found (already moved?)")
            continue
        if dst_path.exists():
            print(f"⚠️  Skipping {src} -> {dst} - destination already exists")
            continue
        dst_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src_path), str(dst_path))
        print(f"✅ Moved {src} -> {dst}")

    # Move everything currently under docs/ into docs/nursing/
    docs_path = Path("docs")
    nursing_docs = docs_path / PROGRAM
    if docs_path.exists() and not nursing_docs.exists():
        nursing_docs.mkdir(parents=True)
        for item in list(docs_path.iterdir()):
            if item.name == PROGRAM:
                continue
            shutil.move(str(item), str(nursing_docs / item.name))
        print(f"✅ Moved docs/* -> docs/{PROGRAM}/*")
    else:
        print(f"⚠️  Skipping docs/ move - docs/{PROGRAM} already exists or docs/ missing")

    # New top-level program picker
    (docs_path / "index.html").write_text(PICKER_HTML, encoding="utf-8")
    print("✅ Wrote new docs/index.html (program picker)")

    # Assets need a root-level copy too, for the picker page's own CSS
    assets_src = Path("assets")
    if assets_src.exists():
        shutil.copytree(assets_src, docs_path / "assets", dirs_exist_ok=True)
        print(f"✅ Copied {assets_src} -> docs/assets (for the picker page)")

    print("\n🏁 Migration complete.")


if __name__ == "__main__":
    run()
