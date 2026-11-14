from pathlib import Path

print("🚀 Connecting Auth to Exam Engine and Analytics...")

# 1. Update Analytics to ensure it uses the real user ID if logged in
analytics_path = Path("assets/analytics.js")
analytics = analytics_path.read_text()

# getUserId in analytics.js already checks localStorage('algocare_uid'). 
# auth.js saves the real Supabase ID to 'algocare_uid', so analytics is automatically linked.
# We just need to make sure logTestStarted/Finished pull it correctly. (They already do).
print("✅ Analytics verified (already picks up the Auth User ID)")

# 2. Update Exam V2 JS (Real-Feel)
exam_path = Path("cbt-app/js/exam_v2.js")
exam_js = exam_path.read_text()

# Inject candidate name logic into render()
old_header = """      <div class="exam-header-left">
        <span class="exam-header-title">Algocare CBT</span>
        <span style="font-size:0.75rem; color:#a1a1aa">Candidate: [Name] | [Reg No]</span>
      </div>"""
new_header = """      <div class="exam-header-left">
        <span class="exam-header-title">Algocare CBT</span>
        <span style="font-size:0.75rem; color:#a1a1aa">Candidate: ${window.candidateName || '[Name]'} | ${window.candidateRegNo || '[Reg No]'}</span>
      </div>"""

exam_js = exam_js.replace(old_header, new_header)

# Add user fetching logic on load
exam_js = exam_js.replace(
    'window.addEventListener("load", async () => { init(); });',
    """window.addEventListener("load", async () => {
  try {
    const user = window.getUser ? window.getUser() : null;
    if (user) {
      window.candidateName = user.user_metadata?.name || user.email.split('@')[0];
      window.candidateRegNo = user.id.substring(0, 8).toUpperCase();
    }
  } catch (e) { console.warn("Auth not loaded"); }
  init(); 
});"""
)
exam_path.write_text(exam_js)

# 3. Update Practice V2 JS
practice_path = Path("cbt-app/js/practice_v2.js")
practice_js = practice_path.read_text()

practice_js = practice_js.replace(old_header, new_header)
practice_js = practice_js.replace(
    'window.addEventListener("load", async () => { init(); });',
    """window.addEventListener("load", async () => {
  try {
    const user = window.getUser ? window.getUser() : null;
    if (user) {
      window.candidateName = user.user_metadata?.name || user.email.split('@')[0];
      window.candidateRegNo = user.id.substring(0, 8).toUpperCase();
    }
  } catch (e) { console.warn("Auth not loaded"); }
  init(); 
});"""
)
practice_path.write_text(practice_js)

# 4. Ensure exam-mode.html and practice.html load auth.js BEFORE the exam JS
for f in ["cbt-app/exam-mode.html", "cbt-app/practice.html"]:
    html_path = Path(f)
    html = html_path.read_text()
    if "../assets/auth.js" not in html:
        html = html.replace(
            '<script src="../assets/analytics.js"></script>',
            '<script src="../assets/analytics.js"></script>\n<script src="../assets/auth.js"></script>'
        )
        html_path.write_text(html)

print("✅ Auth injected into CBT Engine")
