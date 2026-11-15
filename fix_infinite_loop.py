from pathlib import Path

bp = Path("scripts/build.py")
src = bp.read_text()

old_func = """def markdown_to_html(text):
    lines = text.strip().split("\\n")
    parts = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1; continue
        if re.match(r"^\\d+\\.\\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\\d+\\.\\s+", lines[i].strip()):
                txt = re.sub(r"^\\d+\\.\\s+", "", lines[i].strip())
                items.append(f"<li>{_inline_md(txt)}</li>")
                i += 1
            parts.append("<ol>" + "".join(items) + "</ol>")
            continue
        if re.match(r"^[-*]\\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\\s+", lines[i].strip()):
                txt = re.sub(r"^[-*]\\s+", "", lines[i].strip())
                items.append(f"<li>{_inline_md(txt)}</li>")
                i += 1
            parts.append("<ul>" + "".join(items) + "</ul>")
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(\\d+\\.\\s+|[-*]\\s+|\\|)", lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        parts.append(f"<p>{_inline_md(' '.join(para))}</p>")
    return "\\n".join(parts)"""

new_func = """def markdown_to_html(text):
    lines = text.strip().split("\\n")
    parts = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1; continue
        
        # Ordered List
        if re.match(r"^\\d+\\.\\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\\d+\\.\\s+", lines[i].strip()):
                txt = re.sub(r"^\\d+\\.\\s+", "", lines[i].strip())
                items.append(f"<li>{_inline_md(txt)}</li>")
                i += 1
            parts.append("<ol>" + "".join(items) + "</ol>")
            continue
            
        # Unordered List
        if re.match(r"^[-*]\\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\\s+", lines[i].strip()):
                txt = re.sub(r"^[-*]\\s+", "", lines[i].strip())
                items.append(f"<li>{_inline_md(txt)}</li>")
                i += 1
            parts.append("<ul>" + "".join(items) + "</ul>")
            continue
            
        # Table (THIS WAS MISSING)
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(lines[i].strip())
                i += 1
            if rows:
                html_table = "<table>"
                for r in rows:
                    if re.match(r"^[\\s|:-]+$", r): continue
                    html_table += "<tr>" + "".join(f"<td>{_inline_md(c.strip())}</td>" for c in r.strip("|").split("|")) + "</tr>"
                html_table += "</table>"
                parts.append(html_table)
            continue

        # Paragraph
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(\\d+\\.\\s+|[-*]\\s+|\\|)", lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        if para:
            parts.append(f"<p>{_inline_md(' '.join(para))}</p>")
        else:
            i += 1 # SAFETY: prevent infinite loop if line wasn't caught

    return "\\n".join(parts)"""

if old_func in src:
    src = src.replace(old_func, new_func)
    bp.write_text(src)
    print("✅ Fixed infinite loop in markdown_to_html")
else:
    print("⚠️ Could not find the exact function block. Let me know!")
