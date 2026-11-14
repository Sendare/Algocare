// ===== Algocare Auth Logic =====
const SUPABASE_URL = "https://uhrjtcocwejddtzyjyhr.supabase.co";
const SUPABASE_ANON_KEY = "sb_publishable_C_i1zk4P2phfIALmI6C7Iw_pYSMTGfQ";

// 1. Core Session Helpers
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

// 2. Auth Actions
async function signUp(name, email, password) {
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
  window.location.href = "/"; 
}

// 3. Catch Email Confirmation Redirects
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
        window.location.href = "/dashboard.html";
      } catch (err) { 
        console.error("Auth Redirect Error:", err); 
      }
    }
  }
}
handleAuthHash();

// 4. Inject State into Topbar
window.addEventListener("DOMContentLoaded", () => {
  const authSlot = document.getElementById("authSlot");
  if (!authSlot) return; 
  
  const user = getUser();
  if (user) {
    const name = user.user_metadata?.name || user.email.split('@')[0];
    authSlot.innerHTML = `
      <a href="/dashboard.html" style="font-weight:600; color:var(--scrub); text-decoration:none; margin-right:16px;">My Dashboard</a>
      <button onclick="logOut()" style="background:none; border:none; color:var(--ink-soft); cursor:pointer; font-size:0.85rem;">Log out</button>
    `;
  } else {
    authSlot.innerHTML = `
      <a href="/login.html" style="font-weight:600; color:var(--scrub); text-decoration:none;">Log In</a>
    `;
  }
});
