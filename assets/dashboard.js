
document.addEventListener("DOMContentLoaded", async () => {
  const session = getSession();
  if (!session) { window.location.href = "./login.html"; return; }

  const user = session.user;
  const name = user.user_metadata?.name || user.email.split('@')[0];
  const greetingEl = document.getElementById("greeting");
  if (greetingEl) greetingEl.textContent = `Welcome, ${name}`;

  // Program Switcher
  const tabs = document.querySelectorAll(".prog-tab");
  const linkArticles = document.getElementById("link-articles");
  const linkPractice = document.getElementById("link-practice");
  const linkRealfeel = document.getElementById("link-realfeel");
  const linkLeaderboard = document.getElementById("link-leaderboard");
  const statQs = document.getElementById("stat-qs");
  const statScore = document.getElementById("stat-score");
  const statStreak = document.getElementById("stat-streak");

  async function updateStats(prog) {
    if (!statQs) return; // Not on the dashboard page
    
    try {
      // Fetch all finished tests for this user and program
      const res = await fetch(`${SUPABASE_URL}/rest/v1/test_events?user_id=eq.${user.id}&program=eq.${prog}&event_type=eq.finished&select=*`, {
        headers: { "apikey": SUPABASE_ANON_KEY, "Authorization": `Bearer ${SUPABASE_ANON_KEY}` }
      });
      const data = await res.json();
      
      if (data.length === 0) {
        statQs.textContent = "0";
        statScore.textContent = "0%";
        statStreak.textContent = "🔥 0";
        return;
      }

      // Calculate Questions Today
      const today = new Date().toISOString().split('T')[0];
      const todayQs = data.filter(d => d.created_at.startsWith(today)).reduce((sum, d) => sum + d.correct, 0);
      statQs.textContent = todayQs;

      // Calculate Average Score
      const totalCorrect = data.reduce((sum, d) => sum + d.correct, 0);
      const totalQuestions = data.reduce((sum, d) => sum + d.question_count, 0);
      const avg = totalQuestions > 0 ? Math.round((totalCorrect / totalQuestions) * 100) : 0;
      statScore.textContent = `${avg}%`;

      // Calculate Streak (simplified: just count unique days in the last 7 days)
      const uniqueDays = new Set(data.map(d => d.created_at.split('T')[0]));
      statStreak.textContent = `🔥 ${uniqueDays.size}`;

    } catch (err) {
      console.error("Stats error", err);
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
