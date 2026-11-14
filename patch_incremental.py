from pathlib import Path
import json

bp = Path("scripts/build.py")
src = bp.read_text()

# Replace the article generation block with an incremental version
old_block = """        published = []
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
                courses[ctx["course_slug"]]["units"][ctx["unit_slug"]]["topics"].append({"topic_id": topic_id, "title": ctx["title"], "order": ctx["order"]})"""

new_block = """        state_file = ROOT_DIR / "state" / prog / "build_state.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        state_data = load_json(state_file, {"published_done": []})
        published_done = set(state_data["published_done"])
        
        published = []
        courses = {}
        
        articles_dir = Path(f"data/{prog}/articles")
        all_articles = list(articles_dir.glob("*.json")) if articles_dir.exists() else []
        pending_articles = [a for a in all_articles if a.stem not in published_done]
        
        if not pending_articles:
            print(f"  ✅ All {len(all_articles)} articles already built for {prog}.")
            print("ALL_DONE")
            # We still need to build nav and real-feel, so we don't return yet
        else:
            batch = pending_articles[:100]
            print(f"  📦 Processing batch of {len(batch)} articles (Total remaining: {len(pending_articles)})...")
            
            for a_file in batch:
                topic_id = a_file.stem
                ctx = ctx_lookup.get(topic_id)
                if not ctx: continue
                
                article = load_json(a_file, None)
                if not article: continue
                
                write_html(DOCS_DIR / prog / ctx["course_slug"] / ctx["unit_slug"] / f"{topic_id}.html", render_article_page(article, ctx))
                published.append(topic_id)
                published_done.add(topic_id)
                
            # Save state
            state_data["published_done"] = list(published_done)
            save_json(state_file, state_data)
            print(f"  💾 Saved state: {len(published_done)} total published.")

        # Rebuild navigation and index based on *all* published articles (from state)
        published = list(published_done)
        for topic_id in published:
            ctx = ctx_lookup.get(topic_id)
            if not ctx: continue
            courses.setdefault(ctx["course_slug"], {"course_name": ctx["course_name"], "units": {}})
            courses[ctx["course_slug"]]["units"].setdefault(ctx["unit_slug"], {"unit_name": ctx["unit_name"], "topics": []})
            courses[ctx["course_slug"]]["units"][ctx["unit_slug"]]["topics"].append({"topic_id": topic_id, "title": ctx["title"], "order": ctx["order"]})"""

if old_block in src:
    src = src.replace(old_block, new_block)
    # If ALL_DONE is printed, we still want to rebuild nav and real-feel, but we need to tell the YAML to stop.
    # We can use an environment variable or a specific print statement.
    # Let's just print "ALL_DONE" at the end of the loop, but only if pending_articles was empty.
    
    # Actually, to make the bash loop work smoothly, if there are no pending articles, we should still build nav/exams, then exit 0.
    # Let's adjust the end of the file to handle this.
    
    src = src.replace(
        '''        build_real_feel_tests(prog)
        print(f"  ✅ Built {len(published)} articles and generated exams for {prog}")''',
        '''        build_real_feel_tests(prog)
        print(f"  ✅ Generated exams and navigation for {prog}")
        
        if not pending_articles:
            print("BATCH_COMPLETE_ALL_DONE")
        else:
            print("BATCH_COMPLETE_MORE_REMAINING")'''
    )
    bp.write_text(src)
    print("✅ Patched scripts/build.py for incremental 100-file batches")
else:
    print("⚠️ Could not find the article generation block. Did you modify it?")
