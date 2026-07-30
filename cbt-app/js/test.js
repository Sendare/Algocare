const params = new URLSearchParams(window.location.search);
const topicId = params.get("topic");

const TEST_DURATION_SECONDS = 15 * 60; // 15 min default test length
let timeRemaining = TEST_DURATION_SECONDS;
let timerInterval = null;

let questions = [];
let articleTitle = "";
let current = 0;
// answers[i] = { selected: "A", isCorrect: true/false } once answered
let answers = [];

async function init() {
  if (!topicId) {
    document.getElementById("testRoot").innerHTML =
      `<div class="empty-state">No topic specified. <a href="index.html">Go back to topics</a>.</div>`;
    return;
  }

  try {
    const [qRes, aRes] = await Promise.all([
      fetch(`../data/questions/${topicId}.json`),
      fetch(`../data/articles/${topicId}.json`),
    ]);
    questions = await qRes.json();
    const article = await aRes.json();
    articleTitle = article.title;
  } catch (err) {
    document.getElementById("testRoot").innerHTML =
      `<div class="empty-state">Couldn't load this test — it may not be generated yet. <a href="index.html">Go back</a>.</div>`;
    console.error(err);
    return;
  }

  if (!questions.length) {
    document.getElementById("testRoot").innerHTML =
      `<div class="empty-state">No questions available for this topic yet.</div>`;
    return;
  }

  answers = new Array(questions.length).fill(null);
  startTimer();
  render();
}

function startTimer() {
  updateTimerDisplay();
  timerInterval = setInterval(() => {
    timeRemaining--;
    updateTimerDisplay();
    if (timeRemaining <= 0) {
      clearInterval(timerInterval);
      finishTest(true);
    }
  }, 1000);
}

function updateTimerDisplay() {
  const m = Math.floor(timeRemaining / 60).toString().padStart(2, "0");
  const s = (timeRemaining % 60).toString().padStart(2, "0");
  document.getElementById("timerReadout").textContent = `${m}:${s}`;

  const strip = document.getElementById("pulseStrip");
  strip.classList.remove("warning", "danger");
  if (timeRemaining <= 60) strip.classList.add("danger");
  else if (timeRemaining <= 180) strip.classList.add("warning");
}

function render() {
  const q = questions[current];
  const answer = answers[current];

  const optionKeys = Object.keys(q.options);

  const optionsHtml = optionKeys.map(key => {
    let cls = "option";
    if (answer) {
      if (key === answer.selected) cls += " selected";
      if (key === q.answer) cls += " correct";
      if (key === answer.selected && key !== q.answer) cls += " incorrect";
    }
    return `<button class="${cls}" data-key="${key}" ${answer ? "disabled" : ""}>
      <strong>${key}.</strong> ${q.options[key]}
    </button>`;
  }).join("");

  const explanationHtml = answer ? `
    <div class="explanation-box" id="explanationBox">
      ${answer.showExplanation ? parseExplanation(q.explanation) : ""}
    </div>
    <div class="action-row">
      ${!answer.showExplanation ? `<button class="btn secondary" id="showExplanationBtn">Show explanation</button>` : ""}
      <button class="btn" id="nextBtn">${current < questions.length - 1 ? "Next question" : "Finish test"}</button>
    </div>
  ` : "";

  document.getElementById("testRoot").innerHTML = `
    <div class="test-layout">
      <div class="question-nav">${renderNavTabs()}</div>
      <div class="test-card">
        <div class="folder-tab">${articleTitle}</div>
        <div class="question-number">Question ${current + 1} of ${questions.length}</div>
        <div class="question-text">${q.question}</div>
        <div class="options-list">${optionsHtml}</div>
        ${explanationHtml}
      </div>
    </div>
  `;

  attachHandlers();
}

function renderNavTabs() {
  return questions.map((_, i) => {
    let cls = "nav-tab";
    if (i === current) cls += " current";
    else if (answers[i]) cls += answers[i].isCorrect ? " answered-correct" : " answered-incorrect";
    return `<div class="${cls}" data-index="${i}">${i + 1}</div>`;
  }).join("");
}

function parseExplanation(text) {
  // Convert [learn more](article_id#heading_id) into a real link to article.html
  return text.replace(/\[([^\]]+)\]\(([^)#]+)#([^)]+)\)/g,
    (match, label, articleId, headingId) =>
      `<a href="article.html?topic=${articleId}#${headingId}">${label}</a>`
  );
}

function attachHandlers() {
  document.querySelectorAll(".option").forEach(btn => {
    btn.addEventListener("click", () => selectAnswer(btn.dataset.key));
  });

  document.querySelectorAll(".nav-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      current = parseInt(tab.dataset.index, 10);
      render();
    });
  });

  const showExplanationBtn = document.getElementById("showExplanationBtn");
  if (showExplanationBtn) {
    showExplanationBtn.addEventListener("click", () => {
      answers[current].showExplanation = true;
      render();
    });
  }

  const nextBtn = document.getElementById("nextBtn");
  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      if (current < questions.length - 1) {
        current++;
        render();
      } else {
        finishTest(false);
      }
    });
  }
}

function selectAnswer(key) {
  if (answers[current]) return; // already answered, locked
  const q = questions[current];
  answers[current] = {
    selected: key,
    isCorrect: key === q.answer,
    showExplanation: false,
  };
  render();
}

function finishTest(timedOut) {
  clearInterval(timerInterval);
  const correctCount = answers.filter(a => a && a.isCorrect).length;
  const answeredCount = answers.filter(a => a).length;

  document.getElementById("testRoot").innerHTML = `
    <div class="test-card">
      <h2>${timedOut ? "Time's up" : "Test complete"}</h2>
      <p>You answered ${answeredCount} of ${questions.length} questions.</p>
      <p><strong>${correctCount} correct</strong> out of ${answeredCount} answered.</p>
      <div class="action-row">
        <a class="btn" href="index.html" style="text-decoration:none; display:inline-block;">Back to topics</a>
      </div>
    </div>
  `;
}

init();
