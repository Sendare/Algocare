const API_URL = "https://algocare-api.abdul01abdul03.workers.dev";

window.closeWelcomeModal = function() {
  document.getElementById("welcomeModal").style.display = "none";
  localStorage.setItem("algocare_welcomed", "true");
};

document.addEventListener("DOMContentLoaded", async () => {
  const session = getSession();
  if (!session) { window.location.href = "/login"; return; }

  const user = session.user;
  
  // 1. Fetch FRESH user data from Supabase to bypass any local cache issues
  let displayName = "Student";
  try {
    const res = await fetch(`${SUPABASE_URL}/auth/v1/user`, {
      headers: { "apikey": SUPABASE_ANON_KEY, "Authorization": `Bearer ${session.access_token}` }
    });
    const freshUser = await res.json();
    const meta = freshUser.user_metadata || {};
    
    // Fallback logic: Username -> First Name -> Email
    if (meta.username && meta.username.trim() !== "") {
      displayName = meta.username;
    } else if (meta.name && meta.name.trim() !== "") {
      displayName = meta.name.split(' ')[0];
    } else {
      displayName = freshUser.email.split('@')[0];
    }
    
    // Keep localstorage in sync silently
    session.user.user_metadata = meta;
    localStorage.setItem("algocare_session", JSON.stringify(session));
    
  } catch (err) {
    console.error("Could not fetch fresh user data:", err);
    displayName = user.user_metadata?.username || user.email.split('@')[0];
  }

  document.getElementById("greeting").textContent = displayName;

  // 2. Inject Admin Button
  if (user.email && user.email.toLowerCase() === "abdul01abdul03@gmail.com") {
    const container = document.getElementById("adminBtnContainer");
    if (container) {
      container.innerHTML = `
        <a href="/admin.html" style="display:inline-block; background:var(--ink); color:#fff; padding:10px 16px; border-radius:6px; font-weight:700; text-decoration:none; font-size:0.9rem;">
          🛡️ Admin Panel
        </a>`;
    }
  }

  // 3. Setup UI Links and Tabs
  const tabs = document.querySelectorAll(".prog-tab");
  const linkArticles = document.getElementById("link-articles");
  const linkPractice = document.getElementById("link-practice");
  const linkRealfeel = document.getElementById("link-realfeel");
  const linkLeaderboard = document.getElementById("link-leaderboard");

  async function updateStats(prog) {
    const statQs = document.getElementById("stat-qs");
    const statScore = document.getElementById("stat-score");
    const statStreak = document.getElementById("stat-streak");
    const recentList = document.getElementById("recentScoresList");
    
    if (!statQs) return; 
    
    try {
      const res = await fetchWithAuth(`${API_URL}/get-stats?program=${prog}`);
      
      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Worker Error ${res.status}: ${errorText}`);
      }
      
      const data = await res.json();
      if (data.length === 0) {
        statQs.textContent = "0"; statScore.textContent = "0%"; statStreak.textContent = "🔥 0";
        recentList.innerHTML = `<li style="padding: 8px 0; color: var(--ink-soft);">No tests taken yet.</li>`;
        return;
      }

      // Local Date (YYYY-MM-DD)
      const today = new Date().toLocaleDateString('en-CA'); 
      statQs.textContent = data.filter(d => new Date(d.created_at).toLocaleDateString('en-CA') === today).reduce((sum, d) => sum + (d.attempted || d.question_count || 0), 0);
      
      const totalCorrect = data.reduce((sum, d) => sum + d.correct, 0);
      const totalQuestions = data.reduce((sum, d) => sum + d.question_count, 0);
      statScore.textContent = totalQuestions > 0 ? `${Math.round((totalCorrect / totalQuestions) * 100)}%` : "0%";
      
      // Calculate Consecutive Streak
      const dates = [...new Set(data.map(d => new Date(d.created_at).toLocaleDateString('en-CA')))].sort().reverse();
      let streak = 0;
      const yesterday = new Date(Date.now() - 86400000).toLocaleDateString('en-CA');
      
      if (dates.length > 0 && (dates[0] === today || dates[0] === yesterday)) {
        let expectedDate = new Date(dates[0]);
        for (let dateStr of dates) {
          if (dateStr === expectedDate.toLocaleDateString('en-CA')) {
            streak++;
            expectedDate.setDate(expectedDate.getDate() - 1);
          } else { break; }
        }
      }
      statStreak.textContent = `🔥 ${streak}`;

      recentList.innerHTML = data.slice(0, 3).map(r => {
        const pct = Math.round((r.correct / r.question_count) * 100);
        const color = pct >= 50 ? 'var(--scrub)' : 'var(--brick)';
        const title = r.test_type === 'real_feel' ? 'Real-Feel Exam' : 'Practice: ' + (r.test_identifier || '').replace(/-/g, ' ').substring(0, 15);
        return `<li style="display:flex; justify-content:space-between; padding: 12px 0; border-bottom: 1px solid var(--grey-line);">
          <span style="font-weight:600; color:var(--ink);">${esc(title)}...</span>
          <span style="color: ${color}; font-weight: 700;">${r.correct}/${r.question_count} (${pct}%)</span>
        </li>`;
      }).join("");
    } catch (err) {
      recentList.innerHTML = `<li style="padding: 8px 0; color: var(--brick); font-size:0.8rem;">ERROR: ${err.message}</li>`;
    }
  }

  function updateLinks(prog) {
    if (prog === "public-health") {
      alert("Public Health is coming soon! Stay tuned.");
      const savedProg = localStorage.getItem("algocare_dashboard_prog") || "nursing";
      tabs.forEach(t => t.classList.toggle("active", t.dataset.prog === savedProg));
      return;
    }

    tabs.forEach(t => t.classList.toggle("active", t.dataset.prog === prog));
    linkArticles.href = `/${prog}/index.html`;
    linkPractice.href = `/${prog}/cbt/practice-setup.html`;
    linkRealfeel.href = `/${prog}/cbt/exam-setup.html`;
    linkLeaderboard.href = `/leaderboard.html?prog=${prog}`;
    
    localStorage.setItem("algocare_dashboard_prog", prog);
    updateStats(prog);
  }

  tabs.forEach(tab => tab.addEventListener("click", () => updateLinks(tab.dataset.prog)));
  updateLinks(localStorage.getItem("algocare_dashboard_prog") || "nursing");
});
