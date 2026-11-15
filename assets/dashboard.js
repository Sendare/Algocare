document.addEventListener("DOMContentLoaded", async () => {
  const session = getSession();
  if (!session) { window.location.href = "./login.html"; return; }

  const user = session.user;
  const name = user.user_metadata?.name || user.email.split('@')[0];
  const greetingEl = document.getElementById("greeting");
  if (greetingEl) greetingEl.textContent = `Welcome, ${name}`;

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
      // Fetch using the user's actual session token, not the anon key
      const res = await fetch(`${SUPABASE_URL}/rest/v1/test_events?user_id=eq.${user.id}&program=eq.${prog}&event_type=eq.finished&order=created_at.desc&select=*`, {
        headers: { 
          "apikey": SUPABASE_ANON_KEY, 
          "Authorization": `Bearer ${session.access_token}` 
        }
      });
      
      if (!res.ok) throw new Error("Failed to fetch stats");
      const data = await res.json();
      
      if (data.length === 0) {
        statQs.textContent = "0";
        statScore.textContent = "0%";
        statStreak.textContent = "🔥 0";
        if (recentList) recentList.innerHTML = `<li style="padding: 8px 0; color: var(--ink-soft);">No tests taken yet.</li>`;
        return;
      }

      // 1. Calculate Qs Today
      const today = new Date().toISOString().split('T')[0];
      const todayQs = data.filter(d => d.created_at.startsWith(today)).reduce((sum, d) => sum + d.correct, 0);
      statQs.textContent = todayQs;

      // 2. Calculate Average Score
      const totalCorrect = data.reduce((sum, d) => sum + d.correct, 0);
      const totalQuestions = data.reduce((sum, d) => sum + d.question_count, 0);
      const avg = totalQuestions > 0 ? Math.round((totalCorrect / totalQuestions) * 100) : 0;
      statScore.textContent = `${avg}%`;

      // 3. Calculate Streak
      const uniqueDays = new Set(data.map(d => d.created_at.split('T')[0]));
      statStreak.textContent = `🔥 ${uniqueDays.size}`;

      // 4. Build Recent Scores List (Top 3)
      if (recentList) {
        recentList.innerHTML = data.slice(0, 3).map(r => {
          const pct = Math.round((r.correct / r.question_count) * 100);
          const color = pct >= 50 ? 'var(--scrub)' : 'var(--brick)';
          const title = r.test_type === 'real_feel' ? 'Real-Feel Exam' : 'Practice: ' + (r.test_identifier || '').replace(/-/g, ' ').substring(0, 15);
          return `<li style="display:flex; justify-content:space-between; padding: 12px 0; border-bottom: 1px solid var(--grey-line);">
            <span style="font-weight:600; color:var(--ink);">${title}...</span> 
            <span style="color: ${color}; font-weight: 700;">${r.correct}/${r.question_count} (${pct}%)</span>
          </li>`;
        }).join("");
      }

    } catch (err) {
      console.error("Stats error", err);
      if (recentList) recentList.innerHTML = `<li style="padding: 8px 0; color: var(--brick);">Error loading scores.</li>`;
    }
  }

  function updateLinks(prog) {
    linkArticles.href = `./${prog}/index.html`;
    linkPractice.href = `./${prog}/cbt/practice-setup.html`;
    linkRealfeel.href = `./${prog}/cbt/exam-setup.html`;
    linkLeaderboard.href = `./leaderboard.html?prog=${prog}`;

    tabs.forEach(t => t.classList.toggle("active", t.dataset.prog === prog));
    localStorage.setItem("algocare_dashboard_prog", prog);
    updateStats(prog);
  }

  tabs.forEach(tab => tab.addEventListener("click", () => updateLinks(tab.dataset.prog)));
  updateLinks(localStorage.getItem("algocare_dashboard_prog") || "nursing");
});
