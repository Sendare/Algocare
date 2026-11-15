let siteIndex = [];

async function loadIndex() {
  try {
    const res = await fetch("site_index.json");
    siteIndex = await res.json();
  } catch (err) {
    console.error("Could not load search index", err);
  }
}

function renderSearchResults(query) {
  const listEl = document.getElementById("courseList");
  if (!query) {
    listEl.style.display = "";
    const oldResults = document.getElementById("searchResults");
    if (oldResults) oldResults.remove();
    return;
  }
  
  listEl.style.display = "none";

  let resultsEl = document.getElementById("searchResults");
  if (!resultsEl) {
    resultsEl = document.createElement("div");
    resultsEl.id = "searchResults";
    resultsEl.className = "branch-group";
    listEl.after(resultsEl);
  }

  const q = query.toLowerCase();
  const matches = siteIndex.filter(item =>
    item.title.toLowerCase().includes(q) ||
    item.course.toLowerCase().includes(q) ||
    item.unit.toLowerCase().includes(q)
  );

  if (matches.length === 0) {
    resultsEl.innerHTML = `<div class="empty-state">No topics match "${query}".</div>`;
    return;
  }

  resultsEl.innerHTML = matches.map(item => `
    <div class="topic-card">
      <div>
        <div class="topic-title">${item.title}</div>
        <div class="topic-meta">${item.course} · ${item.unit}</div>
      </div>
      <div class="topic-actions"><a href="${item.url}">Read →</a></div>
    </div>
  `).join("");
}

document.addEventListener("DOMContentLoaded", () => {
  loadIndex();
  const input = document.getElementById("searchInput");
  if (input) {
    input.addEventListener("input", (e) => renderSearchResults(e.target.value.trim()));
  }
});
