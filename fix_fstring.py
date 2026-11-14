from pathlib import Path

bp = Path("scripts/build.py")
src = bp.read_text()

# Fix ordered list f-string
src = src.replace(
    '''items.append(f"<li>{_inline_md(re.sub(r'^\\d+\\.\\s+', '', lines[i].strip()))}</li>")''',
    '''txt = re.sub(r"^\\d+\\.\\s+", "", lines[i].strip())\n                items.append(f"<li>{_inline_md(txt)}</li>")'''
)

# Fix unordered list f-string
src = src.replace(
    '''items.append(f"<li>{_inline_md(re.sub(r'^[-*]\\s+', '', lines[i].strip()))}</li>")''',
    '''txt = re.sub(r"^[-*]\\s+", "", lines[i].strip())\n                items.append(f"<li>{_inline_md(txt)}</li>")'''
)

bp.write_text(src)
print("✅ Fixed Python f-string backslash issue")
