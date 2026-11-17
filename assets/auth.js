const SUPABASE_URL = "https://uhrjtcocwejddtzyjyhr.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_C_i1zk4P2phfIALmI6C7Iw_pYSMTGfQ";

function saveSession(data) {
  if (data && data.access_token) {
    localStorage.setItem("algocare_session", JSON.stringify(data));
  }
}

function getSession() {
  try {
    const r = localStorage.getItem("algocare_session");
    return r ? JSON.parse(r) : null;
  } catch { return null; }
}

function getUser() {
  const s = getSession();
  return s ? (s.user || null) : null;
}

async function signUp(name, email, password) {
  const captchaToken = window.captchaToken;
  if (!captchaToken) throw new Error("Please complete the CAPTCHA verification.");
  
  const res = await fetch(`${SUPABASE_URL}/auth/v1/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "apikey": SUPABASE_ANON_KEY },
    body: JSON.stringify({ email, password, data: { name }, gotrue_meta_security: { captcha_token: captchaToken } })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.msg || data.error_description || "Signup failed");
  if (data.access_token) {
    saveSession(data);
    localStorage.setItem("algocare_uid", data.user.id);
  }
  return data;
}

async function logIn(email, password) {
  const captchaToken = window.captchaToken;
  if (!captchaToken) throw new Error("Please complete the CAPTCHA verification.");
  
  const res = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=password`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "apikey": SUPABASE_ANON_KEY },
    body: JSON.stringify({ email, password, gotrue_meta_security: { captcha_token: captchaToken } })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error_description || data.msg || "Login failed");
  saveSession(data);
  localStorage.setItem("algocare_uid", data.user.id);
  return data;
}

async function refreshSession() {
  const session = getSession();
  if (!session || !session.refresh_token) { logOut(); return null; }

  try {
    const res = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=refresh_token`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "apikey": SUPABASE_ANON_KEY },
      body: JSON.stringify({ refresh_token: session.refresh_token })
    });
    if (!res.ok) throw new Error("Refresh failed");
    const data = await res.json();
    saveSession(data);
    return data;
  } catch (err) {
    logOut();
    return null;
  }
}

function logOut() {
  localStorage.removeItem("algocare_session");
  window.location.href = "/login";
}

async function fetchWithAuth(url, options = {}) {
  let session = getSession();
  if (!session || !session.access_token) { logOut(); throw new Error("No valid session"); }

  if (!options.headers) options.headers = {};
  options.headers["Authorization"] = `Bearer ${session.access_token}`;

  let res = await fetch(url, options);

  if (res.status === 401) {
    const newSession = await refreshSession();
    if (newSession && newSession.access_token) {
      options.headers["Authorization"] = `Bearer ${newSession.access_token}`;
      res = await fetch(url, options);
    } else {
      logOut();
      throw new Error("Session expired");
    }
  }
  return res;
}

async function handleAuthHash() {
  if (window.location.hash && window.location.hash.includes("access_token=")) {
    const hashParams = new URLSearchParams(window.location.hash.substring(1));
    const accessToken = hashParams.get("access_token");
    const refreshToken = hashParams.get("refresh_token");
    if (accessToken) {
      try {
        const res = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
          headers: { "apikey": SUPABASE_ANON_KEY, "Authorization": `Bearer ${accessToken}` }
        });
        const user = await res.json();
        saveSession({ access_token: accessToken, refresh_token: refreshToken, user });
        localStorage.setItem("algocare_uid", user.id);
        window.history.replaceState(null, "", window.location.pathname);
        window.location.href = "/dashboard";
      } catch (err) { console.error(err); }
    }
  }
}
handleAuthHash();

window.addEventListener("DOMContentLoaded", () => {
  // Handle both /login and /login.html (Cloudflare strips .html)
  const publicPages = ['index', 'login', 'signup', 'privacy', 'terms', ''];
  const currentPath = window.location.pathname.split('/').pop().replace('.html', '') || 'index';
  
  if (!publicPages.includes(currentPath) && !getSession()) {
    window.location.replace("/signup");
    return;
  }

  const authSlot = document.getElementById("authSlot");
  if (!authSlot) return;

  const user = getUser();
  if (user) {
    authSlot.innerHTML = `
      <a href="/dashboard" style="color:var(--scrub); font-weight:600; margin-right:16px;">Dashboard</a>
      <button onclick="logOut()" style="background:none; border:none; color:var(--ink-soft); cursor:pointer; font-size:0.85rem; font-weight:600; padding:0;">Log out</button>
    `;
  } else {
    authSlot.innerHTML = `<a href="/login" style="color:var(--scrub); font-weight:600;">Log In</a>`;
  }
});
