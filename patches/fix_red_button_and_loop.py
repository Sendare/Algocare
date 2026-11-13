from pathlib import Path

print("🚀 Removing red button, shrinking buttons, fixing loop...")

# ==========================================
# 1. UPDATE CSS (Smaller buttons)
# ==========================================
css_path = Path("cbt-app/exam.css")
css = css_path.read_text()

# Shrink buttons
css = css.replace(
    ".exam-btn { \n    flex: 1; \n    padding: 10px 16px !important; \n    border-radius: 6px; \n    font-weight: 700; \n    font-size: 0.9rem !important; \n    border: none; \n    cursor: pointer; \n    display: flex; \n    justify-content: center; \n    align-items: center; \n    gap: 8px; \n}",
    ".exam-btn { \n    flex: 1; \n    padding: 6px 12px !important; \n    border-radius: 6px; \n    font-weight: 700; \n    font-size: 0.8rem !important; \n    border: none; \n    cursor: pointer; \n    display: flex; \n    justify-content: center; \n    align-items: center; \n    gap: 4px; \n}"
)
# Also handle if the format is different
css = css.replace("padding: 10px 16px !important;", "padding: 6px 12px !important;")
css = css.replace("font-size: 0.9rem !important;", "font-size: 0.8rem !important;")

css_path.write_text(css)
print("✅ Buttons shrunk in exam.css")

# ==========================================
# 2. UPDATE JS (Remove Red Button, Fix Loop)
# ==========================================
for js_file in ["exam_v2.js", "practice_v2.js"]:
    path = Path(f"cbt-app/js/{js_file}")
    if not path.exists(): continue
    src = path.read_text()

    # A. Remove the red submit button from the bottom actions
    # It matches this chunk in the HTML template inside render()
    src = src.replace(
        """<button class="exam-btn exam-btn-submit" onclick="finishExam()" ${canSubmit ? "" : "disabled"} style="margin-left:auto; background: #ef4444; color: white;">Submit Exam ${canSubmit ? "" : `(need ${config.min_answered_to_submit - answeredCount()} more)`}</button>""",
        ""
    )
    src = src.replace(
        """<button class="exam-btn exam-btn-submit" onclick="finishTest(true)" ${canSubmit ? "" : "disabled"} style="margin-left:auto; background: #ef4444; color: white;">Submit Exam ${canSubmit ? "" : `(need ${config.min_answered_to_submit - answeredCount()} more)`}</button>""",
        ""
    )
    # Just in case the patch script didn't catch the exact string
    src = src.replace(
        """<button class="exam-btn exam-btn-submit" onclick="finishExam()" ${canSubmit ? "" : "disabled"} style="margin-left:auto; background: #ef4444; color: white;">Submit Exam</button>""",
        ""
    )
    
    # B. Fix the Catch Skips loop (nextQ function)
    # We replace the whole nextQ function to ensure it triggers on the last question too
    old_nextQ = """function nextQ() {
  if (isCatchingSkips) {
    let targetIndex = -1;
    for (let i = current + 1; i < questions.length; i++) { if (!answers[questions[i].question_id]) { targetIndex = i; break; } }
    if (targetIndex === -1) {
      for (let i = 0; i < current; i++) { if (!answers[questions[i].question_id]) { targetIndex = i; break; } }
    }
    if (targetIndex !== -1) { jumpTo(targetIndex); isCatchingSkips = true; showToast("Jumped to next unanswered"); }
    else { handleSubmitClick(); }
    return;
  }
  if (current < questions.length - 1) { jumpTo(current + 1); }
}"""
    
    new_nextQ = """function nextQ() {
  // Trigger catch skips if we are already doing it, OR if we are on the very last question
  if (isCatchingSkips || current === questions.length - 1) {
    let targetIndex = -1;
    
    // Search forward from current position
    for (let i = current + 1; i < questions.length; i++) { 
      if (!answers[questions[i].question_id]) { targetIndex = i; break; } 
    }
    
    // If not found forward, search from the beginning
    if (targetIndex === -1) {
      for (let i = 0; i <= current; i++) { 
        if (!answers[questions[i].question_id]) { targetIndex = i; break; } 
      }
    }
    
    if (targetIndex !== -1) { 
      jumpTo(targetIndex); 
      isCatchingSkips = true; 
      showToast("Jumped to next unanswered"); 
    } else { 
      handleSubmitClick(); 
    }
    return;
  }
  
  // Normal sequential next
  if (current < questions.length - 1) { 
    jumpTo(current + 1); 
  }
}"""
    
    if old_nextQ in src:
        src = src.replace(old_nextQ, new_nextQ)
    else:
        # If the exact string doesn't match (e.g. it was formatted differently), use regex
        import re
        src = re.sub(r"function nextQ\(\) \{.*?\n\}", new_nextQ, src, flags=re.DOTALL)

    # C. Clear isCatchingSkips when an answer is selected so it doesn't get stuck
    src = src.replace(
        "function selectAnswer(k) { answers[current] = k; saveState(); render(); }",
        "function selectAnswer(k) { answers[current] = k; isCatchingSkips = false; saveState(); render(); }"
    )
    src = src.replace(
        "function selectAnswer(k) { answers[current] = { selected: k, isCorrect: k === questions[current].answer, showExplanation: false }; saveState(); render(); }",
        "function selectAnswer(k) { answers[current] = { selected: k, isCorrect: k === questions[current].answer, showExplanation: false }; isCatchingSkips = false; saveState(); render(); }"
    )

    path.write_text(src)
    print(f"✅ Fixed nextQ loop and removed red button in {js_file}")

print("🎉 Done.")
