const params = new URLSearchParams(window.location.search);
const topicId = params.get("topic");

async function init() {
  if (!topicId) {
    document.getElementById("articleRoot").innerHTML =
      `<div class="empty-state">No article specified. <a href="index.html">Go back to topics</a>.</div>`;
    return;
  }

  let article;
  try {
    const res = await fetch(`../data/articles/${topicId}.json`);
    article = await res.json();
  } catch (err) {
    document.getElementById("articleRoot").innerHTML =
      `<div class="empty-state">Couldn't load this article — it may not be generated yet. <a href="index.html">Go back</a>.</div>`;
    console.error(err);
    return;
  }

  render(article);

  // If a specific heading was linked to (article.html?topic=X#heading_id),
  // scroll to it once content is in the DOM.
  if (window.location.hash) {
    const target = document.querySelector(window.location.hash);
    if (target) target.scrollIntoView({ behavior: "smooth" });
  }
}

function render(article) {
  const breadcrumb = (article.path || []).join(" > ");

  const headingsHtml = article.headings.map(h => `
    <div class="article-heading" id="${h.heading_id}">
      <h2>${h.title}</h2>
      <p>${h.content}</p>
    </div>
  `).join("");

  document.getElementById("articleRoot").innerHTML = `
    <div class="breadcrumb">${breadcrumb}</div>
    <h1>${article.title}</h1>
    ${headingsHtml}
    <a class="test-yourself-link" href="test.html?topic=${topicId}">Test yourself on this topic →</a>
  `;
}

init();
