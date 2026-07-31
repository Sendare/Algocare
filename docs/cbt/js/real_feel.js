const params = new URLSearchParams(window.location.search);
const testNumber = params.get("test");

let config = { question_count: 250, seconds_per_question: 30, min_answered_to_submit: 125 };
let questions = [];
let current = 0;
let answers = []; // answers[i] = "A" | "B" | ... | null (never marked correct/incorrect client-side)
let timeRemaining = 0;
let timerInterval = null;
let finished = false;

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

  answers = new Array(questions.length).fill(null);
  timeRemaining = questions.length * config.seconds_per_question;
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
      finishExam();
    }
  }, 1000);
}

function updateTimerDisplay() {
  const h = Math.floor(timeRemaining / 3600);
  const m = Math.floor((timeRemaining % 3600) / 60).toString().padStart(2, "0");
  const s = (timeRemaining % 60).toString().padStart(2, "0");
  document.getElementById("timerReadout").textContent = h > 0 ? `${h}:${m}:${s}` : `${m}:${s}`;

  const strip = document.getElementById("pulseStrip");
  strip.classList.remove("warning", "danger");
  if (timeRemaining <= 60) strip.classList.add("danger");
  else if (timeRemaining <= 300) strip.classList.add("warning");
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
    <div class="grid-nav" id="gridNav">${renderGridNav()}</div>
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
      render();
    });
  });

  document.querySelectorAll(".nav-tab").forEach(tab => {
    tab.addEventListener("click", () => {
      current = parseInt(tab.dataset.index, 10);
      render();
    });
  });

  const prevBtn = document.getElementById("prevBtn");
  if (prevBtn) prevBtn.addEventListener("click", () => { current--; render(); });

  const nextBtn = document.getElementById("nextBtn");
  if (nextBtn) nextBtn.addEventListener("click", () => { current++; render(); });

  const submitBtn = document.getElementById("submitBtn");
  if (submitBtn) submitBtn.addEventListener("click", () => {
    if (!submitBtn.disabled) finishExam();
  });
}

function finishExam() {
  if (finished) return;
  finished = true;
  clearInterval(timerInterval);

  let correct = 0;
  questions.forEach((q, i) => {
    if (answers[i] === q.answer) correct++;
  });
  const total = questions.length;
  const pct = Math.round((correct / total) * 100);

  document.getElementById("root").innerHTML = `
    <div class="score-summary">
      <h2>Exam complete</h2>
      <div class="big-score">${correct} / ${total}</div>
      <p style="color: var(--ink-soft);">${pct}% · ${answeredCount()} of ${total} questions answered</p>
      <p style="color: var(--ink-soft); font-size: 0.85rem;">Answers and explanations are not shown for real-feel exams.</p>
      <a class="btn" href="index.html" style="text-decoration:none; display:inline-block; margin-top: 16px;">Back to practice tests</a>
    </div>
  `;
}

init();
