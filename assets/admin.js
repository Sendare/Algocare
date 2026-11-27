const API_URL = "https://algocare-api.abdul01abdul03.workers.dev";

function switchTab(tabName) {
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
  document.querySelector(`.tab-btn[onclick="switchTab('${tabName}')"]`).classList.add('active');
  document.getElementById(`tab-${tabName}`).classList.add('active');
}

document.addEventListener("DOMContentLoaded", async () => {
  const session = getSession();
  const user = session ? session.user : null;
  
  // Frontend security check
  if (!user || user.email !== "abdul01abdul03@gmail.com") {
    window.location.href = "/dashboard.html";
    return;
  }

  try {
    const res = await fetch(`${API_URL}/admin-data`, {
      headers: { "Authorization": `Bearer ${session.access_token}` }
    });
    
    if (!res.ok) throw new Error(await res.text());
    const data = await res.json();

    // Populate Stats
    document.getElementById("total-users").textContent = data.users.length;
    document.getElementById("total-feedback").textContent = data.totalFeedback;
    // Count only 'finished' tests for total tests
    document.getElementById("total-tests").textContent = data.totalLogs;

    // Populate Users Table
    const usersBody = document.getElementById("users-body");
    usersBody.innerHTML = data.users.map(u => `
      <tr>
        <td style="font-weight:600;">${esc(u.name)}</td>
        <td>${esc(u.email)}</td>
        <td>${esc(u.school || "N/A")}</td>
        <td>${new Date(u.joined).toLocaleDateString()}</td>
      </tr>
    `).join("");

    // Populate Feedback Table
    const fbBody = document.getElementById("feedback-body");
    fbBody.innerHTML = data.feedback.map(f => `
      <tr>
        <td>${esc(f.user_name || 'Anonymous')}</td>
        <td style="color:var(--amber); font-weight:bold;">${'★'.repeat(f.stars)}</td>
        <td><span class="badge ${f.test_type === 'Bug Report' ? 'badge-bad' : 'badge-good'}">${esc(f.test_type || 'General')}</span></td>
        <td style="max-width: 200px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">${esc(f.comment || '-')}</td>
      </tr>
    `).join("");

    // Populate Articles Table
    const artBody = document.getElementById("articles-body");
    artBody.innerHTML = data.articles.map(a => `
      <tr>
        <td>${esc(a.user_name || 'Anonymous')}</td>
        <td style="font-family:var(--mono); font-size:0.8rem;">${esc(a.topic_id)}</td>
        <td>${new Date(a.created_at).toLocaleDateString()}</td>
      </tr>
    `).join("");

    // Populate Logs Table
    const logsBody = document.getElementById("logs-body");
    logsBody.innerHTML = data.logs.map(l => `
      <tr>
        <td>${esc(l.user_name || 'Anonymous')}</td>
        <td style="text-transform:capitalize;">${esc(l.program)}</td>
        <td>${esc((l.test_type || '').replace('_', ' '))}</td>
        <td style="font-weight:bold; color:var(--scrub);">${l.correct}/${l.question_count}</td>
      </tr>
    `).join("");

    document.getElementById("loading").style.display = "none";
    switchTab('users'); // Open Users tab by default

  } catch (err) {
    document.getElementById("loading").textContent = "Error: " + err.message;
    document.getElementById("loading").style.color = "var(--brick)";
  }
});
