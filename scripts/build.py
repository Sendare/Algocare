import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import random
import re
import shutil
import sys
import html
import time
from pathlib import Path
from utils.weighted_sampling import build_weighted_pool, sample_without_replacement

ROOT_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = ROOT_DIR / "templates"
ASSETS_DIR = ROOT_DIR / "assets"
DOCS_DIR = ROOT_DIR / "docs"
DATA_DIR = ROOT_DIR / "data"
CURRICULA_DIR = ROOT_DIR / "curricula"

# Hard stop at 170 seconds to allow safe git commit/push
MAX_RUNTIME = 99999 

def slugify(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower().strip()).strip("-")

def load_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def write_html(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def _inline_md(text):
    text = html.escape(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

def markdown_to_html(text):
    lines = text.strip().split("\n")
    parts = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1; continue
        
        # Ordered List
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                txt = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                items.append(f"<li>{_inline_md(txt)}</li>")
                i += 1
            parts.append("<ol>" + "".join(items) + "</ol>")
            continue
            
        # Unordered List
        if re.match(r"^[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                txt = re.sub(r"^[-*]\s+", "", lines[i].strip())
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
                    if re.match(r"^[\s|:-]+$", r): continue
                    html_table += "<tr>" + "".join(f"<td>{_inline_md(c.strip())}</td>" for c in r.strip("|").split("|")) + "</tr>"
                html_table += "</table>"
                parts.append(html_table)
            continue

        # Paragraph
        para = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(\d+\.\s+|[-*]\s+|\|)", lines[i].strip()):
            para.append(lines[i].strip())
            i += 1
        if para:
            parts.append(f"<p>{_inline_md(' '.join(para))}</p>")
        else:
            i += 1 # SAFETY: prevent infinite loop if line wasn't caught

    return "\n".join(parts)

PAGE_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Algocare</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{rel}assets/style.css">
<script src="{rel}assets/analytics.js"></script>
<script>window.APP_ROOT = "{root_rel}";</script>
<script src="{root_rel}assets/auth.js"></script>
</head>
<body>
<div class="topbar">
  <a href="{root_rel}index.html" class="brand" style="text-decoration:none;"><span class="pulse-dot"></span>Algocare</a>
  <div class="topbar-menu">
    <a href="{rel}index.html">Study Articles</a>
    <span id="authSlot"></span>
  </div>
</div>
<div class="container">
{breadcrumb}
{body}
</div>
<div style="text-align: center; margin-top: 40px; padding: 16px 0; font-size: 0.8rem;">
  <a href="{root_rel}privacy.html" style="color: var(--ink-soft); margin-right: 16px;">Privacy Policy</a>
  <a href="{root_rel}terms.html" style="color: var(--ink-soft);">Terms &amp; Disclaimer</a>
</div>
</body>
</html>
"""

def render_page(title, rel, breadcrumb_html, body_html):
    root_rel = rel + "../"
    return PAGE_HEAD.replace("{title}", title).replace("{rel}", rel).replace("{root_rel}", root_rel).replace("{breadcrumb}", breadcrumb_html).replace("{body}", body_html)

def breadcrumb(rel, crumbs):
    parts = [f'<a href="{rel}{href}">{label}</a>' if href else label for label, href in crumbs]
    return f'<div class="breadcrumb">{" &gt; ".join(parts)}</div>'

def render_article_page(article, ctx, prog, is_from_exam=False):
    headings_html = "".join(
        f'<div class="article-heading" id="{h["heading_id"]}"><h2>{h["title"]}</h2>{markdown_to_html(h["content"])}</div>'
        for h in sorted(article["headings"], key=lambda x: x["order"])
    )
    crumbs = breadcrumb("../../", [
        ("Home", "index.html"), (ctx["course_name"], f'{ctx["course_slug"]}/index.html'),
        (ctx["unit_name"], f'{ctx["course_slug"]}/{ctx["unit_slug"]}/index.html'), (article["title"], None),
    ])
    body = (
        f'<h1>{article["title"]}</h1>{headings_html}'
        f'<a id="actionButton" class="test-yourself-link" href="../../cbt/exam.html?mode=practice&topic={article["topic_id"]}&prog={prog}" style="display:inline-block; margin-top:24px; padding:10px 18px; background:var(--scrub); color:#fff; border-radius:var(--radius); font-weight:600; text-decoration:none;">Test yourself on this topic →</a>'
        f'<script>'
        f'  if(sessionStorage.getItem("algocare_exam_state")){{'
        f'    document.getElementById("actionButton").textContent="← Return to Exam";'
        f'    document.getElementById("actionButton").href="../../cbt/exam.html?resume=true";'
        f'  }}'
        f'  if(typeof logArticleViewed === "function") {{ logArticleViewed("{article["topic_id"]}"); }}'
        f'</script>'
    )
    return render_page(article["title"], "../../", crumbs, body)

def render_unit_page(course_name, course_slug, unit_name, unit_slug, topics):
    rows = "".join(f'<div class="topic-card"><div class="topic-title">{t["title"]}</div><div class="topic-actions"><a href="{t["topic_id"]}.html">Read →</a></div></div>' for t in sorted(topics, key=lambda x: x["order"]))
    crumbs = breadcrumb("../../", [("Home", "index.html"), (course_name, f"{course_slug}/index.html"), (unit_name, None)])
    return render_page(unit_name, "../../", crumbs, f'<h1>{unit_name}</h1><div class="branch-group">{rows}</div>')

def render_course_page(course_name, course_slug, units):
    rows = "".join(f'<div class="topic-card"><div><div class="topic-title">{u["unit_name"]}</div><div class="topic-meta">{u["topic_count"]} topics</div></div><div class="topic-actions"><a href="{u_slug}/index.html">Open →</a></div></div>' for u_slug, u in sorted(units.items(), key=lambda kv: kv[1]["unit_name"]))
    crumbs = breadcrumb("../", [("Home", "index.html"), (course_name, None)])
    return render_page(course_name, "../", crumbs, f'<h1>{course_name}</h1><div class="branch-group">{rows}</div>')

def render_home_page(courses):
    rows = "".join(f'<div class="topic-card"><div><div class="topic-title">{c["course_name"]}</div><div class="topic-meta">{c["unit_count"]} units · {c["topic_count"]} topics</div></div><div class="topic-actions"><a href="{c_slug}/index.html">Open →</a></div></div>' for c_slug, c in sorted(courses.items(), key=lambda kv: kv[1]["course_name"]))
    body = '<h1>Study articles</h1><p style="color: var(--ink-soft); margin-top: -8px;">Browse by course, or search below.</p><input type="text" id="searchInput" class="search-box" placeholder="Search courses, units, or topics..."><div class="branch-group" id="courseList">' + rows + '</div><script src="assets/home_search.js"></script>'
    return render_page("Algocare", "", "", body)

def build_context_lookup(prog):
    curriculum = load_json(CURRICULA_DIR / f"{prog}.json", {"curriculum": []})
    lookup = {}
    for c in curriculum.get("curriculum", []):
        c_name = c.get("course_name")
        c_slug = slugify(c_name)
        for u in c.get("units", []):
            u_name = u.get("unit_name")
            u_slug = slugify(u_name)
            for t in u.get("topics", []):
                lookup[t["topic_id"]] = {
                    "title": t.get("title"), "order": t.get("order", 0),
                    "course_name": c_name, "course_slug": c_slug,
                    "unit_name": u_name, "unit_slug": u_slug,
                }
    return lookup

def rebuild_navigation(prog, ctx_lookup):
    published = []
    courses = {}
    for topic_id, ctx in ctx_lookup.items():
        out_path = DOCS_DIR / prog / ctx["course_slug"] / ctx["unit_slug"] / f"{topic_id}.html"
        if out_path.exists():
            published.append(topic_id)
            courses.setdefault(ctx["course_slug"], {"course_name": ctx["course_name"], "units": {}})
            courses[ctx["course_slug"]]["units"].setdefault(ctx["unit_slug"], {"unit_name": ctx["unit_name"], "topics": []})
            courses[ctx["course_slug"]]["units"][ctx["unit_slug"]]["topics"].append({"topic_id": topic_id, "title": ctx["title"], "order": ctx["order"]})
            
    for c_slug, c_data in courses.items():
        for u_slug, u_data in c_data["units"].items():
            write_html(DOCS_DIR / prog / c_slug / u_slug / "index.html", render_unit_page(c_data["course_name"], c_slug, u_data["unit_name"], u_slug, u_data["topics"]))
        units_summary = {u_slug: {"unit_name": u["unit_name"], "topic_count": len(u["topics"])} for u_slug, u in c_data["units"].items()}
        write_html(DOCS_DIR / prog / c_slug / "index.html", render_course_page(c_data["course_name"], c_slug, units_summary))
        
    courses_summary = {c_slug: {"course_name": c["course_name"], "unit_count": len(c["units"]), "topic_count": sum(len(u["topics"]) for u in c["units"].values())} for c_slug, c in courses.items()}
    write_html(DOCS_DIR / prog / "index.html", render_home_page(courses_summary))

    site_index = []
    for c_slug, c_data in courses.items():
        for u_slug, u_data in c_data["units"].items():
            for t in u_data["topics"]:
                site_index.append({"topic_id": t["topic_id"], "title": t["title"], "course": c_data["course_name"], "course_slug": c_slug, "unit": u_data["unit_name"], "url": f"{c_slug}/{u_slug}/{t['topic_id']}.html"})
    save_json(DOCS_DIR / prog / "site_index.json", site_index)
    
    (DOCS_DIR / prog / "data" / "course_pools").mkdir(parents=True, exist_ok=True)
    for c_slug, c_data in courses.items():
        flat_qs = []
        for u_data in c_data["units"].values():
            for t in u_data["topics"]:
                flat_qs.extend(load_json(Path(f"data/{prog}/questions") / f"{t['topic_id']}.json", []))
        save_json(DOCS_DIR / prog / "data" / "course_pools" / f"{c_slug}.json", flat_qs)


def build_real_feel_tests(prog):
    config = load_json(f"config/{prog}/real_feel_config.json", {"question_count": 250, "seconds_per_question": 30})
    weights_config = load_json(f"config/{prog}/weights.json", {"courses": {}, "units": {}})
    
    used_ids = set()
    unused_pools = {}
    
    # Load all questions from course pools
    for c_file in (DOCS_DIR / prog / "data" / "course_pools").glob("*.json"):
        c_slug = c_file.stem
        if c_slug in weights_config.get("excluded_from_real_feel", []): continue
        questions = load_json(c_file, [])
        unused_pools[c_slug] = {"all": [q for q in questions if q["question_id"] not in used_ids]}

    pool = build_weighted_pool(unused_pools, weights_config)
    question_count = config["question_count"]

    real_feel_dir = DOCS_DIR / prog / "data" / "real_feel_tests"
    real_feel_dir.mkdir(parents=True, exist_ok=True)
    available = {"tests": []}

    test_num = 1
    while len(pool) >= question_count:
        selected = sample_without_replacement(pool, question_count)
        selected_ids = {q["question_id"] for q in selected}
        random.shuffle(selected)

        save_json(real_feel_dir / f"test_{test_num}.json", selected)
        used_ids.update(selected_ids)
        
        available["tests"].append(test_num)
        test_num += 1
        
        pool = [(q, w) for q, w in pool if q["question_id"] not in selected_ids]

    save_json(real_feel_dir / "index.json", available)
    print(f"  ✅ Generated {len(available['tests'])} Real-Feel Exams for {prog}.", flush=True)


def main():
    start_time = time.time()
    print("🚀 Starting Full Build...", flush=True)
    
    # 1. Root (Always wipe and rebuild to ensure fresh links)
    print("📁 Building root structure...", flush=True)
    if DOCS_DIR.exists(): shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir()
    for page in ["index.html", "login.html", "signup.html", "dashboard.html", "leaderboard.html", "admin.html", "manifest.json", "sw.js"]:
        src = TEMPLATES_DIR / page
        if src.exists(): shutil.copy2(src, DOCS_DIR / page)
    shutil.copytree(ASSETS_DIR, DOCS_DIR / "assets")
    
    # Copy PWA icons to root
    for icon in ["icon-192x192.png", "icon-512x512.png"]:
        icon_path = ASSETS_DIR / icon
        if icon_path.exists():
            shutil.copy2(icon_path, DOCS_DIR / icon)
    
    # Create _headers for Cloudflare to prevent HTML caching
    headers_content = '''/*.html
  Cache-Control: public, max-age=0, must-revalidate
/assets/*
  Cache-Control: public, max-age=31536000, immutable
'''
    (DOCS_DIR / "_headers").write_text(headers_content)

    for prog in ["nursing", "midwifery"]:
        (DOCS_DIR / prog).mkdir(parents=True, exist_ok=True)
        (DOCS_DIR / prog / "data").mkdir(exist_ok=True)
        if not (DOCS_DIR / prog / "assets").exists(): shutil.copytree(ASSETS_DIR, DOCS_DIR / prog / "assets")
        (DOCS_DIR / prog / "cbt").mkdir(exist_ok=True)
        for page in ["practice-setup.html", "exam-setup.html", "exam.html"]:
            src = TEMPLATES_DIR / page
            if src.exists(): shutil.copy2(src, DOCS_DIR / prog / "cbt" / page)
        
        if Path(f"data/{prog}/questions").exists():
            q_dest = DOCS_DIR / prog / "data" / "questions"
            if not q_dest.exists(): shutil.copytree(f"data/{prog}/questions", q_dest)
        if Path(f"config/{prog}/real_feel_config.json").exists():
            save_json(DOCS_DIR / prog / "data" / "real_feel_config.json", load_json(f"config/{prog}/real_feel_config.json", {}))

        ctx_lookup = build_context_lookup(prog)
        articles_dir = Path(f"data/{prog}/articles")
        all_articles = list(articles_dir.glob("*.json")) if articles_dir.exists() else []
        
        pending = []
        for a in all_articles:
            ctx = ctx_lookup.get(a.stem)
            if not ctx: continue
            out_path = DOCS_DIR / prog / ctx["course_slug"] / ctx["unit_slug"] / f"{a.stem}.html"
            if not out_path.exists():
                pending.append(a)

        if pending:
            print(f"📚 {prog.capitalize()}: Building until timeout (Total remaining: {len(pending)})...", flush=True)
            built_count = 0
            for a_file in pending:
                # Check timer at the start of every single file
                if time.time() - start_time > MAX_RUNTIME:
                    print(f"  ⏱️ Time limit reached ({MAX_RUNTIME}s). Stopping gracefully.", flush=True)
                    break
                    
                ctx = ctx_lookup.get(a_file.stem)
                if not ctx: continue
                article = load_json(a_file, None)
                if not article: continue
                
                write_html(DOCS_DIR / prog / ctx["course_slug"] / ctx["unit_slug"] / f"{a_file.stem}.html", render_article_page(article, ctx, prog))
                built_count += 1
                
            print(f"  💾 Built {built_count} files for {prog}.", flush=True)
            rebuild_navigation(prog, ctx_lookup)
            build_real_feel_tests(prog)

    print("🎉 All done! Every article has been generated.", flush=True)

if __name__ == "__main__":
    main()
