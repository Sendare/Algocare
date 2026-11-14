from pathlib import Path
import shutil

print("🚀 Fixing auth.js path...")

# 1. Create docs/assets directory and copy auth.js
docs_assets = Path("docs/assets")
docs_assets.mkdir(parents=True, exist_ok=True)
shutil.copy2("assets/auth.js", docs_assets / "auth.js")
shutil.copy2("assets/style.css", docs_assets / "style.css")
shutil.copy2("assets/analytics.js", docs_assets / "analytics.js")
print("✅ Copied auth.js and styles to docs/assets/")

# 2. Patch build_pages.py to always copy assets to docs/assets/
bp = Path("build_pages.py")
src = bp.read_text()

if "copy_root_assets" not in src:
    # Add a small function to copy root assets
    copy_func = '''
def copy_root_assets():
    """Ensure docs/assets has the latest shared files for the root index.html, login, and signup pages."""
    docs_assets = Path("docs/assets")
    docs_assets.mkdir(parents=True, exist_ok=True)
    for filename in ["style.css", "analytics.js", "auth.js"]:
        src = Path("assets") / filename
        if src.exists():
            shutil.copy2(src, docs_assets / filename)
'''
    src = src.replace("def write_pwa_files():", copy_func + "\ndef write_pwa_files():")
    
    # Call it inside run()
    src = src.replace("    write_pwa_files()", "    write_pwa_files()\n    copy_root_assets()")
    
    bp.write_text(src)
    print("✅ Patched build_pages.py to sync docs/assets/")

