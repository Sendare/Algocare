import json
import random
import re
import shutil
import sys
import time
from pathlib import Path

from utils.course_branch_map import get_course_branch_map, get_course_id_from_topic_id
from utils.weighted_sampling import build_weighted_pool, sample_without_replacement

if len(sys.argv) < 2:
    print("Usage: python build_pages.py <program>  (e.g. nursing, midwifery)")
    sys.exit(1)
PROGRAM = sys.argv[1]

CURRICULUM_PATH = f"curricula/{PROGRAM}.json"
ARTICLES_DIR = Path(f"data/{PROGRAM}/articles")
QUESTIONS_DIR = Path(f"data/{PROGRAM}/questions")
CBT_APP_SRC = Path("cbt-app")          # shared source across all programs
PUBLISHED_DIR = Path(f"docs/{PROGRAM}")
STATE_PATH = Path(f"state/{PROGRAM}/build_state.json")
REAL_FEEL_STATE_PATH = Path(f"state/{PROGRAM}/real_feel_state.json")
REAL_FEEL_CONFIG_PATH = Path(f"config/{PROGRAM}/real_feel_config.json")
WEIGHTS_CONFIG_PATH = Path(f"config/{PROGRAM}/weights.json")

COURSE_BRANCH_MAP = get_course_branch_map(PROGRAM)

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


def _inline_md(text):
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)


def markdown_to_html(text):
    """Converts the limited markdown the AI is instructed to use (bold,
    numbered/bulleted lists, simple tables) into real HTML. Anything else
    is treated as plain prose and wrapped in <p>."""
    lines = text.strip().split("\n")
    html_parts = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if re.match(r"^\d+\.\s+", line):
            items = []
            while i < len(lines) and re.match(r"^\d+\.\s+", lines[i].strip()):
                item_text = re.sub(r"^\d+\.\s+", "", lines[i].strip())
                items.append(f"<li>{_inline_md(item_text)}</li>")
                i += 1
            html_parts.append("<ol>" + "".join(items) + "</ol>")
            continue
        if re.match(r"^[-*]\s+", line):
            items = []
            while i < len(lines) and re.match(r"^[-*]\s+", lines[i].strip()):
                item_text = re.sub(r"^[-*]\s+", "", lines[i].strip())
                items.append(f"<li>{_inline_md(item_text)}</li>")
                i += 1
            html_parts.append("<ul>" + "".join(items) + "</ul>")
            continue
        if line.startswith("|"):
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            rows = [
                [c.strip() for c in l.strip("|").split("|")]
                for l in table_lines
                if not re.match(r"^[\s|:-]+$", l)
            ]
            if rows:
                head, *body = rows
                thead = "<tr>" + "".join(f"<th>{_inline_md(c)}</th>" for c in head) + "</tr>"
                tbody = "".join(
                    "<tr>" + "".join(f"<td>{_inline_md(c)}</td>" for c in r) + "</tr>"
                    for r in body
                )
                html_parts.append(f"<table>{thead}{tbody}</table>")
            continue
        para_lines = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(\d+\.\s+|[-*]\s+|\|)", lines[i].strip()):
            para_lines.append(lines[i].strip())
            i += 1
        html_parts.append(f"<p>{_inline_md(' '.join(para_lines))}</p>")
    return "\n".join(html_parts)


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
<script src="{rel}assets/analytics.js"></script>
</head>
<body>
<div class="topbar">
  <div class="brand"><span class="pulse-dot"></span>Algocare</div>
  <div>
    <a href="{rel}cbt/index.html" style="font-size: 0.85rem; color: var(--scrub); font-weight: 600; margin-right: 16px;">Practice tests</a>
    <a href="{rel}index.html" style="font-size: 0.85rem; color: var(--ink-soft); margin-right: 16px;">Home</a>
    <a href="{root_rel}index.html" style="font-size: 0.85rem; color: var(--ink-soft);">All programs</a>
  </div>
</div>
<div class="container">
{breadcrumb}
{body}
</div>
</body>
</html>
"""


def render_page(title, rel, breadcrumb_html, body_html):
    root_rel = rel + "../"
    return PAGE_HEAD.format(title=title, rel=rel, root_rel=root_rel, breadcrumb=breadcrumb_html, body=body_html)


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
        f'<div class="article-heading" id="{h["heading_id"]}"><h2>{h["title"]}</h2>{markdown_to_html(h["content"])}</div>'
        for h in sorted(article["headings"], key=lambda x: x["order"])
    )
    crumbs = breadcrumb("../../", [
        ("Home", "index.html"),
        (ctx["course_name"], f'{ctx["course_slug"]}/index.html'),
        (ctx["unit_name"], f'{ctx["course_slug"]}/{ctx["unit_slug"]}/index.html'),
        (article["title"], None),
    ])
    body = (
        f'<h1>{article["title"]}</h1>{headings_html}'
        f'<a class="test-yourself-link" href="../../cbt/index.html?topic={article["topic_id"]}">Test yourself on this topic →</a>'
        f'onclick="logArticleCtaClick(\'{article["topic_id"]}\')">Test yourself on this topic →</a>'
        f'<script>logArticleViewed("{article["topic_id"]}");</script>'

    )
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


# ---------- CBT: course pools + real-feel exams ----------

def build_course_pools(courses, questions_dir):
    """
    courses: the same {course_slug: {course_name, units: {unit_slug: {..., topics:[...]}}}}
    structure already built for nav. Returns {course_slug: {unit_slug: [question, ...]}}
    by loading each published topic's question file.
    """
    pools = {}
    for c_slug, c_data in courses.items():
        pools[c_slug] = {}
        for u_slug, u_data in c_data["units"].items():
            questions = []
            for t in u_data["topics"]:
                q_path = questions_dir / f"{t['topic_id']}.json"
                q_list = load_json(q_path, [])
                questions.extend(q_list)
            pools[c_slug][u_slug] = questions
    return pools


def build_real_feel_tests(course_pools):
    """
    Draws fixed-size, weighted, non-overlapping question sets from everything
    published so far. Never rewrites an already-built test - only adds a new
    one when enough unused questions exist. Cheap (no AI calls), safe to run
    every hour alongside the rest of the build.
    """
    config = load_json(REAL_FEEL_CONFIG_PATH, {
        "question_count": 250, "seconds_per_question": 30, "min_answered_to_submit": 125
    })
    weights_config = load_json(WEIGHTS_CONFIG_PATH, {"courses": {}, "units": {}})

    rf_state = load_json(REAL_FEEL_STATE_PATH, {"used_question_ids": [], "tests_built": 0})

    # Self-cleaning: if the state says we're starting fresh (0 built), any
    # real_feel_tests files still on disk are stale leftovers from before a
    # reset - possibly never actually deleted locally if that machine has a
    # sparse checkout that doesn't include docs/. Wipe them here instead,
    # since this always runs with a full checkout on GitHub Actions.
    real_feel_tests_dir = PUBLISHED_DIR / "data" / "real_feel_tests"
    if rf_state.get("tests_built", 0) == 0 and real_feel_tests_dir.exists():
        shutil.rmtree(real_feel_tests_dir)
        print(f"🧹 tests_built is 0 - cleared stale {real_feel_tests_dir} before rebuilding")

    used_ids = set(rf_state["used_question_ids"])

    # Filter out already-used questions before building the weighted pool
    unused_pools = {}
    for c_slug, units in course_pools.items():
        unused_pools[c_slug] = {}
        for u_slug, questions in units.items():
            unused_pools[c_slug][u_slug] = [q for q in questions if q["question_id"] not in used_ids]

    pool = build_weighted_pool(unused_pools, weights_config)
    question_count = config["question_count"]

    tests_built_this_run = 0
    available_ids_path = PUBLISHED_DIR / "data" / "real_feel_tests" / "index.json"
    available = load_json(available_ids_path, {"tests": []})

    while len(pool) >= question_count:
        selected = sample_without_replacement(pool, question_count)
        selected_ids = {q["question_id"] for q in selected}

        random.shuffle(selected)  # guarantee no residual course/unit clustering in presentation order

        rf_state["tests_built"] += 1
        test_number = rf_state["tests_built"]
        save_json(PUBLISHED_DIR / "data" / "real_feel_tests" / f"test_{test_number}.json", selected)

        used_ids.update(selected_ids)
        rf_state["used_question_ids"] = list(used_ids)
        save_json(REAL_FEEL_STATE_PATH, rf_state)

        available["tests"].append(test_number)
        save_json(available_ids_path, available)

        # remove selected from pool so the next loop iteration draws fresh
        pool = [(q, w) for q, w in pool if q["question_id"] not in selected_ids]
        tests_built_this_run += 1

    return tests_built_this_run, rf_state["tests_built"]


def run():
    start_time = time.time()

    print(f"Program: {PROGRAM}")

    # GitHub Pages only serves what's inside PUBLISHED_DIR - assets/ lives at
    # repo root as a sibling, shared across all programs, so it must be
    # copied in on every run to be reachable.
    assets_src = Path("assets")
    if assets_src.exists():
        shutil.copytree(assets_src, PUBLISHED_DIR / "assets", dirs_exist_ok=True)
        print(f"📦 Copied {assets_src} -> {PUBLISHED_DIR / 'assets'}")
    else:
        print(f"⚠️  No {assets_src} folder found at repo root - CSS/JS will be missing.")

    if CBT_APP_SRC.exists():
        shutil.copytree(CBT_APP_SRC, PUBLISHED_DIR / "cbt", dirs_exist_ok=True)
        print(f"📦 Copied {CBT_APP_SRC} -> {PUBLISHED_DIR / 'cbt'}")

    if QUESTIONS_DIR.exists():
        shutil.copytree(QUESTIONS_DIR, PUBLISHED_DIR / "data" / "questions", dirs_exist_ok=True)
        print(f"📦 Copied {QUESTIONS_DIR} -> {PUBLISHED_DIR / 'data' / 'questions'}")

    if REAL_FEEL_CONFIG_PATH.exists():
        rf_config = load_json(REAL_FEEL_CONFIG_PATH, {})
        save_json(PUBLISHED_DIR / "data" / "real_feel_config.json", rf_config)

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
            print(f"⚠️  {topic_id} not found in curriculum. Skipping.")
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
                    "topic_id": t["topic_id"],
                    "title": t["title"],
                    "course": c_data["course_name"],
                    "course_slug": c_slug,
                    "unit": u_data["unit_name"],
                    "url": f"{c_slug}/{u_slug}/{t['topic_id']}.html",
                })
    save_json(PUBLISHED_DIR / "site_index.json", site_index)

    # ---- CBT: course pools + real-feel exams ----
    course_pools = build_course_pools(courses, QUESTIONS_DIR)

    for c_slug, units in course_pools.items():
        flat_questions = [q for qs in units.values() for q in qs]
        save_json(PUBLISHED_DIR / "data" / "course_pools" / f"{c_slug}.json", flat_questions)

    tests_built_this_run, total_tests = build_real_feel_tests(course_pools)

    print(f"\n🏁 Run complete. Built {processed_this_run} new article page(s) this run.")
    print(f"   Total published: {len(published_ids)}/{len(available_ids)}")
    print(f"   Navigation rebuilt for {len(courses)} course(s).")
    print(f"   Real-feel exams: {tests_built_this_run} new this run, {total_tests} total available.")


if __name__ == "__main__":
    run()
