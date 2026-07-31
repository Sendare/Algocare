import json
import re
import shutil
import time
from pathlib import Path

from utils.course_branch_map import COURSE_BRANCH_MAP, get_course_id_from_topic_id

CURRICULUM_PATH = "curriculum.json"
ARTICLES_DIR = Path("data/articles")
PUBLISHED_DIR = Path("docs")
STATE_PATH = Path("state/build_state.json")

MAX_RUNTIME_SECONDS = 270  # 4.5 min hard stop - same tier-limit reasoning as the fetch scripts

# ---------- helpers ----------

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def load_json(path, default):
    p = Path(path)
    if not p.exists():
        return default
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_html(path, html):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html)


def build_context_lookup(curriculum):
    """topic_id -> {title, order, course_name, course_slug, unit_name, unit_slug}"""
    lookup = {}
    for c in curriculum.get("curriculum", []):
        course_id = c.get("course_id")
        course_name = COURSE_BRANCH_MAP.get(course_id, c.get("course_name"))
        course_slug = slugify(course_name)
        for u in c.get("units", []):
            unit_name = u.get("unit_name")
            unit_slug = slugify(unit_name)
            for t in u.get("topics", []):
                lookup[t["topic_id"]] = {
                    "title": t.get("title"),
                    "order": t.get("order", 0),
                    "course_name": course_name,
                    "course_slug": course_slug,
                    "unit_name": unit_name,
                    "unit_slug": unit_slug,
                }
    return lookup


# ---------- page shell ----------

PAGE_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Algocare</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{rel}assets/style.css">
</head>
<body>
<div class="topbar">
  <div class="brand"><span class="pulse-dot"></span>Algocare</div>
  <a href="{rel}index.html" style="font-size: 0.85rem; color: var(--ink-soft);">Home</a>
</div>
<div class="container">
{breadcrumb}
{body}
</div>
</body>
</html>
"""


def render_page(title, rel, breadcrumb_html, body_html):
    return PAGE_HEAD.format(title=title, rel=rel, breadcrumb=breadcrumb_html, body=body_html)


def breadcrumb(rel, crumbs):
    """crumbs = list of (label, href|None) - last one has no href"""
    parts = []
    for label, href in crumbs:
        if href:
            parts.append(f'<a href="{rel}{href}">{label}</a>')
        else:
            parts.append(label)
    return f'<div class="breadcrumb">{" &gt; ".join(parts)}</div>'


# ---------- article page ----------

def render_article_page(article, ctx):
    headings_html = "".join(
        f'<div class="article-heading" id="{h["heading_id"]}"><h2>{h["title"]}</h2><p>{h["content"]}</p></div>'
        for h in sorted(article["headings"], key=lambda x: x["order"])
    )
    crumbs = breadcrumb("../../", [
        ("Home", "index.html"),
        (ctx["course_name"], f'{ctx["course_slug"]}/index.html'),
        (ctx["unit_name"], f'{ctx["course_slug"]}/{ctx["unit_slug"]}/index.html'),
        (article["title"], None),
    ])
    body = f'<h1>{article["title"]}</h1>{headings_html}'
    return render_page(article["title"], "../../", crumbs, body)


# ---------- unit / course / home pages ----------

def render_unit_page(course_name, course_slug, unit_name, unit_slug, topics):
    topics_sorted = sorted(topics, key=lambda t: t["order"])
    rows = "".join(
        f'<div class="topic-card"><div class="topic-title">{t["title"]}</div>'
        f'<div class="topic-actions"><a href="{t["topic_id"]}.html">Read →</a></div></div>'
        for t in topics_sorted
    )
    crumbs = breadcrumb("../../", [
        ("Home", "index.html"),
        (course_name, f"{course_slug}/index.html"),
        (unit_name, None),
    ])
    body = f'<h1>{unit_name}</h1><div class="branch-group">{rows}</div>'
    return render_page(unit_name, "../../", crumbs, body)


def render_course_page(course_name, course_slug, units):
    """units = {unit_slug: {unit_name, topic_count}}"""
    rows = "".join(
        f'<div class="topic-card"><div><div class="topic-title">{u["unit_name"]}</div>'
        f'<div class="topic-meta">{u["topic_count"]} topics</div></div>'
        f'<div class="topic-actions"><a href="{unit_slug}/index.html">Open →</a></div></div>'
        for unit_slug, u in sorted(units.items(), key=lambda kv: kv[1]["unit_name"])
    )
    crumbs = breadcrumb("../", [("Home", "index.html"), (course_name, None)])
    body = f'<h1>{course_name}</h1><div class="branch-group">{rows}</div>'
    return render_page(course_name, "../", crumbs, body)


def render_home_page(courses):
    """courses = {course_slug: {course_name, unit_count, topic_count}}"""
    rows = "".join(
        f'<div class="topic-card"><div><div class="topic-title">{c["course_name"]}</div>'
        f'<div class="topic-meta">{c["unit_count"]} units · {c["topic_count"]} topics</div></div>'
        f'<div class="topic-actions"><a href="{course_slug}/index.html">Open →</a></div></div>'
        for course_slug, c in sorted(courses.items(), key=lambda kv: kv[1]["course_name"])
    )
    body = (
        '<h1>Study articles</h1>'
        '<p style="color: var(--ink-soft); margin-top: -8px;">Browse by course, or search below.</p>'
        '<input type="text" id="searchInput" class="search-box" placeholder="Search courses, units, or topics...">'
        f'<div class="branch-group" id="courseList">{rows}</div>'
        '<script src="assets/home_search.js"></script>'
    )
    return render_page("Algocare", "", "", body)


# ---------- main ----------

def run():
    start_time = time.time()

    # GitHub Pages only serves what's inside PUBLISHED_DIR - assets/ lives at
    # repo root as a sibling, so it must be copied in on every run to be reachable.
    assets_src = Path("assets")
    if assets_src.exists():
        shutil.copytree(assets_src, PUBLISHED_DIR / "assets", dirs_exist_ok=True)
        print(f"📦 Copied {assets_src} -> {PUBLISHED_DIR / 'assets'}")
    else:
        print(f"⚠️  No {assets_src} folder found at repo root - CSS/JS will be missing.")

    curriculum = load_json(CURRICULUM_PATH, {})
    ctx_lookup = build_context_lookup(curriculum)

    state = load_json(STATE_PATH, {})
    state.setdefault("published_done", [])
    done_ids = set(state["published_done"])

    available_ids = sorted(p.stem for p in ARTICLES_DIR.glob("*.json")) if ARTICLES_DIR.exists() else []
    pending_ids = [tid for tid in available_ids if tid not in done_ids]

    print(f"Articles available : {len(available_ids)}")
    print(f"Already published  : {len(done_ids)}")
    print(f"Pending this run   : {len(pending_ids)}")

    processed_this_run = 0

    for topic_id in pending_ids:
        elapsed = time.time() - start_time
        if elapsed > MAX_RUNTIME_SECONDS:
            print(f"⏱️  Time limit reached ({elapsed:.0f}s). Stopping gracefully.")
            break

        ctx = ctx_lookup.get(topic_id)
        if ctx is None:
            print(f"⚠️  {topic_id} not found in curriculum.json. Skipping.")
            continue

        article = load_json(ARTICLES_DIR / f"{topic_id}.json", None)
        if article is None:
            print(f"⚠️  Could not read article file for {topic_id}. Skipping.")
            continue

        html = render_article_page(article, ctx)
        out_path = PUBLISHED_DIR / ctx["course_slug"] / ctx["unit_slug"] / f"{topic_id}.html"
        write_html(out_path, html)

        state["published_done"].append(topic_id)
        save_json(STATE_PATH, state)

        processed_this_run += 1
        print(f"✅ [{processed_this_run}] {topic_id} -> {out_path}")

    # ---- rebuild navigation (home / course / unit pages) from everything published so far ----
    published_ids = state["published_done"]

    courses = {}   # course_slug -> {course_name, units: {unit_slug: {unit_name, topics: [...]}}}
    for topic_id in published_ids:
        ctx = ctx_lookup.get(topic_id)
        if ctx is None:
            continue
        c_slug, u_slug = ctx["course_slug"], ctx["unit_slug"]
        courses.setdefault(c_slug, {"course_name": ctx["course_name"], "units": {}})
        courses[c_slug]["units"].setdefault(u_slug, {"unit_name": ctx["unit_name"], "topics": []})
        courses[c_slug]["units"][u_slug]["topics"].append({
            "topic_id": topic_id, "title": ctx["title"], "order": ctx["order"]
        })

    # unit pages
    for c_slug, c_data in courses.items():
        for u_slug, u_data in c_data["units"].items():
            html = render_unit_page(c_data["course_name"], c_slug, u_data["unit_name"], u_slug, u_data["topics"])
            write_html(PUBLISHED_DIR / c_slug / u_slug / "index.html", html)

    # course pages
    for c_slug, c_data in courses.items():
        units_summary = {
            u_slug: {"unit_name": u_data["unit_name"], "topic_count": len(u_data["topics"])}
            for u_slug, u_data in c_data["units"].items()
        }
        html = render_course_page(c_data["course_name"], c_slug, units_summary)
        write_html(PUBLISHED_DIR / c_slug / "index.html", html)

    # home page
    courses_summary = {
        c_slug: {
            "course_name": c_data["course_name"],
            "unit_count": len(c_data["units"]),
            "topic_count": sum(len(u["topics"]) for u in c_data["units"].values()),
        }
        for c_slug, c_data in courses.items()
    }
    write_html(PUBLISHED_DIR / "index.html", render_home_page(courses_summary))

    # site-wide search index for the homepage's client-side search
    site_index = []
    for c_slug, c_data in courses.items():
        for u_slug, u_data in c_data["units"].items():
            for t in u_data["topics"]:
                site_index.append({
                    "title": t["title"],
                    "course": c_data["course_name"],
                    "unit": u_data["unit_name"],
                    "url": f"{c_slug}/{u_slug}/{t['topic_id']}.html",
                })
    save_json(PUBLISHED_DIR / "site_index.json", site_index)

    print(f"\n🏁 Run complete. Built {processed_this_run} new article page(s) this run.")
    print(f"   Total published: {len(published_ids)}/{len(available_ids)}")
    print(f"   Navigation rebuilt for {len(courses)} course(s).")


if __name__ == "__main__":
    run()
