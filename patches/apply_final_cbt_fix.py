#!/usr/bin/env python3
from pathlib import Path

print("🚀 Fixing CBT Calculator, Real-Feel routing, and Results layout...")

# 1. RESTORE INDEX.HTML (Remove calculator from setup page)
index_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Algocare — Practice Tests</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/style.css">
</head>
<body>

<div id="deviceBanner"></div>

<div class="topbar">
  <div class="brand"><span class="pulse-dot"></span>Algocare</div>
  <a href="../index.html" style="font-size: 0.85rem; color: var(--ink-soft);">← Study articles</a>
</div>

<div class="container" id="root">
  <div class="empty-state">Loading...</div>
</div>

<script src="js/index.js"></script>
</body>
</html>"""
Path("cbt-app/index.html").write_text(index_html)

# 2. PRACTICE JS (JAMB UI for exam, Original UI for results)
practice_js = """const params = new URLSearchParams(window.location.search);
const courseSlug = params.get("course");
const topicId = params.get("topic");
const requestedCount = parseInt(params.get("count"), 10) || null;
const secondsPerQuestion = parseInt(params.get("spq"), 10) || 30;
const STORAGE_KEY = `algocare_practice_${window.location.search}`;

let questions = [], current = 0, answers = [], endTime = null, pauseStartedAt = null, timerInterval = null, attemptId = null;

function shuffle(arr) { let a=[...arr]; for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];} return a; }
function saveState() { sessionStorage.setItem(STORAGE_KEY, JSON.stringify({questions,current,answers,endTime,pauseStartedAt,attemptId})); }
function loadState() { try { const r = sessionStorage.getItem(STORAGE_KEY); return r?JSON.parse(r):null; } catch { return null; } }
function clearState() { sessionStorage.removeItem(STORAGE_KEY); }

async function init() {
  try {
    const saved = loadState();
    if (saved && saved.questions.length) {
      ({questions,current,answers,endTime,pauseStartedAt,attemptId} = saved);
    } else {
      let pool = [];
      if (topicId) pool = await (await fetch(`../data/questions/${topicId}.json`)).json();
      else if (courseSlug) pool = await (await fetch(`../data/course_pools/${courseSlug}.json`)).json();
      else { document.getElementById("examRoot").innerHTML = `<div class="empty-state" style="color:#a1a1aa; text-align:center; padding:40px;">No course or topic specified. <a href="index.html">Go back</a></div>`; return; }

      const count = requestedCount ? Math.min(requestedCount, pool.length) : pool.length;
      questions = shuffle(pool).slice(0, count);
      answers = new Array(questions.length).fill(null);
      endTime = Date.now() + questions.length * secondsPerQuestion * 1000;
      attemptId = generateAttemptId();
      saveState();
      logTestStarted(attemptId, "practice", topicId || courseSlug, questions.length);
    }
  } catch (e) { document.getElementById("examRoot").innerHTML = `<div class="empty-state" style="color:#a1a1aa;">Error loading test.</div>`; return; }

  if (!questions.length) return;
  markTestFinished = trackAbandonment(attemptId, "practice", topicId || courseSlug, questions.length, () => answers.filter(a=>a).length);
  reconcilePause();
  if (Date.now() >= endTime) return finishTest(true);
  startTimer(); render();
}

function isPaused() { const a = answers[current]; return !!(a && a.showExplanation); }
function reconcilePause() {
  if (isPaused()) { if (pauseStartedAt === null) { pauseStartedAt = Date.now(); saveState(); } }
  else if (pauseStartedAt !== null) { endTime += Date.now() - pauseStartedAt; pauseStartedAt = null; saveState(); }
}
function startTimer() {
  updateTimerDisplay();
  timerInterval = setInterval(() => {
    if (isPaused()) return updateTimerDisplay();
    if (Date.now() >= endTime) { clearInterval(timerInterval); finishTest(true); return; }
    updateTimerDisplay();
  }, 1000);
}
function updateTimerDisplay() {
  const rem = Math.max(0, Math.round((endTime - Date.now()) / 1000));
  const m = Math.floor(rem / 60).toString().padStart(2, "0");
  const s = (rem % 60).toString().padStart(2, "0");
  document.getElementById("examTimer").textContent = isPaused() ? "PAUSED" : `${m}:${s}`;
}

function render() {
  reconcilePause();
  const q = questions[current];
  const ans = answers[current];

  const opts = Object.keys(q.options).map(k => {
    let cls = "exam-opt";
    if (ans) {
      if (k === ans.selected) cls += " selected";
      if (k === q.answer) cls += " correct";
      if (k === ans.selected && k !== q.answer) cls += " incorrect";
    }
    return `<button class="${cls}" onclick="selectAnswer('${k}')" ${ans?'disabled':''}>
      <div class="opt-letter">${k}</div><div>${q.options[k]}</div>
    </button>`;
  }).join("");

  const expHtml = ans ? `
    <div class="explanation-box" style="margin-top:20px; padding:16px; background:#18181b; border-left:4px solid #f59e0b; color:#a1a1aa">
      ${ans.showExplanation ? parseExplanation(q.explanation, q.topic_id) : `<button class="btn" style="background:#27272a; color:#fff; border:none;" onclick="showExp()">Show Explanation</button>`}
    </div>
    <div class="exam-actions" style="margin-top:20px">
      <button class="exam-btn exam-btn-next" onclick="nextQ()">${current < questions.length - 1 ? "Next Question" : "Finish"}</button>
    </div>
  ` : '';

  document.getElementById("examRoot").innerHTML = `
    <div class="exam-main">
      <div class="exam-q-info">
        <span>Question ${current + 1} of ${questions.length}</span>
        <span>| Answered: ${answers.filter(a=>a).length}/${questions.length}</span>
      </div>
      <div class="exam-card">
        <div class="exam-q-text">${q.question}</div>
        <div class="exam-options">${opts}</div>
        ${expHtml}
      </div>
      <div class="exam-actions" style="margin-top:auto">
        <button class="exam-btn exam-btn-prev" onclick="prevQ()" ${current===0?'disabled':''}>← Prev (P)</button>
        ${!ans ? `<button class="exam-btn exam-btn-next" onclick="nextQ()">Next (N) →</button>` : ''}
      </div>
    </div>
    <div class="exam-palette">
      <div class="palette-header"><span>Question Palette</span></div>
      <div class="palette-grid">
        ${questions.map((_,i) => {
          let c = "palette-btn";
          if (i === current) c += " current";
          else if (answers[i]) c += answers[i].isCorrect ? " answered" : " flagged";
          return `<button class="${c}" onclick="jumpTo(${i})">${i+1}</button>`;
        }).join("")}
      </div>
    </div>
  `;
}

function parseExplanation(text, ownId) {
  return text.replace(/\\[([^\\]]+)\\]\\(([^)#]+)#([^)]+)\\)/g, (m, l, tid, hid) => {
    const entry = window.siteIndex?.find(i => i.topic_id === tid);
    return entry ? `<a href="../${entry.url}#${hid}" style="color:#f59e0b">${l}</a>` : l;
  });
}
function selectAnswer(k) { answers[current] = { selected: k, isCorrect: k === questions[current].answer, showExplanation: false }; saveState(); render(); }
function showExp() { answers[current].showExplanation = true; saveState(); render(); }
function jumpTo(i) { current = i; saveState(); render(); }
function nextQ() { if (current < questions.length - 1) { current++; saveState(); render(); } else { finishTest(false); } }
function prevQ() { if (current > 0) { current--; saveState(); render(); } }

function finishTest(timedOut) {
  clearInterval(timerInterval);
  const total = questions.length, attempted = answers.filter(a => a).length, correct = answers.filter(a => a && a.isCorrect).length;
  const pctOfAttempted = attempted > 0 ? Math.round((correct / attempted) * 100) : 0;
  const pctOfTotal = Math.round((correct / total) * 100);

  markTestFinished(); logTestFinished(attemptId, "practice", topicId || courseSlug, total, attempted, correct); clearState();

  // RESTORE LIGHT THEME FOR ORIGINAL RESULTS PAGE
  document.body.classList.remove('exam-theme');
  
  document.getElementById("examRoot").innerHTML = `
    <div class="score-summary" style="background: var(--paper); min-height: 100vh; padding: 40px 20px; color: var(--ink);">
      <h2>${timedOut ? "Time's up" : "Practice complete"}</h2>
      <div class="big-score" style="color: var(--ink);">${correct} out of ${total}</div>
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

window.addEventListener("load", async () => {
  window.siteIndex = await (await fetch("../site_index.json")).json();
  init();
});
"""
Path("cbt-app/js/practice.js").write_text(practice_js)

# 3. REAL FEEL JS (Fixing the routing & restoring original light results)
real_feel_js = """const params = new URLSearchParams(window.location.search);
const testNumber = params.get("test");
const STORAGE_KEY = testNumber ? `algocare_realfeel_${testNumber}` : null;

let config = { question_count: 250, seconds_per_question: 30, min_answered_to_submit: 125 };
let questions = [], current = 0, answers = [], endTime = null, timerInterval = null, finished = false, attemptId = null;
let markTestFinished = () => {};

function saveState() { if (!STORAGE_KEY || finished) return; sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ current, answers, endTime, attemptId })); }
function loadState() { if (!STORAGE_KEY) return null; try { const raw = sessionStorage.getItem(STORAGE_KEY); return raw ? JSON.parse(raw) : null; } catch { return null; } }
function clearState() { if (STORAGE_KEY) sessionStorage.removeItem(STORAGE_KEY); }

async function init() {
  if (!testNumber) { document.getElementById("examRoot").innerHTML = `<div class="empty-state" style="color:#a1a1aa; text-align:center; padding:40px;">No exam specified. <a href="index.html">Go back</a>.</div>`; return; }
  try {
    const [configRes, qRes] = await Promise.all([
      fetch("../data/real_feel_config.json").catch(() => null),
      fetch(`../data/real_feel_tests/test_${testNumber}.json`),
    ]);
    if (configRes && configRes.ok) config = await configRes.json();
    questions = await qRes.json();
  } catch (err) { document.getElementById("examRoot").innerHTML = `<div class="empty-state" style="color:#a1a1aa; text-align:center; padding:40px;">Couldn't load this exam. <a href="index.html">Go back</a>.</div>`; return; }

  if (!questions.length) return;
  const saved = loadState();
  if (saved && Array.isArray(saved.answers) && saved.answers.length === questions.length) {
    current = saved.current; answers = saved.answers; endTime = saved.endTime; attemptId = saved.attemptId;
  } else {
    answers = new Array(questions.length).fill(null);
    endTime = Date.now() + questions.length * config.seconds_per_question * 1000;
    attemptId = generateAttemptId();
    saveState();
    logTestStarted(attemptId, "real_feel", testNumber, questions.length);
  }
  markTestFinished = trackAbandonment(attemptId, "real_feel", testNumber, questions.length, () => answers.filter(a => a !== null).length);
  if (Date.now() >= endTime) { finishExam(); return; }
  startTimer(); render();
}

function startTimer() {
  updateTimerDisplay();
  timerInterval = setInterval(() => {
    if (Date.now() >= endTime) { clearInterval(timerInterval); finishExam(); return; }
    updateTimerDisplay();
  }, 1000);
}

function updateTimerDisplay() {
  const rem = Math.max(0, Math.round((endTime - Date.now()) / 1000));
  const h = Math.floor(rem / 3600), m = Math.floor((rem % 3600) / 60).toString().padStart(2, "0"), s = (rem % 60).toString().padStart(2, "0");
  document.getElementById("examTimer").textContent = h > 0 ? `${h}:${m}:${s}` : `${m}:${s}`;
}

function answeredCount() { return answers.filter(a => a !== null).length; }

function render() {
  if (finished) return;
  const q = questions[current], selected = answers[current];
  const opts = Object.keys(q.options).map(k => {
    const cls = "exam-opt" + (k === selected ? " selected" : "");
    return `<button class="${cls}" onclick="selectAnswer('${k}')"><div class="opt-letter">${k}</div><div>${q.options[k]}</div></button>`;
  }).join("");

  const canSubmit = answeredCount() >= config.min_answered_to_submit;

  document.getElementById("examRoot").innerHTML = `
    <div class="exam-main">
      <div class="exam-q-info">
        <span>Question ${current + 1} of ${questions.length}</span>
        <span>| Answered: ${answeredCount()}/${questions.length}</span>
      </div>
      <div class="exam-card">
        <div class="exam-q-text">${q.question}</div>
        <div class="exam-options">${opts}</div>
      </div>
      <div class="exam-actions" style="margin-top:auto">
        <button class="exam-btn exam-btn-prev" onclick="prevQ()" ${current === 0 ? "disabled" : ""}>← Prev (P)</button>
        <button class="exam-btn exam-btn-next" onclick="nextQ()" ${current === questions.length - 1 ? "disabled" : ""}>Next (N) →</button>
        <button class="exam-btn exam-btn-submit" onclick="finishExam()" ${canSubmit ? "" : "disabled"} style="margin-left:auto; background: #ef4444; color: white;">Submit Exam ${canSubmit ? "" : `(need ${config.min_answered_to_submit - answeredCount()} more)`}</button>
      </div>
    </div>
    <div class="exam-palette">
      <div class="palette-header"><span>Question Palette</span></div>
      <div class="palette-grid">
        ${questions.map((_, i) => {
          let c = "palette-btn";
          if (i === current) c += " current";
          else if (answers[i]) c += " answered";
          return `<button class="${c}" onclick="jumpTo(${i})">${i + 1}</button>`;
        }).join("")}
      </div>
    </div>
  `;
}

function selectAnswer(k) { answers[current] = k; saveState(); render(); }
function jumpTo(i) { current = i; saveState(); render(); }
function prevQ() { if (current > 0) { current--; saveState(); render(); } }
function nextQ() { if (current < questions.length - 1) { current++; saveState(); render(); } }

function finishExam() {
  if (finished) return;
  finished = true;
  clearInterval(timerInterval);
  const total = questions.length, attempted = answeredCount();
  let correct = 0;
  questions.forEach((q, i) => { if (answers[i] === q.answer) correct++; });
  const pctOfAttempted = attempted > 0 ? Math.round((correct / attempted) * 100) : 0;
  const pctOfTotal = Math.round((correct / total) * 100);

  markTestFinished(); logTestFinished(attemptId, "real_feel", testNumber, total, attempted, correct); clearState();

  // RESTORE LIGHT THEME FOR ORIGINAL RESULTS PAGE
  document.body.classList.remove('exam-theme');

  document.getElementById("examRoot").innerHTML = `
    <div class="score-summary" style="background: var(--paper); min-height: 100vh; padding: 40px 20px; color: var(--ink);">
      <h2>Exam complete</h2>
      <div class="big-score" style="color: var(--ink);">${correct} out of ${total}</div>
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

window.addEventListener("load", async () => { init(); });
"""
Path("cbt-app/js/real_feel.js").write_text(real_feel_js)

# 4. HTML TEMPLATES
practice_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#09090b">
<title>Algocare — Exam</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/style.css">
<link rel="stylesheet" href="exam.css?v=3">
</head>
<body class="exam-theme">
<div class="exam-header">
  <div class="exam-header-left">
    <span class="exam-header-title">Algocare CBT</span>
    <span style="font-size:0.75rem; color:#a1a1aa">Practice Mode</span>
  </div>
  <div class="exam-header-right">
    <button class="exam-btn-submit" style="background:#18181b; border:1px solid #27272a; color:#fff" onclick="toggleCalculator()">Calc</button>
    <div class="exam-timer" id="examTimer">--:--</div>
    <button class="exam-btn-submit" onclick="finishTest(true)">Submit</button>
  </div>
</div>
<div id="examRoot" style="display:flex; flex-direction:column; flex:1; overflow:hidden;"></div>

<div id="calcModal" class="calc-modal">
  <div class="calc-header">
    <span>Calculator</span>
    <button class="calc-close" onclick="toggleCalculator()">✕</button>
  </div>
  <div class="calc-display" id="calcDisplay">0</div>
  <div class="calc-grid">
    <button class="calc-btn" onclick="calcInput('7')">7</button>
    <button class="calc-btn" onclick="calcInput('8')">8</button>
    <button class="calc-btn" onclick="calcInput('9')">9</button>
    <button class="calc-btn op" onclick="calcInput('/')">÷</button>
    <button class="calc-btn" onclick="calcInput('4')">4</button>
    <button class="calc-btn" onclick="calcInput('5')">5</button>
    <button class="calc-btn" onclick="calcInput('6')">6</button>
    <button class="calc-btn op" onclick="calcInput('*')">×</button>
    <button class="calc-btn" onclick="calcInput('1')">1</button>
    <button class="calc-btn" onclick="calcInput('2')">2</button>
    <button class="calc-btn" onclick="calcInput('3')">3</button>
    <button class="calc-btn op" onclick="calcInput('-')">-</button>
    <button class="calc-btn" onclick="calcInput('0')">0</button>
    <button class="calc-btn" onclick="calcInput('.')">.</button>
    <button class="calc-btn op" onclick="calcInput('+')">+</button>
    <button class="calc-btn op" onclick="calcInput('C')">C</button>
    <button class="calc-btn eq" onclick="calcInput('=')">=</button>
  </div>
</div>

<script src="../assets/analytics.js"></script>
<script src="js/util.js"></script>
<script src="js/practice.js"></script>
</body>
</html>"""
Path("cbt-app/practice.html").write_text(practice_html)

real_feel_html = practice_html.replace('practice.js', 'real_feel.js').replace('Practice Mode', 'Real-Feel Exam').replace('finishTest(true)', 'finishExam()')
Path("cbt-app/real_feel.html").write_text(real_feel_html)

print("✅ Successfully overwrote ALL CBT HTML, CSS, and JS files.")
