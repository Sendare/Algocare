from pathlib import Path

print("🚀 Fixing Modal CSS and Loop Persistence...")

# ==========================================
# 1. ADD MODAL CSS
# ==========================================
css_path = Path("cbt-app/exam.css")
css = css_path.read_text()

modal_css = """
/* Modal Overlay */
.modal-overlay { 
    position: fixed; 
    top: 0; left: 0; right: 0; bottom: 0; 
    background: rgba(0,0,0,0.8); 
    display: flex; 
    align-items: center; 
    justify-content: center; 
    z-index: 9999; 
}
.modal-content { 
    background: #18181b; 
    padding: 24px; 
    border-radius: 12px; 
    border: 1px solid #27272a; 
    max-width: 400px; 
    width: 90%; 
    text-align: center; 
    color: white; 
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
}
.modal-content h2 { color: #f59e0b; margin-top: 0; font-size: 1.5rem; }
.modal-content p { color: #a1a1aa; margin-bottom: 24px; font-size: 1rem; }
.modal-actions { display: flex; gap: 12px; justify-content: center; }
"""
if ".modal-overlay" not in css:
    css += modal_css
    css_path.write_text(css)
    print("✅ Added Modal CSS")

# ==========================================
# 2. FIX THE LOOP (Remove reset in selectAnswer)
# ==========================================
for js_file in ["exam_v2.js", "practice_v2.js"]:
    path = Path(f"cbt-app/js/{js_file}")
    if not path.exists(): continue
    src = path.read_text()

    # Remove isCatchingSkips = false; from selectAnswer so the loop persists
    src = src.replace(
        "function selectAnswer(k) { answers[questions[current].question_id] = k; isCatchingSkips = false; saveState(); render(); }",
        "function selectAnswer(k) { answers[questions[current].question_id] = k; saveState(); render(); }"
    )
    src = src.replace(
        "isCatchingSkips = false; \n  saveState(); render(); \n}",
        "saveState(); render(); \n}"
    )
    # In practice_v2.js it's slightly different
    src = src.replace(
        "isCatchingSkips = false; \n  saveState(); render(); \n}",
        "saveState(); render(); \n}"
    )
    
    path.write_text(src)
    print(f"✅ Fixed loop persistence in {js_file}")
