const params = new URLSearchParams(window.location.search);
const courseSlug = params.get("course");
const topicId = params.get("topic");
const requestedCount = parseInt(params.get("count"), 10) || null;
const secondsPerQuestion = parseInt(params.get("spq"), 10) || 30;

let questions = [];
let siteIndex = [];
let current = 0;
let answers = []; // { selected, isCorrect, showExplanation }
let timeRemaining = 0;
let timerInterval = null;
let timerPaused = false;

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

async function init() {
  try {
    const siteRes = await fetch("../site_index.json");
    siteIndex = await siteRes.json();

    let pool = [];
    if (topicId) {
      const qRes = await fetch(`../data/questions/${topicId}.json`);
      pool = await qRes.json();
    } else if (courseSlug) {
      const qRes = await fetch(`../data/course_pools/${courseSlug}.json`);
      pool = await qRes.json();
    } else {
      document.getElementById("root").innerHTML =
        `<div class="empty-state">No course or topic specified. <a href="index.html">Go back</a>.</div>`;
      return;
    }

    const count = requestedCount ? Math.min(requestedCount, pool.length) : pool.length;
    questions = shuffle(pool).slice(0, count);
  } catch (err) {
    document.getElementById("root").innerHTML =
      `<div class="empty-state">Couldn't load this practice set. <a href="index.html">Go back</a>.</div>`;
    console.error(err);
    return;
  }

  if (!questions.length) {
    document.getElementById("root").innerHTML = `<div class="empty-state">No questions available.</div>`;
    return;
  }

  answers = new Array(questions.length).fill(null);
  timeRemaining = questions.length * secondsPerQuestion;
  startTimer();
  render();
}

function startTimer() {
  updateTimerDisplay();
  timerInterval = setInterval(() => {
    if (timerPaused) return;
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
  document.getElementById("timerReadout").textContent = timerPaused ? "PAUSED" : `${m}:${s}`;

  const strip = document.getElementById("pulseStrip");
  strip.classList.remove("warning", "danger");
  if (timeRemaining <= 60) strip.classList.add("danger");
  else if (timeRemaining <= 180) strip.classList.add("warning");
}

function render() {
  const q = questions[current];
  const answer = answers[current];
  const optionKeys = Object.keys(q.options);

  // Timer pauses exactly while an explanation is open - covers both reading
  // the explanation itself and following a learn-more link from inside it.
  timerPaused = !!(answer && answer.showExplanation);
  updateTimerDisplay();

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
    ${answer.showExplanation ? `<div class="explanation-box">${parseExplanation(q.explanation, q.topic_id)}</div>` : ""}
    <div class="action-row">
      ${!answer.showExplanation ? `<button class="btn secondary" id="showExplanationBtn">Show explanation</button>` : ""}
      <button class="btn" id="nextBtn">${current < questions.length - 1 ? "Next question" : "Finish"}</button>
    </div>
  ` : "";

  document.getElementById("root").innerHTML = `
    <div class="test-layout">
      <div class="question-nav">${renderNavTabs()}</div>
      <div class="test-card">
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

function parseExplanation(text, ownTopicId) {
  // Explanation strings contain [learn more](topic_id#heading_id). Resolve
  // topic_id to the real published article URL via site_index.
  return text.replace(/\[([^\]]+)\]\(([^)#]+)#([^)]+)\)/g, (match, label, tId, headingId) => {
    const entry = siteIndex.find(item => item.topic_id === tId);
    if (!entry) return label; // fall back to plain text if not found
    return `<a href="../${entry.url}#${headingId}">${label}</a>`;
  });
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
  if (answers[current]) return;
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

  document.getElementById("root").innerHTML = `
    <div class="score-summary">
      <h2>${timedOut ? "Time's up" : "Practice complete"}</h2>
      <div class="big-score">${correctCount} / ${questions.length}</div>
      <p style="color: var(--ink-soft);">${answeredCount} of ${questions.length} questions answered</p>
      <a class="btn" href="index.html" style="text-decoration:none; display:inline-block; margin-top: 16px;">Back to practice tests</a>
    </div>
  `;
}

init();
