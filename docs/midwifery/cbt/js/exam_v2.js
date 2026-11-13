
const params = new URLSearchParams(window.location.search);
const testNumber = params.get("test");
const STORAGE_KEY = testNumber ? `algocare_realfeel_${testNumber}` : null;

let config = { question_count: 250, seconds_per_question: 30, min_answered_to_submit: 125 };
let questions = [], current = 0, answers = {}, flags = [], endTime = null, timerInterval = null, finished = false, attemptId = null;
let isCatchingSkips = false;
let markTestFinished = () => {};

function saveState() { if (!STORAGE_KEY || finished) return; sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ current, answers, flags, endTime, attemptId })); }
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
    answers = {}; flags = [];
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

function answeredCount() { return Object.keys(answers).length; }
function updateTopSubmit() { const canSubmit = answeredCount() >= Math.floor(questions.length / 2); document.getElementById("topSubmitBtn").disabled = !canSubmit; }
function showToast(msg) { const t = document.createElement("div"); t.className = "toast"; t.textContent = msg; document.body.appendChild(t); setTimeout(() => t.remove(), 3000); }

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
      <div class="exam-q-info"><span>Question ${current + 1} of ${questions.length}</span><span>| Answered: ${answeredCount()}/${questions.length}</span></div>
      <div class="exam-card"><div class="exam-q-text">${q.question}</div><div class="exam-options">${opts}</div></div>
      <div class="exam-actions" style="margin-top:auto">
        <button class="exam-btn exam-btn-prev" onclick="prevQ()" ${current === 0 ? "disabled" : ""}>← Prev (P)</button>
        <button class="exam-btn exam-btn-next" onclick="nextQ()" ${current === questions.length - 1 ? "disabled" : ""}>Next (N) →</button>
        
      </div>
    </div>
    <div class="exam-palette">
      <div class="palette-header"><span>Question Palette</span></div>
      <div class="palette-grid">${questions.map((_, i) => {
          let c = "palette-btn";
          if (i === current) c += " current";
          else if (answers[i]) c += " answered";
          return `<button class="${c}" onclick="jumpTo(${i})">${i + 1}</button>`;
        }).join("")}</div>
    </div>
  `;
}

function selectAnswer(k) { answers[current] = k; isCatchingSkips = false; saveState(); render(); }
function jumpTo(i) { current = i; saveState(); render(); }
function prevQ() { if (current > 0) { current--; saveState(); render(); } }
function nextQ() {
  // Trigger catch skips if we are already doing it, OR if we are on the very last question
  if (isCatchingSkips || current === questions.length - 1) {
    let targetIndex = -1;
    
    // Search forward from current position
    for (let i = current + 1; i < questions.length; i++) { 
      if (!answers[questions[i].question_id]) { targetIndex = i; break; } 
    }
    
    // If not found forward, search from the beginning
    if (targetIndex === -1) {
      for (let i = 0; i <= current; i++) { 
        if (!answers[questions[i].question_id]) { targetIndex = i; break; } 
      }
    }
    
    if (targetIndex !== -1) { 
      jumpTo(targetIndex); 
      isCatchingSkips = true; 
      showToast("Jumped to next unanswered"); 
    } else { 
      handleSubmitClick(); 
    }
    return;
  }
  
  // Normal sequential next
  if (current < questions.length - 1) { 
    jumpTo(current + 1); 
  }
}

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

  document.body.style.background = "#F7F8F7";
  document.getElementById("examRoot").innerHTML = `
    <div class="score-summary" style="min-height: 100vh; display: flex; flex-direction: column; justify-content: center; padding: 40px 20px;">
      <h2 style="color: #16232E;">Exam complete</h2>
      <div class="big-score" style="color: #16232E;">${correct} out of ${total}</div>
      <div style="color: #46545F; margin-top: 8px;">
        <p style="margin: 4px 0;">Attempted: ${attempted} out of ${total}</p>
        <p style="margin: 4px 0;">Correct answers: ${correct}</p>
        <p style="margin: 4px 0;">Score (of attempted): ${correct} out of ${attempted} · ${pctOfAttempted}%</p>
        <p style="margin: 4px 0;">Score (of all ${total}): ${correct} out of ${total} · ${pctOfTotal}%</p>
      </div>
      <p style="color: #46545F; font-size: 0.85rem; margin-top: 10px;">Answers and explanations are not shown for real-feel exams.</p>
      <div id="reviewWidgetContainer"></div>
      <a class="btn" href="index.html" style="text-decoration:none; display:inline-block; margin: 16px auto 0; width: fit-content;">Back to practice tests</a>
    </div>
  `;
  attachReviewWidget("reviewWidgetContainer", "real_feel");
}

window.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
  const key = e.key.toUpperCase();
  const q = questions[current];
  if (["A", "B", "C", "D"].includes(key)) selectAnswer(key);
  else if (key === "N") nextQ();
  else if (key === "P") prevQ();
  else if (key === "R") toggleFlag();
  else if (key === "S") handleSubmitClick();
});

window.addEventListener("load", async () => { init(); });
