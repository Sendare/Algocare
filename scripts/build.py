#!/usr/bin/env python3
import json
import random
import re
import shutil
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sys
import html
from pathlib import Path

from utils.course_branch_map import get_course_branch_map
from utils.weighted_sampling import build_weighted_pool, sample_without_replacement

ROOT_DIR = Path(__file__).parent.parent
TEMPLATES_DIR = ROOT_DIR / "templates"
ASSETS_DIR = ROOT_DIR / "assets"
DOCS_DIR = ROOT_DIR / "docs"
PROGRAMS = ["nursing", "midwifery"]

# ==========================================
# Helper Functions
# ==========================================
def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")

def load_json(path, default):
    p = Path(path)
    if not p.exists(): return default
    with open(p, "r", encoding="utf-8") as f: return json.load(f)

def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, indent=2, ensure_ascii=False)

def write_html(path, html):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f: f.write(html)

def _inline_md(text):
    text = html.escape(text)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)

def markdown_to_html(text):
    lines = text.strip().split("\n")
    html_parts = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1; continue
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(f"<li>{_inline_md(re.sub(r'^\d+\.\s+', '', lines[i].strip()))}</li>")
                i += 1
            html_parts.append("<ol>" + "".join(items) + "</ol>")
            continue
        if re.match(r"^[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                items.append(f"<li>{_inline_md(re.sub(r'^[-*]\s+', '', lines[i].strip()))}</li>")
                i += 1
            html_parts.append("<ul>" + "".join(items) + "</ul>")
            continue
        para_lines = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(\d+\.\s+|[-*]\s+|\|)", lines[i].strip()):
            para_lines.append(lines[i].strip()); i += 1
        html_parts.append(f"<p>{_inline_md(' '.join(para_lines))}</p>")
    return "\n".join(html_parts)

def build_context_lookup(curriculum, course_map):
    lookup = {}
    for c in curriculum.get("curriculum", []):
        course_id = c.get("course_id")
        course_name = course_map.get(course_id, c.get("course_name"))
        course_slug = slugify(course_name)
        for u in c.get("units", []):
            unit_name = u.get("unit_name")
            unit_slug = slugify(unit_name)
            for t in u.get("topics", []):
                lookup[t["topic_id"]] = {
                    "title": t.get("title"), "order": t.get("order", 0),
                    "course_name": course_name, "course_slug": course_slug,
                    "unit_name": unit_name, "unit_slug": unit_slug,
                }
    return lookup

# ==========================================
# Page Shell (With Auth Topbar)
# ==========================================
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
<script src="{root_rel}assets/auth.js"></script>
</head>
<body>
<div class="topbar">
  <div class="brand"><span class="pulse-dot"></span>Algocare</div>
  <div>
    <a href="{rel}cbt/index.html" style="font-size: 0.85rem; color: var(--scrub); font-weight: 600; margin-right: 16px;">Practice tests</a>
    <a href="{rel}index.html" style="font-size: 0.85rem; color: var(--ink-soft); margin-right: 16px;">Home</a>
    <a href="{root_rel}index.html" style="font-size: 0.85rem; color: var(--ink-soft); margin-right: 16px;">All programs</a>
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
    html = PAGE_HEAD.replace("{title}", title).replace("{rel}", rel).replace("{root_rel}", root_rel).replace("{breadcrumb}", breadcrumb_html).replace("{body}", body_html)
    return html

def breadcrumb(rel, crumbs):
    parts = [f'<a href="{rel}{href}">{label}</a>' if href else label for label, href in crumbs]
    return f'<div class="breadcrumb">{" &gt; ".join(parts)}</div>'

# ==========================================
# Renderers
# ==========================================
def render_article_page(article, ctx):
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
        f'<a class="test-yourself-link" href="../../cbt/practice-setup.html?topic={article["topic_id"]}&prog={ctx["course_slug"]}" style="display:inline-block; margin-top:24px; padding:10px 18px; background:var(--scrub); color:#fff; border-radius:var(--radius); font-weight:600; text-decoration:none;">Test yourself on this topic →</a>'
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

# ==========================================
# CBT Real-Feel Builder
# ==========================================
def build_real_feel_tests(program):
    config = load_json(f"config/{program}/real_feel_config.json", {"question_count": 250, "seconds_per_question": 30})
    weights_config = load_json(f"config/{program}/weights.json", {"courses": {}, "units": {}})
    rf_state_path = Path(f"state/{program}/real_feel_state.json")
    rf_state = load_json(rf_state_path, {"used_question_ids": [], "tests_built": 0})
    
    used_ids = set(rf_state["used_question_ids"])
    unused_pools = {}
    
    # Load all questions from courses
    for c_file in (DOCS_DIR / program / "data" / "course_pools").glob("*.json"):
        c_slug = c_file.stem
        if c_slug in weights_config.get("excluded_from_real_feel", []): continue
        questions = load_json(c_file, [])
        unused_pools[c_slug] = {"all": [q for q in questions if q["question_id"] not in used_ids]}

    pool = build_weighted_pool(unused_pools, weights_config)
    question_count = config["question_count"]

    real_feel_dir = DOCS_DIR / program / "data" / "real_feel_tests"
    real_feel_dir.mkdir(parents=True, exist_ok=True)
    available = load_json(real_feel_dir / "index.json", {"tests": []})

    while len(pool) >= question_count:
        selected = sample_without_replacement(pool, question_count)
        selected_ids = {q["question_id"] for q in selected}
        random.shuffle(selected)

        rf_state["tests_built"] += 1
        test_number = rf_state["tests_built"]
        save_json(real_feel_dir / f"test_{test_number}.json", selected)
        used_ids.update(selected_ids)
        rf_state["used_question_ids"] = list(used_ids)
        save_json(rf_state_path, rf_state)

        available["tests"].append(test_number)
        save_json(real_feel_dir / "index.json", available)
        pool = [(q, w) for q, w in pool if q["question_id"] not in selected_ids]

# ==========================================
# Main Build Loop
# ==========================================
def main():
    print("🚀 Starting Master Build...")
    
    if DOCS_DIR.exists(): shutil.rmtree(DOCS_DIR)
    DOCS_DIR.mkdir()

    # 1. Copy Root Pages
    for page in ["index.html", "login.html", "signup.html", "dashboard.html", "leaderboard.html"]:
        src = TEMPLATES_DIR / page
        if src.exists(): shutil.copy2(src, DOCS_DIR / page)

    # 2. Copy Root Assets
    shutil.copytree(ASSETS_DIR, DOCS_DIR / "assets")

    # 3. Build Programs
    for prog in PROGRAMS:
        print(f"\n📚 Building Program: {prog}")
        
        # Ensure dirs
        (DOCS_DIR / prog).mkdir()
        (DOCS_DIR / prog / "data").mkdir()
        
        # Copy assets & CBT pages
        shutil.copytree(ASSETS_DIR, DOCS_DIR / prog / "assets")
        (DOCS_DIR / prog / "cbt").mkdir()
        for page in ["practice-setup.html", "exam-setup.html", "exam.html"]:
            src = TEMPLATES_DIR / page
            if src.exists(): shutil.copy2(src, DOCS_DIR / prog / "cbt" / page)
            
        # Copy question data
        if Path(f"data/{prog}/questions").exists():
            shutil.copytree(f"data/{prog}/questions", DOCS_DIR / prog / "data" / "questions")
        if Path(f"config/{prog}/real_feel_config.json").exists():
            save_json(DOCS_DIR / prog / "data" / "real_feel_config.json", load_json(f"config/{prog}/real_feel_config.json", {}))

        # Generate Articles
        curriculum = load_json(f"curricula/{prog}.json", {})
        course_map = get_course_branch_map(prog)
        ctx_lookup = build_context_lookup(curriculum, course_map)
        
        published = []
        courses = {}
        
        articles_dir = Path(f"data/{prog}/articles")
        if articles_dir.exists():
            for a_file in articles_dir.glob("*.json"):
                topic_id = a_file.stem
                ctx = ctx_lookup.get(topic_id)
                if not ctx: continue
                
                article = load_json(a_file, None)
                if not article: continue
                
                write_html(DOCS_DIR / prog / ctx["course_slug"] / ctx["unit_slug"] / f"{topic_id}.html", render_article_page(article, ctx))
                published.append(topic_id)
                
                courses.setdefault(ctx["course_slug"], {"course_name": ctx["course_name"], "units": {}})
                courses[ctx["course_slug"]]["units"].setdefault(ctx["unit_slug"], {"unit_name": ctx["unit_name"], "topics": []})
                courses[ctx["course_slug"]]["units"][ctx["unit_slug"]]["topics"].append({"topic_id": topic_id, "title": ctx["title"], "order": ctx["order"]})

        # Generate Navigation Pages
        for c_slug, c_data in courses.items():
            for u_slug, u_data in c_data["units"].items():
                write_html(DOCS_DIR / prog / c_slug / u_slug / "index.html", render_unit_page(c_data["course_name"], c_slug, u_data["unit_name"], u_slug, u_data["topics"]))
            
            units_summary = {u_slug: {"unit_name": u["unit_name"], "topic_count": len(u["topics"])} for u_slug, u in c_data["units"].items()}
            write_html(DOCS_DIR / prog / c_slug / "index.html", render_course_page(c_data["course_name"], c_slug, units_summary))
            
        courses_summary = {c_slug: {"course_name": c["course_name"], "unit_count": len(c["units"]), "topic_count": sum(len(u["topics"]) for u in c["units"].values())} for c_slug, c in courses.items()}
        write_html(DOCS_DIR / prog / "index.html", render_home_page(courses_summary))

        # Site Index for Search
        site_index = []
        for c_slug, c_data in courses.items():
            for u_slug, u_data in c_data["units"].items():
                for t in u_data["topics"]:
                    site_index.append({"topic_id": t["topic_id"], "title": t["title"], "course": c_data["course_name"], "course_slug": c_slug, "unit": u_data["unit_name"], "url": f"{c_slug}/{u_slug}/{t['topic_id']}.html"})
        save_json(DOCS_DIR / prog / "site_index.json", site_index)

        # CBT Pools & Real-Feel
        (DOCS_DIR / prog / "data" / "course_pools").mkdir(parents=True, exist_ok=True)
        for c_slug, c_data in courses.items():
            flat_qs = []
            for u_data in c_data["units"].values():
                for t in u_data["topics"]:
                    flat_qs.extend(load_json(Path(f"data/{prog}/questions") / f"{t['topic_id']}.json", []))
            save_json(DOCS_DIR / prog / "data" / "course_pools" / f"{c_slug}.json", flat_qs)

        build_real_feel_tests(prog)
        print(f"  ✅ Built {len(published)} articles and generated exams for {prog}")

    print("\n🎉 Master Build Complete! Deploy the 'docs' folder.")

if __name__ == "__main__":
    main()
