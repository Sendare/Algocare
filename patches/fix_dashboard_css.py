from pathlib import Path
import shutil

print("🚀 Fixing Dashboard CSS paths...")

# 1. Patch the build script to guarantee root assets are copied
bp = Path("build_pages.py")
src = bp.read_text()

# Ensure all necessary assets are copied to docs/assets/
old_copy = '''    for filename in ["style.css", "analytics.js", "auth.js"]:'''
new_copy = '''    for filename in ["style.css", "analytics.js", "auth.js", "home_search.js"]:'''

if old_copy in src:
    src = src.replace(old_copy, new_copy)
    bp.write_text(src)
    print("✅ Patched build_pages.py to copy all root assets")

# 2. Update dashboard.html, index.html, login.html, signup.html to use absolute paths
for f in ["docs/dashboard.html", "docs/index.html", "docs/login.html", "docs/signup.html"]:
    p = Path(f)
    if not p.exists(): continue
    html = p.read_text()
    
    # Change relative to absolute paths
    html = html.replace('href="assets/style.css"', 'href="/assets/style.css"')
    html = html.replace('src="assets/auth.js"', 'src="/assets/auth.js"')
    
    p.write_text(html)
    print(f"✅ Fixed CSS paths in {f}")

# 3. Force a sync of the assets right now for the local docs folder
docs_assets = Path("docs/assets")
docs_assets.mkdir(parents=True, exist_ok=True)
for f in ["style.css", "auth.js", "analytics.js", "home_search.js"]:
    if Path(f"assets/{f}").exists():
        shutil.copy2(f"assets/{f}", docs_assets / f)
print("✅ Synced local docs/assets/")
