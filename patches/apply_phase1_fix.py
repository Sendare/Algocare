#!/usr/bin/env python3
import re
from pathlib import Path

print("🚀 Starting Phase 1 Fix...")

# ==========================================
# 1. RESTORE ORIGINAL CSS
# ==========================================
original_css = """/* ===== Algocare CBT — Design Tokens ===== */
:root {
  --paper: #F7F8F7;
  --card: #FFFFFF;
  --ink: #16232E;
  --ink-soft: #46545F;
  --grey: #8A9199;
  --grey-line: #DDE2E1;
  --scrub: #2F6F62;
  --scrub-soft: #E4EEEC;
  --brick: #B14A3A;
  --brick-soft: #F7E9E6;
  --amber: #C98A2E;
  --amber-soft: #FBF0DE;

  --display: 'Space Grotesk', sans-serif;
  --body: 'IBM Plex Sans', sans-serif;
  --mono: 'IBM Plex Mono', monospace;

  --radius: 6px;
  --shadow: 0 1px 2px rgba(22, 35, 46, 0.06), 0 4px 12px rgba(22, 35, 46, 0.05);
}

* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--paper); color: var(--ink); font-family: var(--body); font-size: 16px; line-height: 1.5; }
a { color: var(--scrub); text-decoration: none; }
a:hover { text-decoration: underline; }
h1, h2, h3 { font-family: var(--display); font-weight: 600; margin: 0 0 0.5em 0; letter-spacing: -0.01em; }
button, input { font-family: inherit; font-size: inherit; }
:focus-visible { outline: 2px solid var(--scrub); outline-offset: 2px; }
.container { max-width: 760px; margin: 0 auto; padding: 24px 20px 64px; }
.topbar { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px; border-bottom: 1px solid var(--grey-line); background: var(--card); }
.brand { font-family: var(--display); font-weight: 700; font-size: 1.15rem; color: var(--ink); }
.brand .pulse-dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; background: var(--scrub); margin-right: 8px; animation: pulse-dot 1.6s ease-in-out infinite; }
@keyframes pulse-dot { 0%, 100% { opacity: 1; transform: scale(1); } 50% { opacity: 0.4; transform: scale(0.8); } }
.search-box { width: 100%; padding: 12px 16px; border: 1px solid var(--grey-line); border-radius: var(--radius); background: var(--card); margin-bottom: 24px; }
.branch-group { margin-bottom: 28px; }
.topic-card { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; background: var(--card); border: 1px solid var(--grey-line); border-radius: var(--radius); margin-bottom: 8px; transition: border-color 0.15s ease; }
.topic-card:hover { border-color: var(--scrub); }
.topic-title { font-weight: 500; color: var(--ink); }
.topic-meta { font-family: var(--mono); font-size: 0.78rem; color: var(--grey); }
.topic-actions a { font-size: 0.85rem; font-weight: 600; margin-left: 14px; }
.empty-state { text-align: center; padding: 48px 16px; color: var(--grey); }
.pulse-strip { position: relative; height: 48px; background: var(--ink); overflow: hidden; }
.pulse-strip svg { position: absolute; top: 0; left: 0; height: 100%; width: 200%; animation: pulse-scroll 3s linear infinite; }
.pulse-strip.warning svg { stroke: var(--amber); }
.pulse-strip.danger svg { stroke: var(--brick); }
.pulse-strip svg { stroke: var(--scrub); }
@keyframes pulse-scroll { from { transform: translateX(0); } to { transform: translateX(-50%); } }
.timer-readout { position: absolute; top: 50%; right: 16px; transform: translateY(-50%); font-family: var(--mono); font-size: 1.1rem; font-weight: 600; color: #fff; background: rgba(0,0,0,0.35); padding: 4px 10px; border-radius: var(--radius); }
.test-layout { display: flex; gap: 24px; align-items: flex-start; }
.question-nav { display: flex; flex-direction: column; gap: 6px; flex-shrink: 0; }
.nav-tab { width: 36px; height: 36px; display: flex; align-items: center; justify-content: center; font-family: var(--mono); font-size: 0.85rem; border: 1px solid var(--grey-line); border-radius: var(--radius); background: var(--card); cursor: pointer; color: var(--ink-soft); }
.nav-tab.current { border-color: var(--ink); color: var(--ink); font-weight: 700; }
.nav-tab.answered-correct { background: var(--scrub-soft); border-color: var(--scrub); color: var(--scrub); }
.nav-tab.answered-incorrect { background: var(--brick-soft); border-color: var(--brick); color: var(--brick); }
.nav-tab.answered { background: var(--ink); border-color: var(--ink); color: #fff; }
.grid-nav { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 20px; }
.grid-nav .nav-tab { width: 32px; height: 32px; font-size: 0.72rem; }
.device-banner { background: var(--amber-soft); color: var(--ink); padding: 10px 16px; font-size: 0.85rem; text-align: center; border-bottom: 1px solid var(--amber); }
.mode-card { background: var(--card); border: 1px solid var(--grey-line); border-radius: var(--radius); padding: 20px; margin-bottom: 16px; }
.mode-card h3 { margin-bottom: 6px; }
.mode-card p { color: var(--ink-soft); font-size: 0.9rem; margin: 0 0 14px 0; }
.form-row { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.form-row label { font-family: var(--mono); font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.06em; color: var(--grey); }
.form-row select, .form-row input[type="number"] { padding: 10px 12px; border: 1px solid var(--grey-line); border-radius: var(--radius); background: var(--card); }
.score-summary { text-align: center; padding: 32px 16px; }
.score-summary .big-score { font-family: var(--mono); font-size: 3rem; font-weight: 700; margin: 12px 0; }
.test-card { flex: 1; background: var(--card); border: 1px solid var(--grey-line); border-radius: var(--radius); box-shadow: var(--shadow); padding: 28px; position: relative; }
.question-number { font-family: var(--mono); color: var(--grey); font-size: 0.85rem; margin-bottom: 8px; }
.question-text { font-size: 1.15rem; font-weight: 500; margin-bottom: 20px; }
.option { display: block; width: 100%; text-align: left; padding: 12px 16px; margin-bottom: 8px; border: 1px solid var(--grey-line); border-radius: var(--radius); background: var(--card); cursor: pointer; }
.option:hover { border-color: var(--ink-soft); }
.option.selected { border-color: var(--ink); background: var(--paper); }
.option.correct { border-color: var(--scrub); background: var(--scrub-soft); }
.option.incorrect { border-color: var(--brick); background: var(--brick-soft); }
.action-row { display: flex; gap: 10px; margin-top: 20px; }
.btn { padding: 10px 18px; border-radius: var(--radius); border: 1px solid var(--ink); background: var(--ink); color: #fff; font-weight: 600; cursor: pointer; }
.btn.secondary { background: var(--card); color: var(--ink); }
.btn:disabled { opacity: 0.4; cursor: not-allowed; }
.explanation-box { margin-top: 18px; padding: 16px; background: var(--paper); border-left: 3px solid var(--scrub); border-radius: var(--radius); font-size: 0.95rem; color: var(--ink-soft); }
.explanation-box a { font-weight: 600; }
.breadcrumb { font-family: var(--mono); font-size: 0.78rem; color: var(--grey); margin-bottom: 16px; }
.article-heading { scroll-margin-top: 24px; padding: 20px 0; border-bottom: 1px solid var(--grey-line); }
.article-heading h2 { font-size: 1.15rem; }
.article-heading:target { background: var(--amber-soft); margin: 0 -20px; padding: 20px; }
.test-yourself-link { display: inline-block; margin-top: 24px; padding: 10px 18px; background: var(--scrub); color: #fff; border-radius: var(--radius); font-weight: 600; }
.test-yourself-link:hover { text-decoration: none; opacity: 0.9; }
@media (max-width: 640px) { .test-layout { flex-direction: column; } .question-nav { flex-direction: row; flex-wrap: wrap; } }
@media (prefers-reduced-motion: reduce) { .pulse-strip svg { animation: none; } .brand .pulse-dot { animation: none; } }
.review-widget { margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--grey-line); text-align: left; }
.review-prompt { font-weight: 600; margin-bottom: 8px; }
.star-row { display: flex; gap: 4px; margin-bottom: 12px; }
.star-btn { background: none; border: none; font-size: 1.8rem; line-height: 1; cursor: pointer; color: var(--grey-line); padding: 0; }
.star-btn.filled { color: var(--amber); }
.review-widget textarea { width: 100%; padding: 10px; border: 1px solid var(--grey-line); border-radius: var(--radius); font-family: inherit; margin-bottom: 10px; resize: vertical; }
"""
Path("assets/style.css").write_text(original_css)

# ==========================================
# 2. CREATE EXAM CSS (JAMB Theme)
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
.exam-opt { display: flex; align-items: center; gap: 16px; padding: 16px; background: #09090b; border: 2px solid #27272a; border-radius: 6px; cursor: pointer; text-align: left; transition: all 0.2s; color: #f4f4f5; }
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
# 3. CALCULATOR JS
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
# 4. REWRITE practice.js & real_feel.js (RESTORE RESULTS)
# ==========================================
# We are overwriting the files with the JAMB UI, but replacing the finishTest()
# with your exact original light-theme layout.

base_js = """const params = new URLSearchParams(window.location.search);
const courseSlug = params.get("course");
const topicId = params.get("topic");
const requestedCount = parseInt(params.get("count"), 10) || null;
const secondsPerQuestion = parseInt(params.get("spq"), 10) || 30;
const STORAGE_KEY = `algocare_practice_${window.location.search}`;

let questions = [];
let current = 0;
let answers = [];
let endTime = null;
let pauseStartedAt = null;
let timerInterval = null;
let attemptId = null;

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
  const total = questions.length;
  const attempted = answers.filter(a => a).length;
  const correct = answers.filter(a => a && a.isCorrect).length;
  const pctOfAttempted = attempted > 0 ? Math.round((correct / attempted) * 100) : 0;
  const pctOfTotal = Math.round((correct / total) * 100);

  markTestFinished();
  logTestFinished(attemptId, "practice", topicId || courseSlug, total, attempted, correct);
  clearState();

  document.getElementById("examRoot").innerHTML = `
    <div class="score-summary" style="background: #09090b; min-height: 100vh; display: flex; flex-direction: column; justify-content: center;">
      <h2 style="color: #f4f4f5;">${timedOut ? "Time's up" : "Practice complete"}</h2>
      <div class="big-score" style="color: #f59e0b;">${correct} out of ${total}</div>
      <div style="color: #a1a1aa; margin-top: 8px;">
        <p style="margin: 4px 0;">Attempted: ${attempted} out of ${total}</p>
        <p style="margin: 4px 0;">Correct answers: ${correct}</p>
        <p style="margin: 4px 0;">Score (of attempted): ${correct} out of ${attempted} · ${pctOfAttempted}%</p>
        <p style="margin: 4px 0;">Score (of all ${total}): ${correct} out of ${total} · ${pctOfTotal}%</p>
      </div>
      <div id="reviewWidgetContainer"></div>
      <a class="btn exam-btn-submit" href="index.html" style="text-decoration:none; display:inline-block; margin: 16px auto 0; width: fit-content;">Back to practice tests</a>
    </div>
  `;

  attachReviewWidget("reviewWidgetContainer", "practice");
}

window.addEventListener("load", async () => {
  window.siteIndex = await (await fetch("../site_index.json")).json();
  init();
});
"""

real_feel_js = base_js.replace('"practice"', '"real_feel"').replace('courseSlug || topicId', 'testNumber').replace('secondsPerQuestion', 'config.seconds_per_question')

Path("cbt-app/js/practice.js").write_text(base_js)
Path("cbt-app/js/real_feel.js").write_text(real_feel_js)

print("✅ Reverted CSS, added exam.css, restored Results page, added calculator")
