from pathlib import Path
import shutil

print("🚀 Renaming real_feel.html to exam-mode.html to bypass PWA cache...")

# 1. Rename the files in cbt-app
old_html = Path("cbt-app/real_feel.html")
new_html = Path("cbt-app/exam-mode.html")
if old_html.exists():
    shutil.copy(old_html, new_html)
    old_html.unlink()
    print("✅ Renamed real_feel.html -> exam-mode.html")

# 2. Update the link in index.js
index_js = Path("cbt-app/js/index.js")
if index_js.exists():
    src = index_js.read_text()
    src = src.replace("real_feel.html?test=", "exam-mode.html?test=")
    index_js.write_text(src)
    print("✅ Updated index.js to point to exam-mode.html")

# 3. Cleanup test files
for f in ["cbt-app/canary-test.html", "cbt-app/real_feel.html.bak"]:
    p = Path(f)
    if p.exists():
        p.unlink()
        print(f"🧹 Deleted {f}")

# 4. Delete the old real_feel.html from docs to prevent confusion
for prog in ["nursing", "midwifery"]:
    p = Path(f"docs/{prog}/cbt/real_feel.html")
    if p.exists():
        p.unlink()
        print(f"🧹 Deleted stale {p}")

