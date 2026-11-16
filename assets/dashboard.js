const API_URL = "https://algocare-api.abdul01abdul03.workers.dev";

document.addEventListener("DOMContentLoaded", async () => {
  const session = getSession();
  if (!session) { window.location.href = "/login"; return; }

  const user = session.user || {};
  const name = user.user_metadata?.name || user.email?.split('@')[0] || "Student";
  
  document.getElementById("greeting").textContent = `Welcome, ${name}`;

  // --- DEBUG EMAIL ON SCREEN ---
  const debugDiv = document.createElement("div");
  debugDiv.style.cssText = "font-size:0.75rem; color:var(--brick); margin-top:4px; font-family:var(--mono);";
  debugDiv.textContent = `DEBUG: Logged in as ${user.email || "UNKNOWN EMAIL"}`;
  document.querySelector(".dashboard-header > div:first-child").appendChild(debugDiv);
  // -----------------------------

  // 1. Inject Admin Button
  const container = document.getElementById("adminBtnContainer");
  if (container) {
    if (user.email && user.email.toLowerCase() === "abdul01abdul03@gmail.com") {
      container.innerHTML = `
        <a href="/admin.html" style="display:inline-block; background:var(--ink); color:#fff; padding:10px 16px; border-radius:6px; font-weight:700; text-decoration:none; font-size:0.9rem;">
          🛡️ Admin Panel
        </a>`;
    }
  }

  // 2. Setup UI Links
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

      const today = new Date().toISOString().split('T')[0];
      statQs.textContent = data.filter(d => d.created_at.startsWith(today)).reduce((sum, d) => sum + d.correct, 0);
      
      const totalCorrect = data.reduce((sum, d) => sum + d.correct, 0);
      const totalQuestions = data.reduce((sum, d) => sum + d.question_count, 0);
      statScore.textContent = totalQuestions > 0 ? `${Math.round((totalCorrect / totalQuestions) * 100)}%` : "0%";
      
      const uniqueDays = new Set(data.map(d => d.created_at.split('T')[0]));
      statStreak.textContent = `🔥 ${uniqueDays.size}`;

      recentList.innerHTML = data.slice(0, 3).map(r => {
        const pct = Math.round((r.correct / r.question_count) * 100);
        const color = pct >= 50 ? 'var(--scrub)' : 'var(--brick)';
        const title = r.test_type === 'real_feel' ? 'Real-Feel Exam' : 'Practice: ' + (r.test_identifier || '').replace(/-/g, ' ').substring(0, 15);
        return `<li style="display:flex; justify-content:space-between; padding: 12px 0; border-bottom: 1px solid var(--grey-line);">
          <span style="font-weight:600; color:var(--ink);">${title}...</span>
          <span style="color: ${color}; font-weight: 700;">${r.correct}/${r.question_count} (${pct}%)</span>
        </li>`;
      }).join("");
    } catch (err) {
      recentList.innerHTML = `<li style="padding: 8px 0; color: var(--brick); font-size:0.8rem;">ERROR: ${err.message}</li>`;
    }
  }

  function updateLinks(prog) {
    linkArticles.href = `/${prog}/index.html`;
    linkPractice.href = `/${prog}/cbt/practice-setup.html`;
    linkRealfeel.href = `/${prog}/cbt/exam-setup.html`;
    linkLeaderboard.href = `/leaderboard.html?prog=${prog}`;
    tabs.forEach(t => t.classList.toggle("active", t.dataset.prog === prog));
    localStorage.setItem("algocare_dashboard_prog", prog);
    updateStats(prog);
  }

  tabs.forEach(tab => tab.addEventListener("click", () => updateLinks(tab.dataset.prog)));
  updateLinks(localStorage.getItem("algocare_dashboard_prog") || "nursing");
});
