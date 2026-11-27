const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));

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
  // NO CAPTCHA LOGIC HERE ANYMORE
  const res = await fetch(`${SUPABASE_URL}/auth/v1/signup`, {
    method: "POST",
    headers: { "Content-Type": "application/json", "apikey": SUPABASE_ANON_KEY },
    body: JSON.stringify({ email, password, data: { name } })
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
  // NO CAPTCHA LOGIC HERE ANYMORE
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

async function refreshSession() {
  const session = getSession();
  if (!session || !session.refresh_token) { logOut(); return null; }

  try {
    const res = await fetch(`${SUPABASE_URL}/auth/v1/token?grant_type=refresh_token`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "apikey": SUPABASE_ANON_KEY },
      body: JSON.stringify({ refresh_token: session.refresh_token })
    });
    
    // Only log out if the token is actually dead (400/401)
    if (res.status === 400 || res.status === 401) {
      console.warn("Refresh token rejected by Supabase. Logging out.");
      logOut();
      return null;
    }
    
    if (!res.ok) throw new Error("Server error");
    
    const data = await res.json();
    saveSession(data);
    return data;
  } catch (err) {
    console.warn("Refresh failed due to network. Keeping session alive.", err);
    return null; // Don't log out on network drop
  }
}

async function logOut() {
  const session = getSession();
  if (session && session.access_token) {
    // Fire and forget server-side revocation
    fetch(`${SUPABASE_URL}/auth/v1/logout`, {
      method: "POST",
      headers: { "apikey": SUPABASE_ANON_KEY, "Authorization": `Bearer ${session.access_token}` }
    }).catch(() => {});
  }
  
  localStorage.removeItem("algocare_session");
  localStorage.removeItem("algocare_uid");
  sessionStorage.removeItem("algocare_exam_state");
  sessionStorage.removeItem("algocare_results_state");
  window.location.href = "/login";
}

let refreshPromise = null;

async function fetchWithAuth(url, options = {}) {
  let session = getSession();
  if (!session || !session.access_token) { logOut(); throw new Error("No valid session"); }

  if (!options.headers) options.headers = {};
  options.headers["Authorization"] = `Bearer ${session.access_token}`;

  let res = await fetch(url, options);

  if (res.status === 401) {
    // In-flight lock: if a refresh is already happening, wait for it
    if (!refreshPromise) {
      refreshPromise = refreshSession().finally(() => { refreshPromise = null; });
    }
    
    const newSession = await refreshPromise;
    
    if (newSession && newSession.access_token) {
      options.headers["Authorization"] = `Bearer ${newSession.access_token}`;
      res = await fetch(url, options);
    } else {
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
  const publicPages = ['index', 'login', 'signup', 'privacy', 'terms', 'privacy.html', 'terms.html', ''];
  const currentPath = window.location.pathname.split('/').pop().replace('.html', '') || 'index';
  
  if (!publicPages.includes(currentPath) && !getSession()) {
    // Redirect to login (not signup) to preserve the flow
    const nextUrl = encodeURIComponent(window.location.pathname + window.location.search);
    window.location.replace(`/login?next=${nextUrl}`);
    return;
  }

  const authSlot = document.getElementById("authSlot");
  if (!authSlot) return;

  const user = getUser();
  if (user) {
    const name = user.user_metadata?.username || user.user_metadata?.name || user.email.split('@')[0];
    const avatarUrl = user.user_metadata?.avatar_url;
    const avatarContent = avatarUrl 
      ? `<img src="${avatarUrl}" style="width:100%; height:100%; object-fit:cover;">` 
      : `<span>${esc((user.user_metadata?.name || name).charAt(0).toUpperCase())}</span>`;

    authSlot.innerHTML = `
      <div style="position: relative; display: inline-block;">
        <button id="avatarBtn" style="width: 40px; height: 40px; border-radius: 50%; background: var(--scrub-soft); color: var(--scrub); border: 1px solid var(--scrub); font-weight: bold; cursor: pointer; display: flex; align-items: center; justify-content: center; overflow: hidden; padding: 0;">
          ${avatarContent}
        </button>
        
        <div id="avatarDropdown" style="display: none; position: absolute; right: 0; top: 50px; background: var(--card); border: 1px solid var(--grey-line); border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); min-width: 180px; z-index: 100; overflow: hidden;">
          <div style="padding: 12px 16px; border-bottom: 1px solid var(--grey-line); background: var(--paper);">
            <div style="font-weight: bold; color: var(--ink); font-size: 0.9rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${esc(name)}</div>
            <div style="font-size: 0.75rem; color: var(--ink-soft); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${esc(user.email)}</div>
          </div>
          <a href="/dashboard" style="display: block; padding: 10px 16px; color: var(--ink); text-decoration: none; font-size: 0.9rem; border-bottom: 1px solid var(--grey-line);">My Dashboard</a>
          <a href="/settings.html" style="display: block; padding: 10px 16px; color: var(--ink); text-decoration: none; font-size: 0.9rem; border-bottom: 1px solid var(--grey-line);">Profile Settings</a>
          <button onclick="logOut()" style="display: block; width: 100%; text-align: left; padding: 10px 16px; background: none; border: none; color: var(--brick); cursor: pointer; font-size: 0.9rem; font-weight: 600;">Log out</button>
        </div>
      </div>
    `;

    // Toggle dropdown
    document.getElementById("avatarBtn").addEventListener("click", (e) => {
      e.stopPropagation();
      const dropdown = document.getElementById("avatarDropdown");
      dropdown.style.display = dropdown.style.display === "none" ? "block" : "none";
    });

    // Close dropdown when clicking outside
    document.addEventListener("click", () => {
      const dropdown = document.getElementById("avatarDropdown");
      if (dropdown) dropdown.style.display = "none";
    });
  } else {
    authSlot.innerHTML = `<a href="/login" style="color:var(--scrub); font-weight:600;">Log In</a>`;
  }
});
