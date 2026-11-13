#!/usr/bin/env python3
from pathlib import Path
import re

print("🚀 Starting Phase 4: Auth, Dashboard, and Homepage...")

# ==========================================
# 1. CREATE AUTH JS
# ==========================================
auth_js = """
const SUPABASE_URL = "https://uhrjtcocwejddtzyjyhr.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_C_i1zk4P2phfIALmI6C7Iw_pYSMTGfQ";

// Save session to localStorage
function saveSession(data) {
  if (data && data.access_token) {
    localStorage.setItem("algocare_session", JSON.stringify({
      access_token: data.access_token,
      refresh_token: data.refresh_token,
      user: data.user
    }));
  }
}

function getSession() {
  try {
    const raw = localStorage.getItem("algocare_session");
    return raw ? JSON.parse(raw) : null;
  } catch { return null; }
}

function getUser() {
  const session = getSession();
  return session ? session.user : null;
}

async function signUp(name, email, password) {
  const res = await fetch(`${SUPABASE_URL}/auth/v1/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "apikey": SUPABASE_ANON_KEY },
    body: JSON.stringify({ email, password, data: { name } })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.msg || data.error_description || "Signup failed");
  
  // If email confirmation is off, the session is returned immediately
  if (data.access_token) {
    saveSession(data);
    // Link anonymous analytics to this user ID
    localStorage.setItem("algocare_uid", data.user.id);
  }
  return data;
}

async function logIn(email, password) {
  const res = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=password`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "apikey": SUPABASE_ANON_KEY },
    body: JSON.stringify({ email, password })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error_description || data.msg || "Login failed");
  
  saveSession(data);
  localStorage.setItem("algocare_uid", data.user.id);
  return data;
}

function logOut() {
  localStorage.removeItem("algocare_session");
  window.location.href = "/"; // Redirect to homepage
}

// Automatically update the topbar if the authSlot exists
document.addEventListener("DOMContentLoaded", () => {
  const authSlot = document.getElementById("authSlot");
  if (!authSlot) return;
  
  const user = getUser();
  if (user) {
    const name = user.user_metadata?.name || user.email.split('@')[0];
    authSlot.innerHTML = `
      <a href="/dashboard.html" style="font-weight:600; color:var(--scrub); text-decoration:none; margin-right:12px;">My Dashboard</a>
      <button onclick="logOut()" style="background:none; border:none; color:var(--ink-soft); cursor:pointer; font-size:0.85rem;">Log out</button>
    `;
  } else {
    authSlot.innerHTML = `
      <a href="/login.html" style="font-weight:600; color:var(--scrub); text-decoration:none;">Log In</a>
    `;
  }
});
"""
Path("assets/auth.js").write_text(auth_js)

# ==========================================
# 2. CREATE LOGIN & SIGNUP PAGES
# ==========================================
auth_page_style = """
<style>
.auth-container { max-width: 400px; margin: 60px auto; padding: 32px; background: var(--card); border: 1px solid var(--grey-line); border-radius: 12px; box-shadow: var(--shadow); }
.auth-container h2 { text-align: center; margin-bottom: 24px; font-size: 1.5rem; }
.auth-error { background: var(--brick-soft); color: var(--brick); padding: 10px; border-radius: 6px; font-size: 0.85rem; margin-bottom: 16px; display: none; }
.auth-input-group { margin-bottom: 16px; }
.auth-input-group label { display: block; font-family: var(--mono); font-size: 0.75rem; text-transform: uppercase; color: var(--grey); margin-bottom: 6px; }
.auth-input-group input { width: 100%; padding: 12px; border: 1px solid var(--grey-line); border-radius: 6px; background: var(--paper); box-sizing: border-box; }
.auth-btn { width: 100%; padding: 12px; background: var(--scrub); color: #fff; border: none; border-radius: 6px; font-weight: 700; cursor: pointer; font-size: 1rem; margin-top: 8px; }
.auth-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.auth-links { text-align: center; margin-top: 20px; font-size: 0.85rem; color: var(--ink-soft); }
.auth-links a { color: var(--scrub); font-weight: 600; text-decoration: none; }
</style>
"""

login_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Log In — Algocare</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css">
{auth_page_style}
</head>
<body>
<div class="topbar"><div class="brand"><span class="pulse-dot"></span>Algocare</div></div>
<div class="auth-container">
  <h2>Welcome Back</h2>
  <div id="authError" class="auth-error"></div>
  <form id="loginForm">
    <div class="auth-input-group">
      <label>Email</label>
      <input type="email" id="email" required placeholder="you@example.com">
    </div>
    <div class="auth-input-group">
      <label>Password</label>
      <input type="password" id="password" required placeholder="••••••••">
    </div>
    <button type="submit" class="auth-btn" id="submitBtn">Log In</button>
  </form>
  <div class="auth-links">
    Don't have an account? <a href="signup.html">Sign Up</a>
  </div>
</div>
<script src="assets/auth.js"></script>
<script>
  document.getElementById("loginForm").addEventListener("submit", async (e) => {{
    e.preventDefault();
    const btn = document.getElementById("submitBtn");
    const err = document.getElementById("authError");
    btn.disabled = true; btn.textContent = "Logging in..."; err.style.display = "none";
    try {{
      await logIn(document.getElementById("email").value, document.getElementById("password").value);
      window.location.href = "dashboard.html";
    }} catch (error) {{
      err.textContent = error.message; err.style.display = "block";
      btn.disabled = false; btn.textContent = "Log In";
    }}
  }});
</script>
</body>
</html>"""

signup_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Sign Up — Algocare</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css">
{auth_page_style}
</head>
<body>
<div class="topbar"><div class="brand"><span class="pulse-dot"></span>Algocare</div></div>
<div class="auth-container">
  <h2>Create Account</h2>
  <div id="authError" class="auth-error"></div>
  <form id="signupForm">
    <div class="auth-input-group">
      <label>Full Name</label>
      <input type="text" id="name" required placeholder="John Doe">
    </div>
    <div class="auth-input-group">
      <label>Email</label>
      <input type="email" id="email" required placeholder="you@example.com">
    </div>
    <div class="auth-input-group">
      <label>Password</label>
      <input type="password" id="password" required placeholder="••••••••">
    </div>
    <div class="auth-input-group">
      <label>Confirm Password</label>
      <input type="password" id="confirmPassword" required placeholder="••••••••">
    </div>
    <button type="submit" class="auth-btn" id="submitBtn">Sign Up</button>
  </form>
  <div class="auth-links">
    Already have an account? <a href="login.html">Log In</a>
  </div>
</div>
<script src="assets/auth.js"></script>
<script>
  document.getElementById("signupForm").addEventListener("submit", async (e) => {{
    e.preventDefault();
    const btn = document.getElementById("submitBtn");
    const err = document.getElementById("authError");
    const pass = document.getElementById("password").value;
    const confirmPass = document.getElementById("confirmPassword").value;
    
    if (pass !== confirmPass) {{
      err.textContent = "Passwords do not match."; err.style.display = "block"; return;
    }}
    
    btn.disabled = true; btn.textContent = "Creating..."; err.style.display = "none";
    try {{
      const data = await signUp(document.getElementById("name").value, document.getElementById("email").value, pass);
      // If email confirmation is on, there won't be a session, so redirect to login
      if (data.access_token) {{ window.location.href = "dashboard.html"; }}
      else {{ alert("Check your email for a confirmation link!"); window.location.href = "login.html"; }}
    }} catch (error) {{
      err.textContent = error.message; err.style.display = "block";
      btn.disabled = false; btn.textContent = "Sign Up";
    }}
  }});
</script>
</body>
</html>"""

Path("docs/login.html").write_text(login_html)
Path("docs/signup.html").write_text(signup_html)

# ==========================================
# 3. CREATE DASHBOARD
# ==========================================
dashboard_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard — Algocare</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css">
<style>
.dashboard-container { max-width: 800px; margin: 0 auto; padding: 24px 20px; }
.program-switcher { display: flex; gap: 8px; margin-bottom: 24px; overflow-x: auto; padding-bottom: 8px; }
.prog-tab { padding: 10px 20px; background: var(--card); border: 1px solid var(--grey-line); border-radius: 6px; font-weight: 600; cursor: pointer; color: var(--ink-soft); white-space: nowrap; }
.prog-tab.active { background: var(--scrub); color: #fff; border-color: var(--scrub); }
.mode-grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
@media (min-width: 600px) { .mode-grid { grid-template-columns: 1fr 1fr; } }
.mode-card { background: var(--card); padding: 24px; border-radius: 12px; border: 1px solid var(--grey-line); text-decoration: none; color: var(--ink); transition: all 0.2s; display: flex; flex-direction: column; gap: 8px; }
.mode-card:hover { border-color: var(--scrub); transform: translateY(-2px); box-shadow: 0 4px 12px rgba(47,111,98,0.1); }
.mode-card h3 { margin: 0; font-size: 1.1rem; color: var(--scrub); }
.mode-card p { margin: 0; font-size: 0.85rem; color: var(--ink-soft); }
.mode-icon { font-size: 2rem; margin-bottom: 8px; }
</style>
</head>
<body>
<div class="topbar">
  <div class="brand"><span class="pulse-dot"></span>Algocare</div>
  <div id="authSlot"></div>
</div>

<div class="dashboard-container">
  <h1 style="margin-bottom: 4px;">My Dashboard</h1>
  <p style="color: var(--ink-soft); margin-bottom: 24px; margin-top: 0;">Select a program to start studying.</p>

  <div class="program-switcher" id="programSwitcher">
    <button class="prog-tab active" data-prog="nursing">Basic Nursing</button>
    <button class="prog-tab" data-prog="midwifery">Basic Midwifery</button>
  </div>

  <div class="mode-grid">
    <a href="#" id="link-articles" class="mode-card">
      <div class="mode-icon">📚</div>
      <h3>Study Articles</h3>
      <p>Read topics and test yourself on specific concepts.</p>
    </a>
    <a href="#" id="link-practice" class="mode-card">
      <div class="mode-icon">🎯</div>
      <h3>Practice Mode</h3>
      <p>Take custom practice tests by selecting specific courses.</p>
    </a>
    <a href="#" id="link-realfeel" class="mode-card" style="grid-column: 1 / -1;">
      <div class="mode-icon">⏱️</div>
      <h3>Real-Feel Exam</h3>
      <p>Simulate the actual CBT exam with 250 mixed questions and a strict timer.</p>
    </a>
  </div>
</div>

<script src="assets/auth.js"></script>
<script>
  const user = getUser();
  if (!user) window.location.href = "login.html";

  let activeProg = localStorage.getItem("algocare_dashboard_prog") || "nursing";

  function updateLinks(prog) {
    document.getElementById("link-articles").href = `/${prog}/index.html`;
    document.getElementById("link-practice").href = `/${prog}/cbt/index.html`;
    document.getElementById("link-realfeel").href = `/${prog}/cbt/index.html#realfeel`;
    
    document.querySelectorAll(".prog-tab").forEach(tab => {
      tab.classList.toggle("active", tab.dataset.prog === prog);
    });
    localStorage.setItem("algocare_dashboard_prog", prog);
  }

  document.querySelectorAll(".prog-tab").forEach(tab => {
    tab.addEventListener("click", () => updateLinks(tab.dataset.prog));
  });

  // Initialize
  updateLinks(activeProg);
</script>
</body>
</html>"""
Path("docs/dashboard.html").write_text(dashboard_html)

# ==========================================
# 4. UPDATE HOMEPAGE (docs/index.html)
# ==========================================
homepage_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Algocare — Pass Your Nursing & Midwifery Exams</title>
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="assets/style.css">
<style>
.hero { text-align: center; padding: 80px 20px; max-width: 700px; margin: 0 auto; }
.hero h1 { font-size: 2.5rem; margin-bottom: 16px; line-height: 1.2; }
.hero p { font-size: 1.1rem; color: var(--ink-soft); margin-bottom: 32px; }
.hero-btns { display: flex; gap: 12px; justify-content: center; }
.hero-btns a { padding: 14px 28px; border-radius: 8px; font-weight: 700; text-decoration: none; font-size: 1rem; }
.btn-primary { background: var(--scrub); color: #fff; }
.btn-primary:hover { opacity: 0.9; }
.btn-secondary { background: var(--card); color: var(--ink); border: 1px solid var(--grey-line); }
.btn-secondary:hover { background: var(--paper); }
.features { display: grid; grid-template-columns: 1fr; gap: 24px; max-width: 900px; margin: 0 auto 80px; padding: 0 20px; }
@media (min-width: 600px) { .features { grid-template-columns: 1fr 1fr 1fr; } }
.feature-card { background: var(--card); padding: 24px; border-radius: 12px; border: 1px solid var(--grey-line); }
.feature-card h3 { color: var(--scrub); margin-bottom: 8px; }
.feature-card p { color: var(--ink-soft); font-size: 0.9rem; margin: 0; }
</style>
</head>
<body>
<div class="topbar">
  <div class="brand"><span class="pulse-dot"></span>Algocare</div>
  <div id="authSlot"></div>
</div>

<div class="hero">
  <h1>Pass your Nursing & Midwifery exams with confidence.</h1>
  <p>Curated study articles, practice tests, and real-feel CBT exams. Built for Nigerian students.</p>
  <div class="hero-btns">
    <a href="signup.html" class="btn-primary">Get Started Free</a>
    <a href="login.html" class="btn-secondary">Log In</a>
  </div>
</div>

<div class="features">
  <div class="feature-card">
    <h3>📚 Study Articles</h3>
    <p>2,000+ topics covering the full Nursing and Midwifery curriculum.</p>
  </div>
  <div class="feature-card">
    <h3>🎯 Practice Mode</h3>
    <p>Choose specific courses and test yourself with instant explanations.</p>
  </div>
  <div class="feature-card">
    <h3>⏱️ Real-Feel Exams</h3>
    <p>Simulate the actual CBT exam with 250 mixed questions and strict timing.</p>
  </div>
</div>

<script src="assets/auth.js"></script>
</body>
</html>"""
Path("docs/index.html").write_text(homepage_html)

# ==========================================
# 5. PATCH BUILD_PAGES.PY (Add authSlot to Topbar)
# ==========================================
bp = Path("build_pages.py")
src = bp.read_text()

# Add auth.js and authSlot to PAGE_HEAD
if "authSlot" not in src:
    # Add auth.js to head
    src = src.replace(
        '<script src="{rel}assets/analytics.js"></script>',
        '<script src="{rel}assets/analytics.js"></script>\n<script src="{root_rel}assets/auth.js"></script>'
    )
    # Add authSlot to topbar
    src = src.replace(
        '<a href="{root_rel}index.html" style="font-size: 0.85rem; color: var(--ink-soft);">All programs</a>',
        '<a href="{root_rel}index.html" style="font-size: 0.85rem; color: var(--ink-soft); margin-right: 16px;">All programs</a>\n    <span id="authSlot"></span>'
    )
    bp.write_text(src)
    print("✅ Patched build_pages.py with authSlot and auth.js")

print("🎉 Phase 4 Complete. Auth, Dashboard, and Homepage generated.")
