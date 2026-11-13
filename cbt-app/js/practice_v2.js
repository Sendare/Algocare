
const params = new URLSearchParams(window.location.search);
const coursesParam = params.get("courses");
const topicId = params.get("topic");
const requestedCount = parseInt(params.get("count"), 10) || null;
const secondsPerQuestion = parseInt(params.get("spq"), 10) || 30;
const STORAGE_KEY = `algocare_practice_${window.location.search}`;

let subjects = [];
let questions = {}; 
let currentIndexes = {};
let activeSubject = "";
let answers = {}; 
let flags = [];
let endTime = null, pauseStartedAt = null, timerInterval = null, attemptId = null;
let isCatchingSkips = false;

function shuffle(arr) { let a=[...arr]; for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];} return a; }
function saveState() { sessionStorage.setItem(STORAGE_KEY, JSON.stringify({subjects,questions,currentIndexes,activeSubject,answers,flags,endTime,pauseStartedAt,attemptId})); }
function loadState() { try { const r = sessionStorage.getItem(STORAGE_KEY); return r?JSON.parse(r):null; } catch { return null; } }
function clearState() { sessionStorage.removeItem(STORAGE_KEY); }

async function init() {
  try {
    const saved = loadState();
    if (saved && saved.questions.length) {
      ({subjects,questions,currentIndexes,activeSubject,answers,flags,endTime,pauseStartedAt,attemptId} = saved);
    } else {
      if (!coursesParam) { document.getElementById("examRoot").innerHTML = `<div class="empty-state" style="color:#a1a1aa; text-align:center; padding:40px;">No courses specified. <a href="index.html">Go back</a></div>`; return; }
      
      const courseSlugs = coursesParam.split(',');
      const courseNames = {};
      
      // We need siteIndex to map slugs to names
      window.siteIndex = await (await fetch("../site_index.json")).json();
      window.siteIndex.forEach(item => { courseNames[item.course_slug] = item.course; });

      let totalQuestionsLoaded = 0;
      for (const cSlug of courseSlugs) {
        const pool = await (await fetch(`../data/course_pools/${cSlug}.json`)).json();
        const cName = courseNames[cSlug] || cSlug;
        subjects.push(cName);
        questions[cName] = shuffle(pool);
        currentIndexes[cName] = 0;
        totalQuestionsLoaded += pool.length;
      }
      
      // Limit total questions if requested
      let totalAllowed = requestedCount ? Math.min(requestedCount, totalQuestionsLoaded) : totalQuestionsLoaded;
      let distributed = 0;
      for (let i = 0; i < subjects.length; i++) {
        const sub = subjects[i];
        const take = i === subjects.length - 1 ? (totalAllowed - distributed) : Math.floor(totalAllowed / subjects.length);
        questions[sub] = questions[sub].slice(0, take);
        distributed += take;
      }

      activeSubject = subjects[0];
      endTime = Date.now() + totalAllowed * secondsPerQuestion * 1000;
      attemptId = generateAttemptId();
      saveState();
      logTestStarted(attemptId, "practice", coursesParam, totalAllowed);
    }
  } catch (e) { document.getElementById("examRoot").innerHTML = `<div class="empty-state" style="color:#a1a1aa;">Error loading test.</div>`; return; }

  if (!questions.length) return;
  markTestFinished = trackAbandonment(attemptId, "practice", topicId || courseSlug, questions.length, () => answers.filter(a=>a).length);
  reconcilePause();
  if (Date.now() >= endTime) return finishTest(true);
  startTimer(); render();
}

function isPaused() { const q = questions[activeSubject][currentIndexes[activeSubject]]; const a = answers[q.question_id]; return !!(a && a.showExplanation); }
function getAnsweredCount() { return Object.keys(answers).length; }
function getTotalQuestions() { return subjects.reduce((acc, sub) => acc + questions[sub].length, 0); }
function updateTopSubmit() { const canSubmit = getAnsweredCount() >= Math.floor(getTotalQuestions() / 2); document.getElementById("topSubmitBtn").disabled = !canSubmit; }
function showToast(msg) { const t = document.createElement("div"); t.className = "toast"; t.textContent = msg; document.body.appendChild(t); setTimeout(() => t.remove(), 3000); }
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
    return `<button class="${cls}" onclick="selectAnswer('${k}')" ${ans?'disabled':''}><div class="opt-letter">${k}</div><div>${q.options[k]}</div></button>`;
  }).join("");

  const expHtml = ans ? `
    <div class="explanation-box" style="margin-top:20px; padding:16px; background:#18181b; border-left:4px solid #f59e0b; color:#a1a1aa">
      ${ans.showExplanation ? parseExplanation(q.explanation, q.topic_id) : `<button class="btn" style="background:#27272a; color:#fff; border:none;" onclick="showExp()">Show Explanation</button>`}
    </div>
    <div class="exam-actions" style="margin-top:20px"><button class="exam-btn exam-btn-next" onclick="nextQ()">${current < questions.length - 1 ? "Next Question" : "Finish"}</button></div>
  ` : '';

  document.getElementById("examRoot").innerHTML = `
    <div class="exam-main">
      <div class="exam-q-info"><span>Question ${current + 1} of ${questions.length}</span><span>| Answered: ${answers.filter(a=>a).length}/${questions.length}</span></div>
      <div class="exam-card"><div class="exam-q-text">${q.question}</div><div class="exam-options">${opts}</div>${expHtml}</div>
      <div class="exam-actions" style="margin-top:auto"><button class="exam-btn exam-btn-prev" onclick="prevQ()" ${current===0?'disabled':''}>← Prev (P)</button>${!ans ? `<button class="exam-btn exam-btn-next" onclick="nextQ()">Next (N) →</button>` : ''}</div>
    </div>
    <div class="exam-palette">
      <div class="palette-header"><span>Question Palette</span></div>
      <div class="palette-grid">${questions.map((_,i) => {
          let c = "palette-btn";
          if (i === current) c += " current";
          else if (answers[i]) c += answers[i].isCorrect ? " answered" : " flagged";
          return `<button class="${c}" onclick="jumpTo(${i})">${i+1}</button>`;
        }).join("")}</div>
    </div>
  `;
}

function parseExplanation(text, ownId) {
  return text.replace(/\[([^\]]+)\]\(([^)#]+)#([^)]+)\)/g, (m, l, tid, hid) => {
    const entry = window.siteIndex?.find(i => i.topic_id === tid);
    return entry ? `<a href="../${entry.url}#${hid}" style="color:#f59e0b">${l}</a>` : l;
  });
}
function selectAnswer(k) { answers[current] = { selected: k, isCorrect: k === questions[current].answer, showExplanation: false }; saveState(); render(); }
function showExp() { answers[current].showExplanation = true; saveState(); render(); }
function jumpTo(i) { current = i; saveState(); render(); }
function nextQ() { if (current < questions.length - 1) { current++; saveState(); render(); } else { finishTest(false); } }
function prevQ() { if (current > 0) { current--; saveState(); render(); } }

function handleSubmitClick() {
  const answered = getAnsweredCount();
  const total = getTotalQuestions();
  if (answered < Math.floor(total / 2)) { showToast(`You must answer at least ${Math.floor(total / 2)} questions to submit.`); return; }
  
  const modal = document.createElement("div");
  modal.className = "modal-overlay";
  modal.innerHTML = `
    <div class="modal-content">
      <h2>Submit Exam?</h2>
      <p>You have answered <strong>${answered}</strong> out of <strong>${total}</strong> questions.</p>
      <div class="modal-actions">
        <button class="exam-btn exam-btn-prev" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
        <button class="exam-btn exam-btn-next" onclick="this.closest('.modal-overlay').remove(); finishTest(false)">Submit</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

function finishTest(timedOut) {
  clearInterval(timerInterval);
  const total = questions.length, attempted = answers.filter(a => a).length, correct = answers.filter(a => a && a.isCorrect).length;
  const pctOfAttempted = attempted > 0 ? Math.round((correct / attempted) * 100) : 0;
  const pctOfTotal = Math.round((correct / total) * 100);

  markTestFinished(); logTestFinished(attemptId, "practice", topicId || courseSlug, total, attempted, correct); clearState();

  document.body.style.background = "#F7F8F7";
  document.getElementById("examRoot").innerHTML = `
    <div class="score-summary" style="min-height: 100vh; display: flex; flex-direction: column; justify-content: center; padding: 40px 20px;">
      <h2 style="color: #16232E;">${timedOut ? "Time's up" : "Practice complete"}</h2>
      <div class="big-score" style="color: #16232E;">${correct} out of ${total}</div>
      <div style="color: #46545F; margin-top: 8px;">
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

window.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
  const key = e.key.toUpperCase();
  const q = questions[activeSubject][currentIndexes[activeSubject]];
  if (["A", "B", "C", "D"].includes(key)) selectAnswer(key);
  else if (key === "N") nextQ();
  else if (key === "P") prevQ();
  else if (key === "R") toggleFlag();
  else if (key === "S") handleSubmitClick();
});

window.addEventListener("load", async () => {
  window.siteIndex = await (await fetch("../site_index.json")).json();
  init();
});
