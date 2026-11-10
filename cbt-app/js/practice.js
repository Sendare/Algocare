
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
