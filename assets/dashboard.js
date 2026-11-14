// ===== Dashboard Logic =====
document.addEventListener("DOMContentLoaded", () => {
  // 1. Check if user is logged in
  const session = getSession();
  if (!session) {
    window.location.href = "/login.html";
    return;
  }

  // 2. Set Greeting Name
  const user = session.user;
  const name = user.user_metadata?.name || user.email.split('@')[0];
  const greetingEl = document.getElementById("greeting");
  if (greetingEl) greetingEl.textContent = `Welcome, ${name}`;

  // 3. Program Switcher Logic
  const tabs = document.querySelectorAll(".prog-tab");
  const linkArticles = document.getElementById("link-articles");
  const linkPractice = document.getElementById("link-practice");
  const linkRealfeel = document.getElementById("link-realfeel");

  function updateLinks(prog) {
    // Update the href of the cards based on the selected program
    linkArticles.href = `/${prog}/index.html`;
    linkPractice.href = `/${prog}/cbt/practice-setup.html`;
    linkRealfeel.href = `/${prog}/cbt/exam-setup.html`;

    // Update active tab styling
    tabs.forEach(t => {
      t.classList.toggle("active", t.dataset.prog === prog);
    });
  }

  // Add click listeners to the tabs
  tabs.forEach(tab => {
    tab.addEventListener("click", () => updateLinks(tab.dataset.prog));
  });

  // Initialize with Nursing by default
  updateLinks("nursing");
});
