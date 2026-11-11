from pathlib import Path
bp = Path("build_pages.py")
src = bp.read_text()
if "(function() {" in src:
    src = src.replace("(function() {", "(function() {{")
    src = src.replace("})();", "}})();")
    bp.write_text(src)
    print("✅ Escaped JS braces in build_pages.py")
else:
    print("ℹ️ build_pages.py looks clean.")
