const params = new URLSearchParams(window.location.search);
const testNumber = params.get("test");
const STORAGE_KEY = testNumber ? `algocare_realfeel_${testNumber}` : null;

let config = { question_count: 250, seconds_per_question: 30, min_answered_to_submit: 125 };
let questions = [], current = 0, answers = {}, flags = [], endTime = null, timerInterval = null, finished = false, attemptId = null;
let isCatchingSkips = false;

function saveState() { if (!STORAGE_KEY || finished) return; sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ current, answers, flags, endTime, attemptId, isCatchingSkips })); }
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
  if (saved && Array.isArray(saved.answers) && Object.keys(saved.answers).length > 0) {
    current = saved.current || 0; answers = saved.answers || {}; flags = saved.flags || []; endTime = saved.endTime; attemptId = saved.attemptId; isCatchingSkips = saved.isCatchingSkips || false;
  } else {
    answers = {}; flags = [];
    endTime = Date.now() + questions.length * config.seconds_per_question * 1000;
    attemptId = generateAttemptId();
    saveState();
    logTestStarted(attemptId, "real_feel", testNumber, questions.length);
  }
  markTestFinished = trackAbandonment(attemptId, "real_feel", testNumber, questions.length, () => Object.keys(answers).length);
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

function answeredCount() { return Object.keys(answers).length; }

function showToast(msg) { 
  const t = document.createElement("div"); 
  t.className = "toast"; 
  t.textContent = msg; 
  document.body.appendChild(t); 
  setTimeout(() => t.remove(), 3000); 
}

function render() {
  if (finished) return;
  const q = questions[current], selected = answers[q.question_id];
  const isFlagged = flags.includes(q.question_id);
  
  const opts = Object.keys(q.options).map(k => {
    const cls = "exam-opt" + (k === selected ? " selected" : "");
    return `<button class="${cls}" onclick="selectAnswer('${k}')"><div class="opt-letter">${k}</div><div>${q.options[k]}</div></button>`;
  }).join("");

  document.getElementById("examRoot").innerHTML = `
    <div class="exam-main">
      <div class="exam-q-info">
        <span>Question ${current + 1} of ${questions.length}</span>
        <span>| Answered: ${answeredCount()}/${questions.length}</span>
        <button class="exam-flag-btn ${isFlagged ? 'flagged' : ''}" onclick="toggleFlag()">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path><line x1="4" y1="22" x2="4" y2="15"></line></svg>
          ${isFlagged ? 'Flagged' : 'Flag (R)'}
        </button>
      </div>
      <div class="exam-card"><div class="exam-q-text">${q.question}</div><div class="exam-options">${opts}</div></div>
      <div class="exam-actions" style="margin-top:auto">
        <button class="exam-btn exam-btn-prev" onclick="prevQ()" ${current === 0 ? "disabled" : ""}>← Prev (P)</button>
        <button class="exam-btn exam-btn-next" onclick="nextQ()">Next (N) →</button>
      </div>
    </div>
    <div class="exam-palette">
      <div class="palette-header"><span>Question Palette</span></div>
      <div class="palette-grid">${questions.map((item, i) => {
          let c = "palette-btn";
          if (i === current) c += " current";
          else if (answers[item.question_id]) c += " answered";
          if (flags.includes(item.question_id)) c += " flagged";
          return `<button class="${c}" onclick="jumpTo(${i})">${i + 1}</button>`;
        }).join("")}</div>
    </div>
  `;
}

function jumpTo(i) { current = i; isCatchingSkips = false; saveState(); render(); }
function toggleFlag() { const q = questions[current]; if (flags.includes(q.question_id)) flags = flags.filter(id => id !== q.question_id); else flags.push(q.question_id); saveState(); render(); }

function nextQ() {
  if (isCatchingSkips || current === questions.length - 1) {
    let targetIndex = -1;
    for (let i = current + 1; i < questions.length; i++) { if (!answers[questions[i].question_id]) { targetIndex = i; break; } }
    if (targetIndex === -1) {
      for (let i = 0; i <= current; i++) { if (!answers[questions[i].question_id]) { targetIndex = i; break; } }
    }
    if (targetIndex !== -1) { jumpTo(targetIndex); isCatchingSkips = true; showToast("Jumped to next unanswered question"); }
    else { handleSubmitClick(); }
    return;
  }
  if (current < questions.length - 1) { jumpTo(current + 1); }
}

function prevQ() { if (current > 0) { jumpTo(current - 1); } isCatchingSkips = false; }
function selectAnswer(k) { answers[questions[current].question_id] = k; saveState(); render(); }

function handleSubmitClick() {
  const answered = answeredCount();
  const total = questions.length;
  if (answered < Math.floor(total / 2)) { showToast(`You must answer at least ${Math.floor(total / 2)} questions to submit.`); return; }
  
  const modal = document.createElement("div");
  modal.className = "modal-overlay";
  modal.innerHTML = `
    <div class="modal-content">
      <h2>Submit Exam?</h2>
      <p>You have answered <strong>${answered}</strong> out of <strong>${total}</strong> questions.</p>
      <div class="modal-actions">
        <button class="exam-btn exam-btn-prev" onclick="this.closest('.modal-overlay').remove()">Cancel</button>
        <button class="exam-btn exam-btn-next" onclick="this.closest('.modal-overlay').remove(); finishExam()">Submit</button>
      </div>
    </div>
  `;
  document.body.appendChild(modal);
}

function finishExam() {
  if (finished) return;
  finished = true;
  clearInterval(timerInterval);
  const total = questions.length, attempted = answeredCount();
  let correct = 0;
  questions.forEach((q) => { if (answers[q.question_id] === q.answer) correct++; });

  markTestFinished(); logTestFinished(attemptId, "real_feel", testNumber, total, attempted, correct); clearState();

  // Build Review Incorrect HTML (No explanations for real-feel)
  let reviewHtml = "";
  questions.forEach(q => {
    const uAns = answers[q.question_id];
    if (uAns && uAns !== q.answer) {
      const uText = q.options[uAns];
      const cText = q.options[q.answer];
      
      const entry = window.siteIndex?.find(i => i.topic_id === q.topic_id);
      const learnMoreBtn = entry ? `<a href="../${entry.url}" class="learn-more-btn">Learn More →</a>` : '';

      reviewHtml += `
        <div class="wrong-q-card">
          <div class="wrong-q-text">${q.question}</div>
          <div class="ans-line"><span class="ans-yours">Your answer:</span> ${uText}</div>
          <div class="ans-line"><span class="ans-correct">Correct answer:</span> ${cText}</div>
          ${learnMoreBtn}
        </div>
      `;
    }
  });

  if (!reviewHtml) reviewHtml = `<p style="text-align:center; color:#a1a1aa; font-size:0.875rem;">You got everything right! No corrections to show.</p>`;

  document.body.style.background = "#09090b";
  document.getElementById("examRoot").innerHTML = `
    <div class="results-page">
      <header class="results-header">
        <h1>Results</h1>
        <div class="results-header-actions">
          <button class="btn-share" onclick="handleShare(${correct}, ${total})">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="18" cy="5" r="3"></circle><circle cx="6" cy="12" r="3"></circle><circle cx="18" cy="19" r="3"></circle><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"></line><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"></line></svg>
            Share
          </button>
          <a href="index.html" class="btn-home">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>
            Home
          </a>
        </div>
      </header>

      <div class="score-card">
        <h2>JAMB UTME Score</h2>
        <div class="score-val">${correct} <span>/ ${total}</span></div>
        <p class="score-sub">${correct} correct out of ${total} questions</p>
      </div>

      <details class="review-section">
        <summary class="review-summary">
          <span>Review Incorrect Answers</span>
          <span class="review-summary-icon">▼</span>
        </summary>
        <div class="review-content">
          <p style="color:#a1a1aa; font-size:0.875rem; margin-top:0; margin-bottom:16px;">Answers and explanations are not shown for real-feel exams.</p>
          ${reviewHtml}
        </div>
      </details>

      <div class="feedback-section" id="feedbackContainer">
        <div class="feedback-header">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>
          Give Feedback
        </div>
        <div class="feedback-body" id="feedbackBody">
          <p>How do you feel about the app? Any complaints, suggestions, or bugs to report?</p>
          <div class="star-row" id="starRow">
            ${[1,2,3,4,5].map(n => `<button class="star-btn" data-star="${n}">★</button>`).join("")}
          </div>
          <div class="cat-row" id="catRow">
            ${['General', 'Suggestion', 'Bug Report'].map((c, i) => `<button class="cat-btn ${i===0?'active':''}" data-cat="${c}">${c}</button>`).join("")}
          </div>
          <textarea class="feedback-textarea" id="feedbackText" placeholder="Tell us what you think or how we can improve..."></textarea>
          <button class="btn-submit-feedback" onclick="submitFeedback('real_feel')">Submit Feedback</button>
        </div>
      </div>
    </div>
    <div class="fixed-bottom">
      <a href="index.html" class="btn-take-another" style="text-decoration:none; display:block; text-align:center;">Take Another Exam</a>
    </div>
  `;
  setupFeedbackWidget();
}

function handleShare(score, total) {
  const text = `I just scored ${score}/${total} on Algocare CBT! 🎯 Ready for my exams. Practice here:`;
  const url = window.location.origin + "/" + (window.location.pathname.split('/')[1] || '');
  if (navigator.share) {
    navigator.share({ title: 'Algocare', text: text, url: url }).catch(console.error);
  } else {
    navigator.clipboard.writeText(text + " " + url);
    alert('Link copied to clipboard!');
  }
}

function setupFeedbackWidget() {
  let selectedStars = 0;
  let selectedCat = 'General';
  const stars = document.querySelectorAll('.star-btn');
  const cats = document.querySelectorAll('.cat-btn');

  stars.forEach(s => {
    s.addEventListener('click', () => {
      selectedStars = parseInt(s.dataset.star);
      stars.forEach(b => b.classList.remove('active'));
      for(let i=0; i<selectedStars; i++) stars[i].classList.add('active');
    });
  });

  cats.forEach(c => {
    c.addEventListener('click', () => {
      selectedCat = c.dataset.cat;
      cats.forEach(b => b.classList.remove('active'));
      c.classList.add('active');
    });
  });

  window.submitFeedback = (mode) => {
    if (selectedStars === 0) return alert("Please select a star rating first.");
    const comment = document.getElementById('feedbackText').value;
    
    // Use analytics.js function to save to DB
    logReview(mode, selectedStars, comment);
    
    document.getElementById('feedbackBody').innerHTML = `
      <div class="feedback-success">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
        <h4>Thank you!</h4>
        <p>Your feedback has been securely saved.</p>
      </div>
    `;
  };
}


window.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
  const key = e.key.toUpperCase();
  if (["A", "B", "C", "D"].includes(key)) selectAnswer(key);
  else if (key === "N") nextQ();
  else if (key === "P") prevQ();
  else if (key === "R") toggleFlag();
  else if (key === "S") handleSubmitClick();
});

window.addEventListener("load", async () => {
  try {
    const user = window.getUser ? window.getUser() : null;
    if (user) {
      window.candidateName = user.user_metadata?.name || user.email.split('@')[0];
      window.candidateRegNo = user.id.substring(0, 8).toUpperCase();
    }
  } catch (e) { console.warn("Auth not loaded"); }
  init(); 
});
