#!/usr/bin/env python3
import os
from pathlib import Path

print("🚀 Starting JAMB UI Overhaul...")

# ==========================================
# 1. REWRITE CSS (Theme Toggle + JAMB UI)
# ==========================================
css_content = """/* ===== Algocare Master CSS ===== */
:root {
  --display: 'Space Grotesk', sans-serif;
  --body: 'IBM Plex Sans', sans-serif;
  --mono: 'IBM Plex Mono', monospace;
  --radius: 8px;
}

/* --- CLINICAL THEME (Default) --- */
:root[data-theme="clinical"] {
  --paper: #F7F8F7;
  --card: #FFFFFF;
  --ink: #16232E;
  --ink-soft: #46545F;
  --grey: #8A9199;
  --grey-line: #DDE2E1;
  --scrub: #2F6F62;
  --scrub-soft: #E4EEEC;
  --amber: #C98A2E;
  --amber-soft: #FBF0DE;
  --brick: #B14A3A;
  --brick-soft: #F7E9E6;
  --shadow: 0 1px 2px rgba(22, 35, 46, 0.06), 0 4px 12px rgba(22, 35, 46, 0.05);
  
  /* Specific UI overrides */
  --header-bg: var(--card);
  --header-border: var(--grey-line);
  --opt-bg: var(--card);
  --opt-text: var(--ink);
  --opt-border: var(--grey-line);
  --opt-hover: var(--paper);
  --btn-primary-bg: var(--ink);
  --btn-primary-text: #fff;
  --nav-bg: var(--card);
  --nav-text: var(--ink-soft);
}

/* --- JAMB THEME (Dark/Amber) --- */
:root[data-theme="jamb"] {
  --paper: #09090b; /* zinc-950 */
  --card: #18181b;  /* zinc-900 */
  --ink: #f4f4f5;   /* zinc-100 */
  --ink-soft: #a1a1aa; /* zinc-400 */
  --grey: #52525b;  /* zinc-600 */
  --grey-line: #27272a; /* zinc-800 */
  --scrub: #10b981; /* emerald-500 */
  --scrub-soft: rgba(16, 185, 129, 0.1);
  --amber: #f59e0b; /* amber-500 */
  --amber-soft: rgba(245, 158, 11, 0.1);
  --brick: #ef4444; /* red-500 */
  --brick-soft: rgba(239, 68, 68, 0.1);
  --shadow: none;
  
  /* Specific UI overrides */
  --header-bg: #09090b;
  --header-border: #27272a;
  --opt-bg: #18181b;
  --opt-text: #f4f4f5;
  --opt-border: #27272a;
  --opt-hover: #27272a;
  --btn-primary-bg: var(--amber);
  --btn-primary-text: #000000;
  --nav-bg: #09090b;
  --nav-text: #a1a1aa;
}

* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: var(--paper); color: var(--ink); font-family: var(--body); font-size: 16px; transition: background 0.2s, color 0.2s; }
a { color: var(--scrub); text-decoration: none; }
a:hover { text-decoration: underline; }
h1, h2, h3 { font-family: var(--display); font-weight: 600; margin: 0 0 0.5em 0; }
button, input, select, textarea { font-family: inherit; font-size: inherit; }
:focus-visible { outline: 2px solid var(--scrub); outline-offset: 2px; }

.container { max-width: 800px; margin: 0 auto; padding: 24px 20px 64px; }

/* Topbar */
.topbar { display: flex; align-items: center; justify-content: space-between; padding: 12px 20px; border-bottom: 1px solid var(--header-border); background: var(--header-bg); transition: all 0.2s; }
.brand { font-family: var(--display); font-weight: 700; font-size: 1.15rem; color: var(--ink); display: flex; align-items: center; gap: 8px; }
.theme-toggle { background: none; border: 1px solid var(--grey-line); color: var(--ink-soft); padding: 6px 12px; border-radius: var(--radius); cursor: pointer; font-size: 0.85rem; font-weight: 600; transition: all 0.2s; }
.theme-toggle:hover { background: var(--opt-hover); color: var(--ink); }

/* Cards & Articles */
.topic-card { display: flex; align-items: center; justify-content: space-between; padding: 14px 16px; background: var(--card); border: 1px solid var(--grey-line); border-radius: var(--radius); margin-bottom: 8px; transition: all 0.2s; }
.topic-card:hover { border-color: var(--scrub); }
.topic-title { font-weight: 600; color: var(--ink); }
.topic-meta { font-family: var(--mono); font-size: 0.78rem; color: var(--grey); margin-top: 4px; }
.topic-actions a { font-size: 0.85rem; font-weight: 700; color: var(--scrub); }
.article-heading { scroll-margin-top: 24px; padding: 20px 0; border-bottom: 1px solid var(--grey-line); color: var(--ink); }
.article-heading:target { background: var(--amber-soft); margin: 0 -20px; padding: 20px; border-radius: var(--radius); }

/* Forms */
.form-row { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
.form-row label { font-family: var(--mono); font-size: 0.75rem; text-transform: uppercase; color: var(--grey); }
.form-row select, .form-row input { padding: 10px 12px; border: 1px solid var(--grey-line); border-radius: var(--radius); background: var(--card); color: var(--ink); }
.btn { padding: 10px 18px; border-radius: var(--radius); border: none; background: var(--btn-primary-bg); color: var(--btn-primary-text); font-weight: 700; cursor: pointer; display: inline-block; text-align: center; transition: opacity 0.2s; }
.btn:hover { opacity: 0.9; text-decoration: none; }
.btn.secondary { background: var(--card); color: var(--ink); border: 1px solid var(--grey-line); }

/* ===== JAMB EXAM LAYOUT ===== */
.exam-layout { display: flex; flex-direction: column; height: 100vh; overflow: hidden; background: var(--paper); }
.exam-header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; background: #09090b; border-bottom: 1px solid #27272a; color: #fff; }
.exam-header-left { display: flex; flex-direction: column; }
.exam-header-title { font-family: var(--display); font-size: 1.2rem; font-weight: 700; color: var(--amber); }
.exam-header-right { display: flex; align-items: center; gap: 12px; }
.exam-timer { background: #18181b; border: 1px solid #27272a; padding: 6px 12px; border-radius: var(--radius); font-family: var(--mono); font-weight: 700; font-size: 1.1rem; color: #fff; }
.exam-btn-submit { background: var(--amber); color: #000; padding: 8px 16px; border-radius: var(--radius); font-weight: 700; border: none; cursor: pointer; }

.exam-tabs { display: flex; overflow-x: auto; background: #09090b; border-bottom: 1px solid #27272a; padding: 0 16px; }
.exam-tab { padding: 12px 20px; color: #a1a1aa; font-weight: 600; font-size: 0.9rem; border-bottom: 2px solid transparent; cursor: pointer; white-space: nowrap; background: none; border-top: none; border-left: none; border-right: none; }
.exam-tab.active { color: #fff; border-bottom-color: var(--amber); background: #18181b; }

.exam-main { display: flex; flex-direction: column; flex: 1; overflow-y: auto; padding: 16px; max-width: 1000px; margin: 0 auto; width: 100%; }
.exam-q-info { display: flex; justify-content: space-between; align-items: center; background: #18181b; border: 1px solid #27272a; padding: 10px 16px; border-radius: var(--radius); color: #a1a1aa; font-size: 0.85rem; margin-bottom: 16px; font-weight: 600; }
.exam-flag-btn { background: none; border: none; color: #a1a1aa; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; }
.exam-flag-btn.flagged { color: var(--amber); }

.exam-card { background: #18181b; border: 1px solid #27272a; border-radius: var(--radius); padding: 24px; margin-bottom: 20px; }
.exam-q-text { font-size: 1.15rem; font-weight: 500; color: #fff; margin-bottom: 24px; line-height: 1.6; }

.exam-options { display: flex; flex-direction: column; gap: 12px; }
.exam-opt { display: flex; align-items: center; gap: 16px; padding: 16px; background: #09090b; border: 2px solid #27272a; border-radius: var(--radius); cursor: pointer; text-align: left; transition: all 0.2s; color: #f4f4f5; }
.exam-opt:hover { border-color: rgba(245, 158, 11, 0.5); }
.exam-opt.selected { border-color: var(--amber); background: rgba(245, 158, 11, 0.1); }
.exam-opt.selected .opt-letter { background: var(--amber); color: #000; }
.exam-opt.correct { border-color: var(--scrub); background: rgba(16, 185, 129, 0.1); }
.exam-opt.correct .opt-letter { background: var(--scrub); color: #fff; }
.exam-opt.incorrect { border-color: var(--brick); background: rgba(239, 68, 68, 0.1); }
.exam-opt.incorrect .opt-letter { background: var(--brick); color: #fff; }
.opt-letter { width: 32px; height: 32px; border-radius: 50%; background: #27272a; color: #a1a1aa; display: flex; align-items: center; justify-content: center; font-weight: 700; flex-shrink: 0; }

.exam-actions { display: flex; gap: 16px; margin-top: auto; }
.exam-btn { flex: 1; padding: 14px; border-radius: var(--radius); font-weight: 700; font-size: 1rem; border: none; cursor: pointer; display: flex; justify-content: center; align-items: center; gap: 8px; }
.exam-btn-prev { background: #18181b; color: #d4d4d8; border: 2px solid #27272a; }
.exam-btn-next { background: var(--amber); color: #000; }

/* Question Palette */
.exam-palette { background: #09090b; border-top: 4px solid #27272a; padding: 16px; }
.palette-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; font-weight: 700; color: #fff; font-size: 0.9rem; }
.palette-stats { display: flex; gap: 8px; font-size: 0.75rem; }
.stat-a { color: #10b981; background: rgba(16,185,129,0.1); padding: 2px 8px; border-radius: 4px; border: 1px solid #27272a; }
.stat-f { color: #f59e0b; background: rgba(245,158,11,0.1); padding: 2px 8px; border-radius: 4px; border: 1px solid #27272a; }
.palette-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(36px, 1fr)); gap: 8px; }
.palette-btn { height: 36px; border-radius: 6px; border: 1px solid #27272a; background: #18181b; color: #a1a1aa; font-weight: 700; cursor: pointer; display: flex; align-items: center; justify-content: center; font-size: 0.85rem; }
.palette-btn.answered { background: #10b981; color: #fff; border-color: #059669; }
.palette-btn.flagged { background: #f59e0b; color: #000; border-color: #d97706; }
.palette-btn.current { outline: 2px solid #3b82f6; outline-offset: 2px; }

/* Calculator Modal */
.calc-modal { position: fixed; bottom: 20px; right: 20px; width: 280px; background: #18181b; border: 1px solid #27272a; border-radius: 12px; box-shadow: 0 10px 25px rgba(0,0,0,0.5); z-index: 100; display: none; flex-direction: column; }
.calc-modal.open { display: flex; }
.calc-header { display: flex; justify-content: space-between; padding: 10px 16px; border-bottom: 1px solid #27272a; color: #fff; font-weight: 700; }
.calc-close { background: none; border: none; color: #ef4444; cursor: pointer; font-weight: bold; }
.calc-display { padding: 16px; font-family: var(--mono); font-size: 1.5rem; text-align: right; color: #fff; background: #09090b; margin: 10px; border-radius: 6px; border: 1px solid #27272a; overflow-x: auto; }
.calc-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 6px; padding: 10px; }
.calc-btn { padding: 12px; border-radius: 6px; border: none; background: #27272a; color: #fff; font-weight: 700; cursor: pointer; font-size: 1rem; }
.calc-btn.op { background: rgba(245, 158, 11, 0.2); color: var(--amber); }
.calc-btn.eq { background: var(--amber); color: #000; grid-column: span 2; }
"""
Path("assets/style.css").write_text(css_content)
print("✅ Overwrote assets/style.css with dual-theme + JAMB layout")

# ==========================================
# 2. PATCH build_pages.py (Inject Theme Toggle)
# ==========================================
bp = Path("build_pages.py")
src = bp.read_text()

if "theme-toggle" not in src:
    # Inject Theme JS into <head> to prevent flash of wrong theme
    head_script = """
<script>
  (function() {
    const t = localStorage.getItem('algocare_theme') || 'clinical';
    document.documentElement.setAttribute('data-theme', t);
  })();
</script>"""
    src = src.replace("<head>", "<head>" + head_script, 1)

    # Add Toggle Button to topbar
    toggle_btn = """
    <button class="theme-toggle" onclick="
      const cur = document.documentElement.getAttribute('data-theme');
      const next = cur === 'clinical' ? 'jamb' : 'clinical';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('algocare_theme', next);
    ">Switch Theme</button>"""
    
    # Find the end of the topbar div
    src = src.replace('</div>\n</div>\n<div class="container">', toggle_btn + '</div>\n</div>\n<div class="container">', 1)
    
    bp.write_text(src)
    print("✅ Patched build_pages.py with theme toggle")
else:
    print("ℹ️ build_pages.py already has theme toggle")

# ==========================================
# 3. PATCH cbt-app JS & HTML
# ==========================================
# We will create a shared util.js for the calculator and theme
util_js = """
function toggleCalculator() {
  const modal = document.getElementById('calcModal');
  if (modal) modal.classList.toggle('open');
}

let calcExpr = '';
function calcInput(val) {
  const display = document.getElementById('calcDisplay');
  if (val === 'C') { calcExpr = ''; }
  else if (val === '=') {
    try { calcExpr = String(eval(calcExpr || '0')); } catch { calcExpr = 'Error'; }
  } else {
    if (calcExpr === 'Error') calcExpr = '';
    calcExpr += val;
  }
  display.textContent = calcExpr || '0';
}
"""
Path("cbt-app/js/util.js").write_text(util_js)

calc_html = """
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
"""

# Update index.html, practice.html, real_feel.html to include calculator and util.js
for f in ["index.html", "practice.html", "real_feel.html"]:
    p = Path(f"cbt-app/{f}")
    if p.exists():
        html = p.read_text()
        if "calcModal" not in html:
            html = html.replace("</body>", calc_html + "\n<script src='js/util.js'></script>\n</body>")
            p.write_text(html)

print("✅ Added Calculator to CBT HTML files")

# ==========================================
# 4. REWRITE practice.js and real_feel.js
# ==========================================
# We need to match the JAMB structure exactly
practice_js = """
const params = new URLSearchParams(window.location.search);
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
      else { document.body.innerHTML = `<div class="empty-state">No course or topic specified. <a href="index.html">Go back</a></div>`; return; }
      
      const count = requestedCount ? Math.min(requestedCount, pool.length) : pool.length;
      questions = shuffle(pool).slice(0, count);
      answers = new Array(questions.length).fill(null);
      endTime = Date.now() + questions.length * secondsPerQuestion * 1000;
      attemptId = generateAttemptId();
      saveState();
      logTestStarted(attemptId, "practice", topicId || courseSlug, questions.length);
    }
  } catch (e) { document.body.innerHTML = `<div class="empty-state">Error loading test.</div>`; return; }

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
    <div class="explanation-box" style="margin-top:20px; padding:16px; background:var(--paper); border-left:4px solid var(--amber); color:var(--ink-soft)">
      ${ans.showExplanation ? parseExplanation(q.explanation, q.topic_id) : `<button class="btn" onclick="showExp()">Show Explanation</button>`}
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
  return text.replace(/\[([^\]]+)\]\(([^)#]+)#([^)]+)\)/g, (m, l, tid, hid) => {
    const entry = window.siteIndex?.find(i => i.topic_id === tid);
    return entry ? `<a href="../${entry.url}#${hid}" style="color:var(--amber)">${l}</a>` : l;
  });
}
function selectAnswer(k) { answers[current] = { selected: k, isCorrect: k === questions[current].answer, showExplanation: false }; saveState(); render(); }
function showExp() { answers[current].showExplanation = true; saveState(); render(); }
function jumpTo(i) { current = i; saveState(); render(); }
function nextQ() { if (current < questions.length - 1) { current++; saveState(); render(); } else { finishTest(false); } }
function prevQ() { if (current > 0) { current--; saveState(); render(); } }

function finishTest(to) {
  clearInterval(timerInterval);
  const tot = questions.length, att = answers.filter(a=>a).length, cor = answers.filter(a=>a&&a.isCorrect).length;
  markTestFinished(); logTestFinished(attemptId, "practice", topicId||courseSlug, tot, att, cor); clearState();
  document.getElementById("examRoot").innerHTML = `
    <div class="score-summary" style="text-align:center; padding:40px 20px;">
      <h2 style="color:var(--amber); font-size:2rem">${to ? "Time's up" : "Practice Complete"}</h2>
      <div style="font-size:3rem; font-weight:800; color:var(--ink); margin:20px 0">${cor} / ${tot}</div>
      <p style="color:var(--ink-soft)">Attempted: ${att} · Correct: ${cor} · Score: ${att>0?Math.round((cor/att)*100):0}%</p>
      <div id="reviewWidgetContainer"></div>
      <a class="btn" href="index.html" style="margin-top:24px">Back to Practice</a>
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

# Update practice.html and real_feel.html to use the new JAMB layout
layout_html = """<!DOCTYPE html>
<html lang="en" data-theme="jamb">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Algocare — Exam</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/style.css">
<style>
  .exam-layout { height: 100vh; display: flex; flex-direction: column; }
  .exam-main { flex: 1; overflow-y: auto; padding: 16px; display: flex; flex-direction: column; max-width: 800px; margin: 0 auto; width: 100%; }
  .exam-palette { background: var(--card); border-top: 1px solid var(--grey-line); padding: 16px; }
  .palette-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(36px, 1fr)); gap: 8px; margin-top: 10px; }
  .palette-btn { height: 36px; border-radius: 6px; border: 1px solid var(--grey-line); background: var(--paper); color: var(--ink-soft); font-weight: 700; cursor: pointer; }
  .palette-btn.current { outline: 2px solid var(--scrub); outline-offset: 2px; }
  .palette-btn.answered { background: var(--scrub); color: #fff; border-color: var(--scrub); }
  .palette-btn.flagged { background: var(--amber); color: #000; border-color: var(--amber); }
</style>
</head>
<body style="margin:0; background:var(--paper);">
<div class="exam-layout">
  <header class="exam-header">
    <div class="exam-header-left">
      <span class="exam-header-title">Algocare CBT</span>
      <span style="font-size:0.75rem; color:#a1a1aa">Practice Mode</span>
    </div>
    <div class="exam-header-right">
      <button class="exam-btn-submit" onclick="toggleCalculator()" style="background:#18181b; border:1px solid #27272a; color:#fff">Calc</button>
      <div class="exam-timer" id="examTimer">--:--</div>
      <button class="exam-btn-submit" onclick="finishTest(true)">Submit</button>
    </div>
  </header>
  <div id="examRoot" style="display:flex; flex-direction:column; flex:1; overflow:hidden;"></div>
</div>

<script src="../assets/analytics.js"></script>
<script src="js/util.js"></script>
<script src="js/practice.js"></script>
</body>
</html>"""
Path("cbt-app/practice.html").write_text(layout_html)
Path("cbt-app/real_feel.html").write_text(layout_html.replace("practice.js", "real_feel.js").replace("Practice Mode", "Real-Feel Exam"))

# Copy practice.js logic to real_feel.js with minor tweaks
real_feel_js = practice_js.replace('"practice"', '"real_feel"').replace('courseSlug || topicId', 'testNumber')
Path("cbt-app/js/real_feel.js").write_text(real_feel_js)

print("✅ Overwrote cbt-app JS and HTML with JAMB Exam UI")
print("🎉 All patches applied successfully. Ready for rebuild.")
