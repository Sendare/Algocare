let manifest = [];

async function loadManifest() {
  try {
    const res = await fetch("../data/manifest.json");
    const data = await res.json();
    manifest = data.topics || [];
    render(manifest);
  } catch (err) {
    document.getElementById("results").innerHTML =
      `<div class="empty-state">Couldn't load the topic list. It may not exist yet — check back once generation has produced some articles.</div>`;
    console.error(err);
  }
}

function groupByBranch(topics) {
  const groups = {};
  for (const t of topics) {
    const branch = (t.path && t.path[0]) || "Uncategorized";
    if (!groups[branch]) groups[branch] = [];
    groups[branch].push(t);
  }
  return groups;
}

function render(topics) {
  const container = document.getElementById("results");

  if (topics.length === 0) {
    container.innerHTML = `<div class="empty-state">No topics match that search.</div>`;
    return;
  }

  const groups = groupByBranch(topics);
  const branchNames = Object.keys(groups).sort();

  container.innerHTML = branchNames.map(branch => `
    <div class="branch-group">
      <div class="branch-label">${branch}</div>
      ${groups[branch].map(t => `
        <div class="topic-card">
          <div>
            <div class="topic-title">${t.title}</div>
            <div class="topic-meta">${t.question_count} questions · ${t.heading_count} sections</div>
          </div>
          <div class="topic-actions">
            <a href="article.html?topic=${t.topic_id}">Read</a>
            <a href="test.html?topic=${t.topic_id}">Test yourself →</a>
          </div>
        </div>
      `).join("")}
    </div>
  `).join("");
}

document.getElementById("searchInput").addEventListener("input", (e) => {
  const q = e.target.value.trim().toLowerCase();
  if (!q) {
    render(manifest);
    return;
  }
  const filtered = manifest.filter(t =>
    t.title.toLowerCase().includes(q) ||
    (t.path || []).some(p => p.toLowerCase().includes(q))
  );
  render(filtered);
});

loadManifest();
