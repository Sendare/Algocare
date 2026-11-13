const params = new URLSearchParams(window.location.search);
const coursesParam = params.get("courses");
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
function saveState() { sessionStorage.setItem(STORAGE_KEY, JSON.stringify({subjects,questions,currentIndexes,activeSubject,answers,flags,endTime,pauseStartedAt,attemptId,isCatchingSkips})); }
function loadState() { try { const r = sessionStorage.getItem(STORAGE_KEY); return r?JSON.parse(r):null; } catch { return null; } }
function clearState() { sessionStorage.removeItem(STORAGE_KEY); }

async function init() {
  try {
    const saved = loadState();
    if (saved && saved.subjects && saved.subjects.length) {
      ({subjects,questions,currentIndexes,activeSubject,answers,flags,endTime,pauseStartedAt,attemptId,isCatchingSkips} = saved);
    } else {
      if (!coursesParam) { document.getElementById("examRoot").innerHTML = `<div class="empty-state" style="color:#a1a1aa; text-align:center; padding:40px;">No courses specified. <a href="index.html">Go back</a></div>`; return; }
      
      const courseSlugs = coursesParam.split(',');
      const courseNames = {};
      
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

  if (!subjects.length) return;
  markTestFinished = trackAbandonment(attemptId, "practice", coursesParam, getTotalQuestions(), () => getAnsweredCount());
  reconcilePause();
  if (Date.now() >= endTime) return finishTest(true);
  startTimer(); render();
}

function isPaused() { const q = questions[activeSubject][currentIndexes[activeSubject]]; const a = answers[q.question_id]; return !!(a && a.showExplanation); }
function getAnsweredCount() { return Object.keys(answers).length; }
function getTotalQuestions() { return subjects.reduce((acc, sub) => acc + questions[sub].length, 0); }
function showToast(msg) { 
  const t = document.createElement("div"); 
  t.className = "toast"; 
  t.textContent = msg; 
  document.body.appendChild(t); 
  setTimeout(() => t.remove(), 3000); 
}

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
  const qList = questions[activeSubject];
  const current = currentIndexes[activeSubject];
  const q = qList[current];
  const ans = answers[q.question_id];
  const isFlagged = flags.includes(q.question_id);

  const tabsHtml = subjects.length > 1 ? `<div class="exam-tabs">${subjects.map(s => `<button class="exam-tab ${s === activeSubject ? 'active' : ''}" onclick="switchTab('${s}')">${s}</button>`).join("")}</div>` : '';

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
  ` : '';

  document.getElementById("examRoot").innerHTML = `
    ${tabsHtml}
    <div class="exam-main">
      <div class="exam-q-info">
        <span>Question ${current + 1} of ${qList.length}</span>
        <span>| Answered: ${getAnsweredCount()}/${getTotalQuestions()}</span>
        <button class="exam-flag-btn ${isFlagged ? 'flagged' : ''}" onclick="toggleFlag()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path><line x1="4" y1="22" x2="4" y2="15"></line></svg>
          ${isFlagged ? 'Flagged' : 'Flag (R)'}
        </button>
      </div>
      <div class="exam-card"><div class="exam-q-text">${q.question}</div><div class="exam-options">${opts}</div>${expHtml}</div>
      <div class="exam-actions" style="margin-top:auto">
        <button class="exam-btn exam-btn-prev" onclick="prevQ()" ${current===0 && activeSubject===subjects[0]?'disabled':''}>← Prev (P)</button>
        <button class="exam-btn exam-btn-next" onclick="nextQ()">Next (N) →</button>
      </div>
    </div>
    <div class="exam-palette">
      <div class="palette-header"><span>Question Palette</span></div>
      <div class="palette-grid">${qList.map((item, i) => {
          let c = "palette-btn";
          if (i === current) c += " current";
          else if (answers[item.question_id]) c += " answered";
          if (flags.includes(item.question_id)) c += " flagged";
          return `<button class="${c}" onclick="jumpTo(${i})">${i+1}</button>`;
        }).join("")}</div>
    </div>
  `;
}

function switchTab(sub) { activeSubject = sub; isCatchingSkips = false; saveState(); render(); }
function toggleFlag() { const q = questions[activeSubject][currentIndexes[activeSubject]]; if (flags.includes(q.question_id)) flags = flags.filter(id => id !== q.question_id); else flags.push(q.question_id); saveState(); render(); }
function jumpTo(i) { currentIndexes[activeSubject] = i; isCatchingSkips = false; saveState(); render(); }

function nextQ() {
  const currentIndex = currentIndexes[activeSubject];
  const currentQuestions = questions[activeSubject];
  const isAtAbsoluteEnd = activeSubject === subjects[subjects.length - 1] && currentIndex === currentQuestions.length - 1;

  if (isCatchingSkips || isAtAbsoluteEnd) {
    let targetSub = '';
    let targetIndex = -1;

    for (let s = subjects.indexOf(activeSubject); s < subjects.length; s++) {
      const sub = subjects[s];
      const subQs = questions[sub] || [];
      for (let i = 0; i < subQs.length; i++) {
        if (s === subjects.indexOf(activeSubject) && i <= currentIndex) continue;
        if (!answers[subQs[i].question_id]) { targetSub = sub; targetIndex = i; break; }
      }
      if (targetSub) break;
    }

    if (!targetSub) {
      for (let s = 0; s <= subjects.indexOf(activeSubject); s++) {
        const sub = subjects[s];
        const subQs = questions[sub] || [];
        for (let i = 0; i < subQs.length; i++) {
          if (s === subjects.indexOf(activeSubject) && i >= currentIndex) break;
          if (!answers[subQs[i].question_id]) { targetSub = sub; targetIndex = i; break; }
        }
        if (targetSub) break;
      }
    }

    if (targetSub !== '') {
      switchTab(targetSub);
      jumpTo(targetIndex);
      isCatchingSkips = true;
      showToast("Jumped to next unanswered question");
    } else {
      handleSubmitClick();
      isCatchingSkips = false;
    }
    return;
  }

  if (currentIndex < currentQuestions.length - 1) {
    jumpTo(currentIndex + 1);
  } else {
    const currentSubIndex = subjects.indexOf(activeSubject);
    if (currentSubIndex < subjects.length - 1) {
      switchTab(subjects[currentSubIndex + 1]);
      jumpTo(0);
    }
  }
}

function prevQ() {
  const current = currentIndexes[activeSubject];
  if (current > 0) { jumpTo(current - 1); }
  else {
    const currentSubIndex = subjects.indexOf(activeSubject);
    if (currentSubIndex > 0) {
      const prevSub = subjects[currentSubIndex - 1];
      switchTab(prevSub); jumpTo(questions[prevSub].length - 1);
    }
  }
  isCatchingSkips = false;
}

function selectAnswer(k) { 
  const q = questions[activeSubject][currentIndexes[activeSubject]];
  answers[q.question_id] = { selected: k, isCorrect: k === q.answer, showExplanation: false }; 
  isCatchingSkips = false; 
  saveState(); render(); 
}

function showExp() { 
  const q = questions[activeSubject][currentIndexes[activeSubject]];
  answers[q.question_id].showExplanation = true; 
  saveState(); render(); 
}

function parseExplanation(text, ownId) {
  return text.replace(/\[([^\]]+)\]\(([^)#]+)#([^)]+)\)/g, (m, l, tid, hid) => {
    const entry = window.siteIndex?.find(i => i.topic_id === tid);
    return entry ? `<a href="../${entry.url}#${hid}" style="color:var(--amber)">${l}</a>` : l;
  });
}

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
  const tot = getTotalQuestions(), att = getAnsweredCount();
  let cor = 0;
  subjects.forEach(sub => {
    questions[sub].forEach(q => {
      if (answers[q.question_id] && answers[q.question_id].isCorrect) cor++;
    });
  });

  markTestFinished(); logTestFinished(attemptId, "practice", coursesParam, tot, att, cor); clearState();

  document.body.style.background = "#F7F8F7";
  document.getElementById("examRoot").innerHTML = `
    <div class="score-summary" style="min-height: 100vh; display: flex; flex-direction: column; justify-content: center; padding: 40px 20px;">
      <h2 style="color: #16232E;">${timedOut ? "Time's up" : "Practice complete"}</h2>
      <div class="big-score" style="color: #16232E;">${cor} out of ${tot}</div>
      <div style="color: #46545F; margin-top: 8px;">
        <p style="margin: 4px 0;">Attempted: ${att} out of ${tot}</p>
        <p style="margin: 4px 0;">Correct answers: ${cor}</p>
        <p style="margin: 4px 0;">Score (of attempted): ${cor} out of ${att} · ${att>0?Math.round((cor/att)*100):0}%</p>
        <p style="margin: 4px 0;">Score (of all ${tot}): ${cor} out of ${tot} · ${Math.round((cor/tot)*100)}%</p>
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

window.addEventListener("load", async () => { init(); });
