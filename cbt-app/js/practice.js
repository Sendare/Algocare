const params = new URLSearchParams(window.location.search);
const courseSlug = params.get("course");
const topicId = params.get("topic");
const requestedCount = parseInt(params.get("count"), 10) || null;
const secondsPerQuestion = parseInt(params.get("spq"), 10) || 30;

// Keyed on the full query string so different course/topic/count/spq combos
// don't collide, but reloading the *same* URL resumes the *same* attempt.
const STORAGE_KEY = `algocare_practice_${window.location.search}`;

let questions = [];
let siteIndex = [];
let current = 0;
let answers = []; // { selected, isCorrect, showExplanation }
let endTime = null; // absolute timestamp (ms) - survives refresh/backgrounding
let pauseStartedAt = null; // timestamp (ms) when the current pause began, or null
let timerInterval = null;
let attemptId = null;
let markTestFinished = () => {};

function shuffle(arr) {
  const a = [...arr];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function saveState() {
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify({
    questions, current, answers, endTime, pauseStartedAt, attemptId,
  }));
}

function loadState() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function clearState() {
  sessionStorage.removeItem(STORAGE_KEY);
}

async function init() {
  try {
    const siteRes = await fetch("../site_index.json");
    siteIndex = await siteRes.json();

    // Resume an in-progress attempt for this exact URL if one exists in this tab.
    const saved = loadState();
    if (saved && Array.isArray(saved.questions) && saved.questions.length) {
      questions = saved.questions;
      current = saved.current;
      answers = saved.answers;
      endTime = saved.endTime;
      pauseStartedAt = saved.pauseStartedAt ?? null;
      attemptId = saved.attemptId;
    } else {
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
      answers = new Array(questions.length).fill(null);
      endTime = Date.now() + questions.length * secondsPerQuestion * 1000;
      pauseStartedAt = null;
      attemptId = generateAttemptId();
      saveState();

      logTestStarted(attemptId, "practice", topicId || courseSlug, questions.length);
    }
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

  markTestFinished = trackAbandonment(
    attemptId, "practice", topicId || courseSlug, questions.length,
    () => answers.filter(a => a).length
  );

  // Reconcile any pause that was active across a reload/background before
  // checking whether time's up.
  reconcilePause();

  if (Date.now() >= endTime) {
    finishTest(true);
    return;
  }

  startTimer();
  render();
}

function isPaused() {
  const a = answers[current];
  return !!(a && a.showExplanation);
}

function reconcilePause() {
  if (isPaused()) {
    if (pauseStartedAt === null) {
      pauseStartedAt = Date.now();
      saveState();
    }
  } else if (pauseStartedAt !== null) {
    endTime += Date.now() - pauseStartedAt;
    pauseStartedAt = null;
    saveState();
  }
}

function startTimer() {
  updateTimerDisplay();
  timerInterval = setInterval(() => {
    if (isPaused()) {
      updateTimerDisplay();
      return;
    }
    if (Date.now() >= endTime) {
      clearInterval(timerInterval);
      finishTest(true);
      return;
    }
    updateTimerDisplay();
  }, 1000);
}

function timeRemainingSeconds() {
  return Math.max(0, Math.round((endTime - Date.now()) / 1000));
}

function updateTimerDisplay() {
  const remaining = timeRemainingSeconds();
  const paused = isPaused();
  const m = Math.floor(remaining / 60).toString().padStart(2, "0");
  const s = (remaining % 60).toString().padStart(2, "0");
  document.getElementById("timerReadout").textContent = paused ? "PAUSED" : `${m}:${s}`;

  const strip = document.getElementById("pulseStrip");
  strip.classList.remove("warning", "danger");
  if (remaining <= 60) strip.classList.add("danger");
  else if (remaining <= 180) strip.classList.add("warning");
}

function render() {
  reconcilePause();

  const q = questions[current];
  const answer = answers[current];
  const optionKeys = Object.keys(q.options);

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

  const resultBanner = answer.isCorrect
    ? ""
    : `<p style="color: var(--brick); font-weight: 600; margin-bottom: 8px;">Not quite — here's the correct answer:</p>`;

  const explanationHtml = answer ? `
    ${answer.showExplanation ? `<div class="explanation-box">${resultBanner}${parseExplanation(q.explanation, q.topic_id)}</div>` : ""}
    <div class="action-row">
      ${!answer.showExplanation ? `<button class="btn secondary" id="showExplanationBtn">Show explanation</button>` : ""}
      <button class="btn" id="nextBtn">${current < questions.length - 1 ? "Next question" : "Finish"}</button>
    </div>
  ` : "";

  document.getElementById("root").innerHTML = `
    <div class="test-layout">
      <div class="test-card">
        <div class="question-number">Question ${current + 1} of ${questions.length}</div>
        <div class="question-text">${q.question}</div>
        <div class="options-list">${optionsHtml}</div>
        ${explanationHtml}
      </div>
      <div class="question-nav">${renderNavTabs()}</div>
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
  return text.replace(/\[([^\]]+)\]\(([^)#]+)#([^)]+)\)/g, (match, label, tId, headingId) => {
    const entry = siteIndex.find(item => item.topic_id === tId);
    if (!entry) return label;
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
      saveState();
      render();
    });
  });

  const showExplanationBtn = document.getElementById("showExplanationBtn");
  if (showExplanationBtn) {
    showExplanationBtn.addEventListener("click", () => {
      answers[current].showExplanation = true;
      saveState();
      render();
    });
  }

  const nextBtn = document.getElementById("nextBtn");
  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      if (current < questions.length - 1) {
        current++;
        saveState();
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
  saveState();
  render();
}

function finishTest(timedOut) {
  clearInterval(timerInterval);

  const total = questions.length;
  const attempted = answers.filter(a => a).length;
  const correct = answers.filter(a => a && a.isCorrect).length;
  const pctOfAttempted = attempted > 0 ? Math.round((correct / attempted) * 100) : 0;
  const pctOfTotal = Math.round((correct / total) * 100);

  markTestFinished();
  logTestFinished(attemptId, "practice", topicId || courseSlug, total, attempted, correct);
  clearState();

  document.getElementById("root").innerHTML = `
    <div class="score-summary">
      <h2>${timedOut ? "Time's up" : "Practice complete"}</h2>
      <div class="big-score">${correct} out of ${total}</div>
      <div style="color: var(--ink-soft); margin-top: 8px;">
        <p style="margin: 4px 0;">Attempted: ${attempted} out of ${total}</p>
        <p style="margin: 4px 0;">Correct answers: ${correct}</p>
        <p style="margin: 4px 0;">Score (of attempted): ${correct} out of ${attempted} · ${pctOfAttempted}%</p>
        <p style="margin: 4px 0;">Score (of all ${total}): ${correct} out of ${total} · ${pctOfTotal}%</p>
      </div>
      <div id="reviewWidgetContainer"></div>
      <a class="btn" href="index.html" style="text-decoration:none; display:inline-block; margin-top: 16px;">Back to practice tests</a>
    </div>
  `;

  attachReviewWidget("reviewWidgetContainer", "practice");
}

init();
