document.addEventListener("DOMContentLoaded", () => {
  const session = getSession();
  if (!session) { window.location.href = "/login.html"; return; }

  const urlParams = new URLSearchParams(window.location.search);
  const program = urlParams.get("prog") || "nursing";
  
  let currentMode = "real_feel";
  const container = document.getElementById("leaderboardContainer");
  const toggleBtns = document.querySelectorAll(".toggle-btn");

  // Supabase RPC call
  async function fetchLeaderboard(mode) {
    container.innerHTML = '<div class="loading">Loading scores...</div>';
    
    try {
      const res = await fetch(`${SUPABASE_URL}/rest/v1/rpc/get_leaderboard`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "apikey": SUPABASE_ANON_KEY,
          "Authorization": `Bearer ${SUPABASE_ANON_KEY}`
        },
        body: JSON.stringify({
          prog: program,
          test_mode: mode,
          limit_count: 20
        })
      });

      if (!res.ok) throw new Error("Failed to load leaderboard");
      const data = await res.json();
      
      if (data.length === 0) {
        container.innerHTML = '<div class="loading">No scores yet. Be the first to take a test!</div>';
        return;
      }

      // Build Table HTML
      let html = `
        <table class="lb-table">
          <thead>
            <tr>
              <th>Rank</th>
              <th>Student</th>
              <th style="text-align:right;">Score</th>
            </tr>
          </thead>
          <tbody>
      `;
      
      data.forEach((row, index) => {
        // Highlight the current logged-in user
        const isMe = row.user_id === session.user.id;
        const rowStyle = isMe ? 'background: var(--scrub-soft);' : '';
        const rankDisplay = index === 0 ? '🥇 1' : index === 1 ? '🥈 2' : index === 2 ? '🥉 3' : index + 1;

        html += `
          <tr style="${rowStyle}">
            <td class="lb-rank">${rankDisplay}</td>
            <td class="lb-name">${row.user_name} ${isMe ? '(You)' : ''}</td>
            <td class="lb-score">${row.correct} / ${row.total}</td>
          </tr>
        `;
      });

      html += `</tbody></table>`;
      container.innerHTML = html;

    } catch (err) {
      console.error(err);
      container.innerHTML = '<div class="loading" style="color: var(--brick);">Error loading leaderboard.</div>';
    }
  }

  // Handle Mode Toggles (Practice vs Real-Feel)
  toggleBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      toggleBtns.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      currentMode = btn.dataset.mode;
      fetchLeaderboard(currentMode);
    });
  });

  // Initial fetch
  fetchLeaderboard(currentMode);
});
