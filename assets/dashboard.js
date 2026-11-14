document.addEventListener("DOMContentLoaded", () => {
  const session = getSession();
  if (!session) { window.location.href = "/login.html"; return; }

  const user = session.user;
  const name = user.user_metadata?.name || user.email.split('@')[0];
  const greetingEl = document.getElementById("greeting");
  if (greetingEl) greetingEl.textContent = `Welcome, ${name}`;

  const tabs = document.querySelectorAll(".prog-tab");
  const linkArticles = document.getElementById("link-articles");
  const linkPractice = document.getElementById("link-practice");
  const linkRealfeel = document.getElementById("link-realfeel");
  const linkLeaderboard = document.getElementById("link-leaderboard");

  function updateLinks(prog) {
    linkArticles.href = `/${prog}/index.html`;
    linkPractice.href = `/${prog}/cbt/practice-setup.html`;
    linkRealfeel.href = `/${prog}/cbt/exam-setup.html`;
    linkLeaderboard.href = `/leaderboard.html?prog=${prog}`;

    tabs.forEach(t => t.classList.toggle("active", t.dataset.prog === prog));
    localStorage.setItem("algocare_dashboard_prog", prog);
  }

  tabs.forEach(tab => tab.addEventListener("click", () => updateLinks(tab.dataset.prog)));
  updateLinks(localStorage.getItem("algocare_dashboard_prog") || "nursing");
});
