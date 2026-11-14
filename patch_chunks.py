from pathlib import Path

bp = Path("scripts/build.py")
src = bp.read_text()

# Find the main() function and replace it
start_idx = src.find("def main():")
if start_idx == -1:
    print("❌ Could not find main() in build.py")
    exit(1)

new_main = '''def main():
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else "all"
    print(f"🚀 Starting Master Build (Target: {target})...")
    
    if target == "all" or target == "root":
        print("📁 Creating root folder structure...")
        if DOCS_DIR.exists(): shutil.rmtree(DOCS_DIR)
        DOCS_DIR.mkdir()
        for page in ["index.html", "login.html", "signup.html", "dashboard.html", "leaderboard.html"]:
            src = TEMPLATES_DIR / page
            if src.exists(): shutil.copy2(src, DOCS_DIR / page)
        shutil.copytree(ASSETS_DIR, DOCS_DIR / "assets")

    progs = PROGRAMS if target == "all" else [target] if target in PROGRAMS else []
    
    for prog in progs:
        print(f"\\n📚 Building Program: {prog}")
        
        # Ensure dirs
        (DOCS_DIR / prog).mkdir(parents=True, exist_ok=True)
        (DOCS_DIR / prog / "data").mkdir(exist_ok=True)
        
        # Copy assets & CBT pages
        if not (DOCS_DIR / prog / "assets").exists():
            shutil.copytree(ASSETS_DIR, DOCS_DIR / prog / "assets")
            
        (DOCS_DIR / prog / "cbt").mkdir(exist_ok=True)
        for page in ["practice-setup.html", "exam-setup.html", "exam.html"]:
            src = TEMPLATES_DIR / page
            if src.exists(): shutil.copy2(src, DOCS_DIR / prog / "cbt" / page)
            
        # Copy question data
        if Path(f"data/{prog}/questions").exists():
            q_dest = DOCS_DIR / prog / "data" / "questions"
            if not q_dest.exists():
                shutil.copytree(f"data/{prog}/questions", q_dest)
                
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

    print("\\n🎉 Build Complete! Deploy the 'docs' folder.")

if __name__ == "__main__":
    main()'''

src = src[:start_idx] + new_main
bp.write_text(src)
print("✅ Patched scripts/build.py for chunking")
