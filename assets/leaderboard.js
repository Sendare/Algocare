const API_URL = "https://algocare-api.abdul01abdul03.workers.dev";

document.addEventListener("DOMContentLoaded", () => {
  const session = getSession();
  if (!session) { window.location.href = "/login.html"; return; }

  const urlParams = new URLSearchParams(window.location.search);
  const program = urlParams.get("prog") || "nursing";
  
  let currentMode = "real_feel";
  const container = document.getElementById("leaderboardContainer");
  const toggleBtns = document.querySelectorAll(".toggle-btn");

  async function fetchLeaderboard(mode) {
    container.innerHTML = '<div class="loading">Loading scores...</div>';
    
    try {
      const res = await fetchWithAuth(`${API_URL}/leaderboard?program=${program}&mode=${mode}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}: ${await res.text()}`);
      
      const data = await res.json();
      
      if (data.length === 0) {
        container.innerHTML = '<div class="loading">No scores yet. Be the first to take a test!</div>';
        return;
      }

      let html = `<table class="lb-table"><thead><tr><th>Rank</th><th>Student</th><th style="text-align:right;">Score</th></tr></thead><tbody>`;
      
      data.forEach((row, index) => {
        const isMe = row.user_id === session.user.id;
        const rowStyle = isMe ? 'background: var(--scrub-soft);' : '';
        const rankDisplay = index === 0 ? '🥇 1' : index === 1 ? '🥈 2' : index === 2 ? '🥉 3' : index + 1;

        html += `<tr style="${rowStyle}">
            <td class="lb-rank">${rankDisplay}</td>
            <td class="lb-name">${row.user_name} ${isMe ? '(You)' : ''}</td>
            <td class="lb-score" style="font-size: 1.1rem;">${row.total_correct} 🏅</td>
          </tr>`;
      });
      html += `</tbody></table>`;
      container.innerHTML = html;
    } catch (err) {
      container.innerHTML = `<div class="loading" style="color: var(--brick);">Error: ${err.message}</div>`;
    }
  }

  toggleBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      toggleBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentMode = btn.dataset.mode;
      fetchLeaderboard(currentMode);
    });
  });

  fetchLeaderboard(currentMode);
});
