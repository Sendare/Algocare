from pathlib import Path
import shutil

print("🚀 Fixing CSS paths, Practice topic redirect, and Candidate Name...")

# ==========================================
# 1. FIX ASSET PATHS IN ROOT PAGES (Dashboard, Login, etc.)
# ==========================================
# We revert from absolute /assets/ to relative ./assets/ 
# Because these files sit in the root of docs/, ./assets/ works perfectly.
for f in ["docs/dashboard.html", "docs/index.html", "docs/login.html", "docs/signup.html"]:
    p = Path(f)
    if not p.exists(): continue
    html = p.read_text()
    html = html.replace('href="/assets/style.css"', 'href="./assets/style.css"')
    html = html.replace('src="/assets/auth.js"', 'src="./assets/auth.js"')
    p.write_text(html)
    print(f"✅ Fixed relative CSS/JS paths in {f}")

# ==========================================
# 2. FIX PRACTICE ENGINE TO SUPPORT ?topic=
# ==========================================
practice_path = Path("cbt-app/js/practice_v2.js")
src = practice_path.read_text()

# Add topic handling in the init() logic
old_init = """      if (!coursesParam) { document.getElementById("examRoot").innerHTML = `<div class="empty-state" style="color:#a1a1aa; text-align:center; padding:40px;">No courses specified. <a href="index.html">Go back</a></div>`; return; }
      
      const courseSlugs = coursesParam.split(',');"""
new_init = """      const topicId = params.get("topic");
      if (topicId) {
        // Single topic mode (from article CTA)
        const pool = await (await fetch(`../data/questions/${topicId}.json`)).json();
        subjects = ["Topic Practice"];
        questions["Topic Practice"] = shuffle(pool);
        currentIndexes["Topic Practice"] = 0;
        activeSubject = "Topic Practice";
        // Default to 20 questions or the pool size
        const limit = requestedCount || 20;
        questions["Topic Practice"] = questions["Topic Practice"].slice(0, Math.min(limit, pool.length));
        endTime = Date.now() + questions["Topic Practice"].length * secondsPerQuestion * 1000;
        attemptId = generateAttemptId();
        saveState();
        logTestStarted(attemptId, "practice", topicId, questions["Topic Practice"].length);
      } else if (coursesParam) {
        const courseSlugs = coursesParam.split(',');"""
        
src = src.replace(old_init, new_init)

# Fix the closing bracket for the `else` block after the loop
src = src.replace(
    """      activeSubject = subjects[0];
      endTime = Date.now() + totalAllowed * secondsPerQuestion * 1000;
      attemptId = generateAttemptId();
      saveState();
      logTestStarted(attemptId, "practice", coursesParam, totalAllowed);
    }""",
    """      activeSubject = subjects[0];
      endTime = Date.now() + totalAllowed * secondsPerQuestion * 1000;
      attemptId = generateAttemptId();
      saveState();
      logTestStarted(attemptId, "practice", coursesParam, totalAllowed);
      }
    }"""
)
practice_path.write_text(src)
print("✅ Added ?topic= support to Practice Engine")

# ==========================================
# 3. FIX CANDIDATE NAME RENDERING IN HEADERS
# ==========================================
# We will move the user fetching logic to the top of the script, 
# and use a small `setTimeout` to ensure the DOM is fully ready.
for js_file in ["exam_v2.js", "practice_v2.js"]:
    path = Path(f"cbt-app/js/{js_file}")
    if not path.exists(): continue
    src = path.read_text()

    # Replace the window load listener with a more robust approach
    src = src.replace(
        """window.addEventListener("load", async () => {
  try {
    const user = window.getUser ? window.getUser() : null;
    if (user) {
      window.candidateName = user.user_metadata?.name || user.email.split('@')[0];
      window.candidateRegNo = user.id.substring(0, 8).toUpperCase();
    }
  } catch (e) { console.warn("Auth not loaded"); }
  init(); 
});""",
        """window.addEventListener("load", async () => {
  // Wait a tiny bit for auth.js to parse the session
  await new Promise(r => setTimeout(r, 150));
  try {
    const user = window.getUser ? window.getUser() : null;
    if (user) {
      window.candidateName = user.user_metadata?.name || user.email.split('@')[0];
      window.candidateRegNo = user.id.substring(0, 8).toUpperCase();
    }
  } catch (e) { console.warn("Auth loading error:", e); }
  init(); 
});"""
    )
    path.write_text(src)
print("✅ Added robust user name fetching to Exam headers")

# ==========================================
# 4. ENSURE AUTH.JS IS LOADED ON ARTICLE PAGES
# ==========================================
bp = Path("build_pages.py")
src = bp.read_text()

# The previous patch added auth.js to PAGE_HEAD, but the path might be broken.
# Let's fix the path to use the same relative logic as analytics.js
if 'src="{root_rel}assets/auth.js"' in src:
    # This is fine, but we need to ensure the file actually exists in docs/assets
    pass
else:
    # If the patch didn't apply correctly, inject it now
    src = src.replace(
        '<script src="{rel}assets/analytics.js"></script>',
        '<script src="{rel}assets/analytics.js"></script>\n<script src="{root_rel}assets/auth.js"></script>'
    )
    bp.write_text(src)
    print("✅ Re-injected auth.js into PAGE_HEAD")

# ==========================================
# 5. FORCE SYNC ASSETS TO DOCS/ASSETS
# ==========================================
docs_assets = Path("docs/assets")
docs_assets.mkdir(parents=True, exist_ok=True)
for f in ["style.css", "auth.js", "analytics.js"]:
    if Path(f"assets/{f}").exists():
        shutil.copy2(f"assets/{f}", docs_assets / f)
print("✅ Synced assets to docs/assets/")

print("🎉 All fixes applied.")
