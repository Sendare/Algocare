from pathlib import Path
import shutil

print("🚀 Fixing Header Name rendering, Topic routing, and Cache Busting...")

# ==========================================
# 1. FIX HEADER NAME IN EXAM JS
# ==========================================
for js_file in ["exam_v2.js", "practice_v2.js"]:
    path = Path(f"cbt-app/js/{js_file}")
    if not path.exists(): continue
    src = path.read_text()

    # Update the load listener to directly modify the DOM header
    old_load = """window.addEventListener("load", async () => {
  await new Promise(r => setTimeout(r, 200));
  try {
    const user = window.getUser ? window.getUser() : null;
    if (user) {
      window.candidateName = user.user_metadata?.name || user.email.split('@')[0];
      window.candidateRegNo = user.id.substring(0, 8).toUpperCase();
    }
  } catch (e) { console.warn("Auth loading error"); }
  init(); 
});"""
    
    new_load = """window.addEventListener("load", async () => {
  await new Promise(r => setTimeout(r, 200));
  try {
    const user = window.getUser ? window.getUser() : null;
    if (user) {
      const name = user.user_metadata?.name || user.email.split('@')[0];
      const regNo = user.id.substring(0, 8).toUpperCase();
      // Find the candidate span in the header and update it directly
      const headerSpan = document.querySelector('.exam-header-left span:nth-child(2)');
      if (headerSpan) headerSpan.textContent = `Candidate: ${name} | ${regNo}`;
    }
  } catch (e) { console.warn("Auth loading error:", e); }
  init(); 
});"""
    
    src = src.replace(old_load, new_load)
    path.write_text(src)
    print(f"✅ Fixed header name rendering in {js_file}")

# ==========================================
# 2. FIX AUTH.JS LOGGING (To debug topbar)
# ==========================================
auth_path = Path("assets/auth.js")
auth_src = auth_path.read_text()
auth_src = auth_src.replace(
    'const authSlot = document.getElementById("authSlot");\n  if (!authSlot) return;',
    'const authSlot = document.getElementById("authSlot");\n  if (!authSlot) return console.log("AuthSlot not found on this page.");'
)
auth_path.write_text(auth_src)
shutil.copy2(auth_path, "docs/assets/auth.js")

# ==========================================
# 3. ENSURE CBT HTML HAS THE DYNAMIC HEADER SPAN
# ==========================================
for f in ["cbt-app/exam-mode.html", "cbt-app/practice.html"]:
    p = Path(f)
    src = p.read_text()
    # Ensure the span has the class/selector we are targeting
    if "Candidate: [Name]" in src:
        src = src.replace(
            '<span style="font-size:0.75rem; color:#a1a1aa">Candidate: [Name] | [Reg No]</span>',
            '<span style="font-size:0.75rem; color:#a1a1aa" id="candidateInfo">Candidate: [Name] | [Reg No]</span>'
        )
        p.write_text(src)
        print(f"✅ Added ID to candidate span in {f}")

# Update JS to target the ID instead of nth-child
for js_file in ["exam_v2.js", "practice_v2.js"]:
    path = Path(f"cbt-app/js/{js_file}")
    src = path.read_text()
    src = src.replace(
        "const headerSpan = document.querySelector('.exam-header-left span:nth-child(2)');",
        "const headerSpan = document.getElementById('candidateInfo');"
    )
    path.write_text(src)

# ==========================================
# 4. BUMP SERVICE WORKER TO FORCE CACHE CLEAR
# ==========================================
sw_path = Path("assets/sw-template.js")
if sw_path.exists():
    sw = sw_path.read_text()
    # Replace any previous version bump with v100
    import re
    sw = re.sub(r"algocare-v\d+-", "algocare-v100-", sw)
    sw = sw.replace("algocare-${BUILD_ID}", "algocare-v100-${BUILD_ID}")
    sw_path.write_text(sw)
    print("✅ Bumped Service Worker to v100 to destroy phone cache")

print("🎉 Done.")
