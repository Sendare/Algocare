// ===== Exam Engine =====
const params = new URLSearchParams(window.location.search);
let mode = params.get("mode") || "practice";
const prog = params.get("prog") || "nursing";
const testNum = params.get("test");
const coursesParam = params.get("courses");
const topicId = params.get("topic");
const requestedCount = parseInt(params.get("count"), 10) || null;
const secondsPerQuestion = parseInt(params.get("spq"), 10) || 30;

let subjects = [];
let questions = {}; 
let currentIndexes = {};
let activeSubject = "";
let answers = {}; 
let flags = [];
let endTime = null, timerInterval = null, attemptId = null;
let isCatchingSkips = false;
let isFinished = false;


function saveState() {
  const state = { subjects, questions, currentIndexes, activeSubject, answers, flags, endTime, attemptId, isCatchingSkips, isFinished };
  sessionStorage.setItem("algocare_exam_state", JSON.stringify(state));
}
function loadState() {
  try {
    const s = sessionStorage.getItem("algocare_exam_state");
    if (!s) return null;
    const state = JSON.parse(s);
    if (state.isFinished) return null; // Don't load a finished exam
    return state;
  } catch { return null; }
}
function clearState() {
  sessionStorage.removeItem("algocare_exam_state");
}

function shuffle(arr) { let a=[...arr]; for(let i=a.length-1;i>0;i--){const j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]];} return a; }

// --- Initialization ---
async function init() {
  const resultsStr = sessionStorage.getItem("algocare_results_state");
  if (resultsStr) {
    const r = JSON.parse(resultsStr);
    // Only restore if the URL matches, preventing old results from hijacking new tests
    if (r.search === window.location.search) {
      subjects = r.subjects;
      questions = r.questions;
      answers = r.answers;
      mode = r.mode;
      isFinished = false;
      finishExam(r.timedOut, true); // Pass true to prevent double-logging
      return;
    } else {
      sessionStorage.removeItem("algocare_results_state");
    }
  }

  const saved = loadState();
  if (saved) {
    subjects = saved.subjects;
    questions = saved.questions;
    currentIndexes = saved.currentIndexes;
    activeSubject = saved.activeSubject;
    answers = saved.answers;
    flags = saved.flags;
    endTime = saved.endTime;
    attemptId = saved.attemptId;
    isCatchingSkips = saved.isCatchingSkips;
    startTimer(); render(); return;
  }

  try {
    // Load site index in the background without blocking the exam
    try { window.siteIndex = await (await fetch(`../site_index.json`)).json(); } catch(e) { console.warn(e); }

    if (mode === "practice") {
      if (topicId) {
        const pool = await (await fetch(`../data/questions/${topicId}.json`)).json();
        subjects = ["Topic Practice"];
        questions["Topic Practice"] = shuffle(pool).slice(0, 20);
        currentIndexes["Topic Practice"] = 0;
        activeSubject = "Topic Practice";
        endTime = Date.now() + questions["Topic Practice"].length * secondsPerQuestion * 1000;
      } else if (coursesParam) {
        const slugs = coursesParam.split(',');
        const courseNames = {};
        if (window.siteIndex) {
          window.siteIndex.forEach(item => courseNames[item.course_slug] = item.course);
        }

        let totalLoaded = 0;
        for (const slug of slugs) {
          const pool = await (await fetch(`../data/course_pools/${slug}.json`)).json();
          const name = courseNames[slug] || slug;
          subjects.push(name);
          questions[name] = shuffle(pool);
          currentIndexes[name] = 0;
          totalLoaded += pool.length;
        }
        
        let totalAllowed = requestedCount ? Math.min(requestedCount, totalLoaded) : totalLoaded;
        let distributed = 0;
        for (let i = 0; i < subjects.length; i++) {
          const sub = subjects[i];
          const take = i === subjects.length - 1 ? (totalAllowed - distributed) : Math.floor(totalAllowed / subjects.length);
          questions[sub] = questions[sub].slice(0, take);
          distributed += take;
        }
        activeSubject = subjects[0];
        endTime = Date.now() + totalAllowed * secondsPerQuestion * 1000;
      }
    } else if (mode === "real_feel") {
      const res = await fetch(`../data/real_feel_tests/test_${testNum}.json`);
      const pool = await res.json();
      subjects = ["Real-Feel Exam"];
      questions["Real-Feel Exam"] = shuffle(pool);
      currentIndexes["Real-Feel Exam"] = 0;
      activeSubject = "Real-Feel Exam";
      endTime = Date.now() + questions["Real-Feel Exam"].length * 30 * 1000;
    }
  } catch (e) {
    document.getElementById("examRoot").innerHTML = `<div class="empty-state" style="text-align:center; padding:40px;">Error loading exam. <a href="index.html">Go back</a></div>`;
    return;
  }

  if (!subjects.length) return;
  if (!attemptId) attemptId = generateAttemptId();
  logTestStarted(attemptId, mode, coursesParam || topicId || testNum, getTotalQuestions());
  startTimer(); render();
}

// --- Timer ---
function startTimer() {
  updateTimerDisplay();
  timerInterval = setInterval(() => {
    if (isFinished) return;
    if (Date.now() >= endTime) { clearInterval(timerInterval); finishExam(true); return; }
    updateTimerDisplay();
  }, 1000);
}
function updateTimerDisplay() {
  const rem = Math.max(0, Math.round((endTime - Date.now()) / 1000));
  const h = Math.floor(rem / 3600), m = Math.floor((rem % 3600) / 60).toString().padStart(2, "0"), s = (rem % 60).toString().padStart(2, "0");
  document.getElementById("examTimer").textContent = h > 0 ? `${h}:${m}:${s}` : `${m}:${s}`;
}

// --- Helpers ---
function getAnsweredCount() { return Object.keys(answers).length; }
function getTotalQuestions() { return subjects.reduce((acc, sub) => acc + questions[sub].length, 0); }
function showToast(msg) { 
  const t = document.createElement("div"); t.className = "toast"; t.textContent = msg; 
  document.body.appendChild(t); setTimeout(() => t.remove(), 3000); 
}

// --- Render Loop ---
function render() {
  if (isFinished) return;
  const qList = questions[activeSubject];
  const current = currentIndexes[activeSubject];
  const q = qList[current];
  const ans = answers[q.question_id];
  const isFlagged = flags.includes(q.question_id);

  const tabsHtml = subjects.length > 1 ? `<div class="exam-tabs">${subjects.map(s => `<button class="exam-tab ${s === activeSubject ? 'active' : ''}" data-subject="${esc(s)}">${s}</button>`).join("")}</div>` : '';

  const opts = Object.keys(q.options).map(k => {
    let cls = "exam-opt";
    if (ans) {
      if (k === ans.selected) cls += " selected";
      if (mode === "practice" && k === q.answer) cls += " correct";
      if (mode === "practice" && k === ans.selected && k !== q.answer) cls += " incorrect";
    }
    return `<button class="${cls}" onclick="selectAnswer('${k}')" ${ans && mode==='practice'?'disabled':''}><div class="opt-letter">${k}</div><div>${esc(q.options[k])}</div></button>`;
  }).join("");

  let expHtml = "";
  if (mode === "practice" && ans) {
    expHtml = `
      <div class="expl-box" style="margin-top:20px;">
        ${ans.showExplanation ? parseExplanation(q.explanation, q.topic_id) : `<button class="btn" style="background:var(--paper); color:var(--ink); border:1px solid var(--grey-line);" onclick="showExp()">Show Explanation</button>`}
      </div>
    `;
  }

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
      <div class="exam-card">
        <div class="exam-q-text">${esc(q.question)}</div>
        <div class="exam-options">${opts}</div>
        ${expHtml}
      </div>
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
  
  // Attach Tab Listeners safely
  document.querySelectorAll('.exam-tab').forEach(btn => {
    btn.addEventListener('click', () => switchTab(btn.dataset.subject));
  });
}

// --- Actions ---
function switchTab(sub) { saveState(); activeSubject = sub; isCatchingSkips = false; render(); }
function toggleFlag() { const q = questions[activeSubject][currentIndexes[activeSubject]]; if (flags.includes(q.question_id)) flags = flags.filter(id => id !== q.question_id); else flags.push(q.question_id); saveState(); render(); }
function jumpTo(i) { saveState(); currentIndexes[activeSubject] = i; isCatchingSkips = false; render(); }

function selectAnswer(k) { saveState(); 
  const q = questions[activeSubject][currentIndexes[activeSubject]];
  answers[q.question_id] = { selected: k, isCorrect: k === q.answer, showExplanation: false }; 
  if (mode === "practice") isCatchingSkips = false; 
  render(); 
}
function showExp() { 
  const q = questions[activeSubject][currentIndexes[activeSubject]];
  answers[q.question_id].showExplanation = true; 
  render(); 
}

function nextQ() {
  const currentIndex = currentIndexes[activeSubject];
  const currentQuestions = questions[activeSubject];
  const isAtAbsoluteEnd = activeSubject === subjects[subjects.length - 1] && currentIndex === currentQuestions.length - 1;

  if (isCatchingSkips || isAtAbsoluteEnd) {
    let targetSub = '', targetIndex = -1;
    for (let s = subjects.indexOf(activeSubject); s < subjects.length; s++) {
      const sub = subjects[s]; const subQs = questions[sub] || [];
      for (let i = 0; i < subQs.length; i++) {
        if (s === subjects.indexOf(activeSubject) && i <= currentIndex) continue;
        if (!answers[subQs[i].question_id]) { targetSub = sub; targetIndex = i; break; }
      }
      if (targetSub) break;
    }
    if (!targetSub) {
      for (let s = 0; s <= subjects.indexOf(activeSubject); s++) {
        const sub = subjects[s]; const subQs = questions[sub] || [];
        for (let i = 0; i < subQs.length; i++) {
          if (s === subjects.indexOf(activeSubject) && i >= currentIndex) break;
          if (!answers[subQs[i].question_id]) { targetSub = sub; targetIndex = i; break; }
        }
        if (targetSub) break;
      }
    }
    if (targetSub !== '') {
      switchTab(targetSub); jumpTo(targetIndex); isCatchingSkips = true; showToast("Jumped to next unanswered question");
    } else { handleSubmitClick(); isCatchingSkips = false; }
    return;
  }

  if (currentIndex < currentQuestions.length - 1) { jumpTo(currentIndex + 1); }
  else {
    const currentSubIndex = subjects.indexOf(activeSubject);
    if (currentSubIndex < subjects.length - 1) { switchTab(subjects[currentSubIndex + 1]); jumpTo(0); }
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

// --- Submission ---
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
        <button class="exam-btn exam-btn-next" onclick="this.closest('.modal-overlay').remove(); finishExam(false)">Submit</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

// --- Explanation Parser ---
function parseExplanation(text, ownId) {
  if (!text) return "";
  // Regex allows for an optional space between ] and (
  return text.replace(/\[([^\]]+)\]\s*\(([^)#]+)#([^)]+)\)/g, function(match, label, topicId, headingId) {
    if (!window.siteIndex) return label;
    const entry = window.siteIndex.find(i => i.topic_id === topicId);
    if (entry) {
      return `<a href="../${entry.url}#${headingId}" style="color:var(--scrub); font-weight:700;">${label}</a>`;
    }
    return label;
  });
}

// --- Results & Feedback ---
function finishExam(timedOut, fromRestore = false) {
  if (isFinished) return;
  clearState();
  sessionStorage.removeItem('algocare_exam_state');
  isFinished = true;
  clearInterval(timerInterval);
  
  if (!fromRestore) {
    const totalCorr = subjects.reduce((acc, sub) => acc + questions[sub].filter(q => answers[q.question_id] && answers[q.question_id].isCorrect).length, 0);
    logTestFinished(attemptId, mode, coursesParam || topicId || testNum, getTotalQuestions(), getAnsweredCount(), totalCorr);
  }
  
  // Hide the exam header
  const header = document.querySelector('.exam-header');
  if (header) header.style.display = 'none';

  const total = getTotalQuestions(), attempted = getAnsweredCount();
  let totalCorrect = 0;
  const subjectResults = [];

  subjects.forEach(sub => {
    let correct = 0;
    questions[sub].forEach(q => {
      if (answers[q.question_id] && answers[q.question_id].isCorrect) correct++;
    });
    totalCorrect += correct;
    subjectResults.push({ sub, correct, total: questions[sub].length });
  });

  const subjectHtml = mode === "practice" ? `
    <h3 class="section-title">Subject Breakdown</h3>
    <div class="subject-grid">${subjectResults.map(r => `
      <div class="subject-card">
        <div class="subject-name">${r.sub.replace(/-/g, ' ')}</div>
        <div class="subject-score-row">
          <span class="subject-score-bold" style="font-size: 1.1rem;">${r.correct} <span style="font-size: 0.8rem; color: var(--ink-soft);">/ ${r.total}</span></span>
        </div>
      </div>
    `).join("")}</div>
  ` : "";

  let reviewHtml = "";
  if (mode === "practice") {
    subjects.forEach(sub => {
      const wrongQs = questions[sub].filter(q => answers[q.question_id] && !answers[q.question_id].isCorrect);
      if (wrongQs.length === 0) return;
      reviewHtml += `<div style="margin-bottom: 24px;"><h3 style="color:var(--ink); text-transform:capitalize; border-bottom:1px solid var(--grey-line); padding-bottom:4px; margin-bottom:12px; font-size:1rem;">${sub.replace(/-/g, ' ')}</h3>`;
      wrongQs.forEach(q => {
        const uAns = answers[q.question_id].selected;
        const cAns = q.answer;
        const entry = window.siteIndex?.find(i => i.topic_id === q.topic_id);
        const learnMoreBtn = entry ? `<a href="../${entry.url}" class="learn-more-btn">Study more on this topic →</a>` : '';

        reviewHtml += `
          <div class="wrong-q-card">
            <div class="wrong-q-text">${q.question}</div>
            <div class="ans-line"><span class="ans-yours">Your answer:</span> ${q.options[uAns]}</div>
            <div class="ans-line"><span class="ans-correct">Correct answer:</span> ${q.options[cAns]}</div>
            ${q.explanation ? `<div class="expl-box"><strong style="color:var(--ink);">Explanation:</strong> ${parseExplanation(q.explanation, q.topic_id)}</div>` : ''}
            ${learnMoreBtn}
          </div>
        `;
      });
      reviewHtml += `</div>`;
    });
    if (!reviewHtml) reviewHtml = `<p style="text-align:center; color:var(--ink-soft); font-size:0.9rem;">You got everything right! No corrections to show.</p>`;
  } else {
    reviewHtml = `<p style="text-align:center; color:var(--ink-soft); font-size:0.9rem;">Answers and explanations are not shown for real-feel exams.</p>`;
  }

  sessionStorage.setItem("algocare_results_state", JSON.stringify({ subjects, questions, answers, mode, timedOut, search: window.location.search }));
  
  document.getElementById("examRoot").innerHTML = `
    <div class="results-page" style="overflow-y:auto; height:100dvh;">
      <header class="results-header">
        <h1>Results</h1>
        <div style="display:flex;">
          <button class="btn-share" onclick="navigator.clipboard.writeText('I scored ${totalCorrect}/${total} on Algocare!'); alert('Score copied!')">Share</button>
          <a href="../../dashboard.html" onclick="sessionStorage.removeItem('algocare_results_state');" class="btn-home">Home</a>
        </div>
      </header>
      
      <div class="score-card">
        <h2>${mode === 'real_feel' ? 'Real-Feel Score' : 'Practice Score'}</h2>
        <div class="score-val">${totalCorrect} <span>/ ${total}</span></div>
        <p style="color:var(--ink-soft); margin:0;">${timedOut ? "Time's up!" : `${totalCorrect} correct out of ${total} questions`}</p>
      </div>

      ${subjectHtml}

      <details class="review-section">
        <summary class="review-summary">
          <span>Review Incorrect Answers</span>
          <span style="font-size:0.8rem; color:var(--grey);">▼</span>
        </summary>
        <div class="review-content">${reviewHtml}</div>
      </details>

      <div class="feedback-section">
        <div class="feedback-header">Give Feedback</div>
        <div class="feedback-body" id="feedbackBody">
          <p style="margin-top:0; font-size:0.9rem; color:var(--ink-soft);">How do you feel about the app?</p>
          <div class="star-row" id="starRow">${[1,2,3,4,5].map(n => `<button class="star-btn" data-star="${n}">★</button>`).join("")}</div>
          <textarea class="feedback-textarea" id="feedbackText" placeholder="Any complaints, suggestions, or bugs?"></textarea>
          <button class="btn-submit-feedback" onclick="submitFeedback('${mode}')">Submit Feedback</button>
        </div>
      </div>
    </div>
    <div class="fixed-bottom"><a href="../../dashboard.html" onclick="sessionStorage.removeItem('algocare_results_state');" class="btn-take-another">Back to Dashboard</a></div>
  `;

  setupFeedbackWidget();
}

function setupFeedbackWidget() {
  let selectedStars = 0;
  const stars = document.querySelectorAll('.star-btn');
  stars.forEach(s => {
    s.addEventListener('click', () => {
      selectedStars = parseInt(s.dataset.star);
      stars.forEach(b => b.classList.remove('active'));
      for(let i=0; i<selectedStars; i++) stars[i].classList.add('active');
    });
  });
  window.submitFeedback = (modeType) => {
    if (selectedStars === 0) return alert("Please select a star rating first.");
    const comment = document.getElementById('feedbackText').value;
    logReview(modeType, selectedStars, comment);
    document.getElementById('feedbackBody').innerHTML = `<div style="text-align:center; padding:20px;"><p style="color:var(--scrub); font-weight:700;">Thank you!</p><p style="font-size:0.9rem; color:var(--ink-soft);">Your feedback has been saved.</p></div>`;
  };
}

// Calculator Logic
function toggleCalculator() { document.getElementById('calcModal').classList.toggle('open'); }
let calcExpr = '';
function safeMathEval(str) {
  if (!/^[0-9+\-*/(). ]+$/.test(str)) return 'Error';
  let tokens = str.match(/(\d+\.?\d*|[+\-*/()])/g);
  if (!tokens) return 'Error';
  let pos = 0;
  function parseExpression() {
    let left = parseTerm();
    while (tokens[pos] === '+' || tokens[pos] === '-') {
      let op = tokens[pos++]; let right = parseTerm();
      if (op === '+') left += right; else left -= right;
    } return left;
  }
  function parseTerm() {
    let left = parseFactor();
    while (tokens[pos] === '*' || tokens[pos] === '/') {
      let op = tokens[pos++]; let right = parseFactor();
      if (op === '*') left *= right; else left /= right;
    } return left;
  }
  function parseFactor() {
    if (tokens[pos] === '(') { pos++; let val = parseExpression(); pos++; return val; }
    if (tokens[pos] === '-') { pos++; return -parseFactor(); }
    let num = parseFloat(tokens[pos++]);
    return isNaN(num) ? 'Error' : num;
  }
  try { let res = parseExpression(); return isNaN(res) ? 'Error' : String(res); } catch { return 'Error'; }
}

function calcInput(val) {
  const display = document.getElementById('calcDisplay');
  if (val === 'C') { calcExpr = ''; }
  else if (val === '=') { calcExpr = safeMathEval(calcExpr || '0'); }
  else { if (calcExpr === 'Error') calcExpr = ''; calcExpr += val; }
  display.textContent = calcExpr || '0';
}

// Keyboard shortcuts
window.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
  const key = e.key.toUpperCase();
  if (["A", "B", "C", "D"].includes(key)) selectAnswer(key);
  else if (key === "N") nextQ();
  else if (key === "P") prevQ();
  else if (key === "R") toggleFlag();
  });

// Load Candidate Name
document.addEventListener("visibilitychange", () => {
  // ONLY save if the exam is NOT finished. 
  // This stops the "Return to Exam" button from showing on articles after finishing.
  if (document.visibilityState === "hidden" && !isFinished) {
    clearInterval(timerInterval);
    saveState();
  } else if (!isFinished && endTime) {
    startTimer();
  }
});

window.addEventListener("load", async () => {
  await new Promise(r => setTimeout(r, 200));
  try {
    const user = window.getUser ? window.getUser() : null;
    if (user) {
      const meta = user.user_metadata || {};
      // Priority: Username -> First Name -> Email prefix
      const name = meta.username || (meta.name ? meta.name.split(' ')[0] : user.email.split('@')[0]);
      const regNo = user.id.substring(0, 8).toUpperCase();
      const el = document.getElementById("candidateInfo");
      if (el) el.textContent = `Candidate: ${name} | ${regNo}`;
    }
  } catch (e) { console.log("Auth error:", e); }
  init(); 
});
