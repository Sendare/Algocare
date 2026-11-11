#!/usr/bin/env python3
from pathlib import Path

print("🚀 Starting Phase 2 Fix: CSS isolation, results revert, and Real-Feel fix...")

# ==========================================
# 1. EXAM CSS (Isolated Dark Theme)
# ==========================================
exam_css = """/* JAMB Exam Specific Theme */
body.exam-theme { background: #09090b !important; color: #f4f4f5 !important; margin: 0; height: 100vh; display: flex; flex-direction: column; font-family: var(--body); }
.exam-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #09090b; border-bottom: 1px solid #27272a; color: #fff; flex-shrink: 0; }
.exam-header-left { display: flex; flex-direction: column; }
.exam-header-title { font-family: var(--display); font-size: 1.2rem; font-weight: 700; color: #f59e0b; }
.exam-header-right { display: flex; align-items: center; gap: 12px; }
.exam-timer { background: #18181b; border: 1px solid #27272a; padding: 6px 12px; border-radius: 6px; font-family: var(--mono); font-weight: 700; font-size: 1.1rem; color: #fff; }
.exam-btn-submit { background: #f59e0b; color: #000; padding: 8px 16px; border-radius: 6px; font-weight: 700; border: none; cursor: pointer; }
.exam-main { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; max-width: 800px; margin: 0 auto; width: 100%; }
.exam-q-info { display: flex; justify-content: space-between; align-items: center; background: #18181b; border: 1px solid #27272a; padding: 10px 16px; border-radius: 6px; color: #a1a1aa; font-size: 0.85rem; margin-bottom: 16px; font-weight: 600; }
.exam-card { background: #18181b; border: 1px solid #27272a; border-radius: 6px; padding: 24px; margin-bottom: 20px; }
.exam-q-text { font-size: 1.15rem; font-weight: 500; color: #fff; margin-bottom: 24px; line-height: 1.6; }
.exam-options { display: flex; flex-direction: column; gap: 12px; }
.exam-opt { display: flex; align-items: center; gap: 16px; padding: 16px; background: #09090b; border: 2px solid #27272a; border-radius: 6px; cursor: pointer; text-align: left; transition: all 0.2s; color: #f4f4f5; width: 100%; }
.exam-opt:hover { border-color: rgba(245, 158, 11, 0.5); }
.exam-opt.selected { border-color: #f59e0b; background: rgba(245, 158, 11, 0.1); }
.exam-opt.selected .opt-letter { background: #f59e0b; color: #000; }
.exam-opt.correct { border-color: #10b981; background: rgba(16, 185, 129, 0.1); }
.exam-opt.correct .opt-letter { background: #10b981; color: #fff; }
.exam-opt.incorrect { border-color: #ef4444; background: rgba(239, 68, 68, 0.1); }
.exam-opt.incorrect .opt-letter { background: #ef4444; color: #fff; }
.opt-letter { width: 32px; height: 32px; border-radius: 50%; background: #27272a; color: #a1a1aa; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }
.exam-actions { display: flex; gap: 16px; margin-top: auto; padding-bottom: 20px; }
.exam-btn { flex: 1; padding: 14px; border-radius: 6px; font-weight: 700; font-size: 1rem; border: none; cursor: pointer; display: flex; justify-content: center; align-items: center; gap: 8px; }
.exam-btn-prev { background: #18181b; color: #d4d4d8; border: 2px solid #27272a; }
.exam-btn-next { background: #f59e0b; color: #000; }
.exam-palette { background: #09090b; border-top: 4px solid #27272a; padding: 16px; flex-shrink: 0; }
.palette-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-weight: 700; color: #fff; font-size: 0.9rem; }
.palette-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(36px, 1fr)); gap: 8px; }
.palette-btn { height: 36px; border-radius: 6px; border: 1px solid #27272a; background: #18181b; color: #a1a1aa; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; }
.palette-btn.answered { background: #10b981; color: #fff; border-color: #059669; }
.palette-btn.flagged { background: #f59e0b; color: #000; border-color: #d97706; }
.palette-btn.current { outline: 2px solid #3b82f6; outline-offset: 2px; }
.calc-modal { position: fixed; bottom: 20px; right: 20px; width: 280px; background: #18181b; border: 1px solid #27272a; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); z-index: 100; display: none; flex-direction: column; }
.calc-modal.open { display: flex; }
.calc-header { display: flex; justify-content: space-between; padding: 10px 16px; border-bottom: 1px solid #27272a; color: #fff; font-weight: 700; }
.calc-close { background: none; border: none; color: #ef4444; cursor: pointer; font-weight: bold; }
.calc-display { padding: 16px; font-family: var(--mono); font-size: 1.5rem; text-align: right; color: #fff; background: #09090b; margin: 10px; border-radius: 6px; border: 1px solid #27272a; overflow-x: auto; }
.calc-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; padding: 10px; }
.calc-btn { padding: 12px; border-radius: 6px; border: none; background: #27272a; color: #fff; font-weight: 700; cursor: pointer; font-size: 1rem; }
.calc-btn.op { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
.calc-btn.eq { background: #f59e0b; color: #000; grid-column: span 2; }
"""
Path("cbt-app/exam.css").write_text(exam_css)

# ==========================================
# 2. UTIL JS (Calculator)
# ==========================================
calc_js = """
let calcExpr = '';
function toggleCalculator() { document.getElementById('calcModal').classList.toggle('open'); }
function calcInput(val) {
  const display = document.getElementById('calcDisplay');
  if (val === 'C') { calcExpr = ''; }
  else if (val === '=') { try { calcExpr = String(eval(calcExpr || '0')); } catch { calcExpr = 'Error'; } }
  else { if (calcExpr === 'Error') calcExpr = ''; calcExpr += val; }
  display.textContent = calcExpr || '0';
}
"""
Path("cbt-app/js/util.js").write_text(calc_js)

# ==========================================
# 3. PRACTICE JS
# ==========================================
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

  document.body.classList.remove('exam-theme');
  
  document.getElementById("examRoot").innerHTML = `
    <div class="score-summary" style="min-height: 100vh; display: flex; flex-direction: column; justify-content: center; padding: 40px 20px;">
      <h2 style="color: var(--ink);">${timedOut ? "Time's up" : "Practice complete"}</h2>
      <div class="big-score">${correct} out of ${total}</div>
      <div style="color: var(--ink-soft); margin-top: 8px;">
        <p style="margin: 4px 0;">Attempted: ${attempted} out of ${total}</p>
        <p style="margin: 4px 0;">Correct answers: ${correct}</p>
        <p style="margin: 4px 0;">Score (of attempted): ${correct} out of ${attempted} · ${pctOfAttempted}%</p>
        <p style="margin: 4px 0;">Score (of all ${total}): ${correct} out of ${total} · ${pctOfTotal}%</p>
      </div>
      <div id="reviewWidgetContainer"></div>
      <a class="btn" href="index.html" style="text-decoration:none; display:inline-block; margin: 16px auto 0; width: fit-content;">Back to practice tests</a>
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

# ==========================================
# 4. REAL FEEL JS
# ==========================================
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

  document.body.classList.remove('exam-theme');

  document.getElementById("examRoot").innerHTML = `
    <div class="score-summary" style="min-height: 100vh; display: flex; flex-direction: column; justify-content: center; padding: 40px 20px;">
      <h2 style="color: var(--ink);">Exam complete</h2>
      <div class="big-score">${correct} out of ${total}</div>
      <div style="color: var(--ink-soft); margin-top: 8px;">
        <p style="margin: 4px 0;">Attempted: ${attempted} out of ${total}</p>
        <p style="margin: 4px 0;">Correct answers: ${correct}</p>
        <p style="margin: 4px 0;">Score (of attempted): ${correct} out of ${attempted} · ${pctOfAttempted}%</p>
        <p style="margin: 4px 0;">Score (of all ${total}): ${correct} out of ${total} · ${pctOfTotal}%</p>
      </div>
      <p style="color: var(--ink-soft); font-size: 0.85rem; margin-top: 10px;">Answers and explanations are not shown for real-feel exams.</p>
      <div id="reviewWidgetContainer"></div>
      <a class="btn" href="index.html" style="text-decoration:none; display:inline-block; margin: 16px auto 0; width: fit-content;">Back to practice tests</a>
    </div>
  `;
  attachReviewWidget("reviewWidgetContainer", "real_feel");
}

window.addEventListener("load", async () => { init(); });
"""
Path("cbt-app/js/real_feel.js").write_text(real_feel_js)

# ==========================================
# 5. HTML TEMPLATES
# ==========================================
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
<link rel="stylesheet" href="exam.css?v=2">
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
