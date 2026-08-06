const params = new URLSearchParams(window.location.search);
const testNumber = params.get("test");
const STORAGE_KEY = testNumber ? `algocare_realfeel_${testNumber}` : null;

let config = { question_count: 250, seconds_per_question: 30, min_answered_to_submit: 125 };
let questions = [];
let current = 0;
let answers = [];
let endTime = null;
let timerInterval = null;
let finished = false;
let attemptId = null;
let markTestFinished = () => {};

function saveState() {
  if (!STORAGE_KEY || finished) return;
  sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ current, answers, endTime, attemptId }));
}

function loadState() {
  if (!STORAGE_KEY) return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

function clearState() {
  if (STORAGE_KEY) sessionStorage.removeItem(STORAGE_KEY);
}

async function init() {
  if (!testNumber) {
    document.getElementById("root").innerHTML =
      `<div class="empty-state">No exam specified. <a href="index.html">Go back</a>.</div>`;
    return;
  }

  try {
    const [configRes, qRes] = await Promise.all([
      fetch("../data/real_feel_config.json").catch(() => null),
      fetch(`../data/real_feel_tests/test_${testNumber}.json`),
    ]);
    if (configRes && configRes.ok) config = await configRes.json();
    questions = await qRes.json();
  } catch (err) {
    document.getElementById("root").innerHTML =
      `<div class="empty-state">Couldn't load this exam. <a href="index.html">Go back</a>.</div>`;
    console.error(err);
    return;
  }

  if (!questions.length) {
    document.getElementById("root").innerHTML = `<div class="empty-state">This exam has no questions.</div>`;
    return;
  }

  const saved = loadState();
  if (saved && Array.isArray(saved.answers) && saved.answers.length === questions.length) {
    current = saved.current;
    answers = saved.answers;
    endTime = saved.endTime;
    attemptId = saved.attemptId;
  } else {
    answers = new Array(questions.length).fill(null);
    endTime = Date.now() + questions.length * config.seconds_per_question * 1000;
    attemptId = generateAttemptId();
    saveState();

    logTestStarted(attemptId, "real_feel", testNumber, questions.length);
  }

  markTestFinished = trackAbandonment(
    attemptId, "real_feel", testNumber, questions.length,
    () => answeredCount()
  );

  if (Date.now() >= endTime) {
    finishExam();
    return;
  }

  startTimer();
  render();
}

function startTimer() {
  updateTimerDisplay();
  timerInterval = setInterval(() => {
    if (Date.now() >= endTime) {
      clearInterval(timerInterval);
      finishExam();
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
  const h = Math.floor(remaining / 3600);
  const m = Math.floor((remaining % 3600) / 60).toString().padStart(2, "0");
  const s = (remaining % 60).toString().padStart(2, "0");
  document.getElementById("timerReadout").textContent = h > 0 ? `${h}:${m}:${s}` : `${m}:${s}`;

  const strip = document.getElementById("pulseStrip");
  strip.classList.remove("warning", "danger");
  if (remaining <= 60) strip.classList.add("danger");
  else if (remaining <= 300) strip.classList.add("warning");
}

function answeredCount() {
  return answers.filter(a => a !== null).length;
}

function render() {
  if (finished) return;

  const q = questions[current];
  const selected = answers[current];
  const optionKeys = Object.keys(q.options);

  const optionsHtml = optionKeys.map(key => {
    const cls = "option" + (key === selected ? " selected" : "");
    return `<button class="${cls}" data-key="${key}"><strong>${key}.</strong> ${q.options[key]}</button>`;
  }).join("");

  const canSubmit = answeredCount() >= config.min_answered_to_submit;

  document.getElementById("root").innerHTML = `
    <div class="test-card">
      <div class="question-number">Question ${current + 1} of ${questions.length} · ${answeredCount()} answered</div>
      <div class="question-text">${q.question}</div>
      <div class="options-list">${optionsHtml}</div>
      <div class="action-row">
        <button class="btn secondary" id="prevBtn" ${current === 0 ? "disabled" : ""}>← Prev</button>
        <button class="btn" id="nextBtn" ${current === questions.length - 1 ? "disabled" : ""}>Next →</button>
        <button class="btn" id="submitBtn" ${canSubmit ? "" : "disabled"} style="margin-left:auto; background: var(--brick); border-color: var(--brick);">
          Submit exam ${canSubmit ? "" : `(need ${config.min_answered_to_submit - answeredCount()} more)`}
        </button>
      </div>
    </div>
    <div class="grid-nav" id="gridNav">${renderGridNav()}</div>
  `;

  attachHandlers();
}

function renderGridNav() {
  return questions.map((_, i) => {
    let cls = "nav-tab";
    if (i === current) cls += " current";
    else if (answers[i]) cls += " answered";
    return `<div class="${cls}" data-index="${i}">${i + 1}</div>`;
  }).join("");
}

function attachHandlers() {
  document.querySelectorAll(".option").forEach(btn => {
    btn.addEventListener("click", () => {
      answers[current] = btn.dataset.key;
      saveState();
      render();
    });
  });

  document.querySelectorAll(".nav-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      current = parseInt(tab.dataset.index, 10);
      saveState();
      render();
    });
  });

  const prevBtn = document.getElementById("prevBtn");
  if (prevBtn) prevBtn.addEventListener("click", () => { current--; saveState(); render(); });

  const nextBtn = document.getElementById("nextBtn");
  if (nextBtn) nextBtn.addEventListener("click", () => { current++; saveState(); render(); });

  const submitBtn = document.getElementById("submitBtn");
  if (submitBtn) submitBtn.addEventListener("click", () => {
    if (!submitBtn.disabled) finishExam();
  });
}

function finishExam() {
  if (finished) return;
  finished = true;
  clearInterval(timerInterval);

  const total = questions.length;
  const attempted = answeredCount();
  let correct = 0;
  questions.forEach((q, i) => {
    if (answers[i] === q.answer) correct++;
  });
  const pctOfAttempted = attempted > 0 ? Math.round((correct / attempted) * 100) : 0;
  const pctOfTotal = Math.round((correct / total) * 100);

  markTestFinished();
  logTestFinished(attemptId, "real_feel", testNumber, total, attempted, correct);
  clearState();

  document.getElementById("root").innerHTML = `
    <div class="score-summary">
      <h2>Exam complete</h2>
      <div class="big-score">${correct} out of ${total}</div>
      <div style="color: var(--ink-soft); margin-top: 8px;">
        <p style="margin: 4px 0;">Attempted: ${attempted} out of ${total}</p>
        <p style="margin: 4px 0;">Correct answers: ${correct}</p>
        <p style="margin: 4px 0;">Score (of attempted): ${correct} out of ${attempted} · ${pctOfAttempted}%</p>
        <p style="margin: 4px 0;">Score (of all ${total}): ${correct} out of ${total} · ${pctOfTotal}%</p>
      </div>
      <p style="color: var(--ink-soft); font-size: 0.85rem;">Answers and explanations are not shown for real-feel exams.</p>
      <div id="reviewWidgetContainer"></div>
      <a class="btn" href="index.html" style="text-decoration:none; display:inline-block; margin-top: 16px;">Back to practice tests</a>
    </div>
  `;

  attachReviewWidget("reviewWidgetContainer", "real_feel");
}

init();
