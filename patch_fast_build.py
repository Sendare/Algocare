from pathlib import Path

bp = Path("scripts/build.py")
src = bp.read_text()

# Fix the list comprehension bug for pending articles
old_code = """    pending = [a for a in all_articles if not (DOCS_DIR / prog / ctx_lookup.get(a.stem, {}).get("course_slug", "x") / ctx_lookup.get(a.stem, {}).get("unit_slug", "x") / f"{a.stem}.html").exists()]"""
new_code = """    pending = []
    for a in all_articles:
        ctx = ctx_lookup.get(a.stem)
        if not ctx: continue
        out_path = DOCS_DIR / prog / ctx["course_slug"] / ctx["unit_slug"] / f"{a.stem}.html"
        if not out_path.exists():
            pending.append(a)"""

src = src.replace(old_code, new_code)
bp.write_text(src)
print("✅ Fixed pending articles loop in scripts/build.py")
