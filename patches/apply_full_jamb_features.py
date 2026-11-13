#!/usr/bin/env python3
from pathlib import Path

print("🚀 Applying ALL JAMB features to Algocare...")

# ==========================================
# 1. UPDATE CSS (Tabs, Flags, Modals, Toasts)
# ==========================================
css_path = Path("cbt-app/exam.css")
css = css_path.read_text()

# Add new styles for tabs, modals, and toasts
css += """
/* JAMB Tabs */
.exam-tabs { display: flex; overflow-x: auto; background: #09090b; border-bottom: 1px solid #27272a; padding: 0 16px; }
.exam-tab { padding: 12px 20px; color: #a1a1aa; font-weight: 600; font-size: 0.9rem; border-bottom: 2px solid transparent; cursor: pointer; white-space: nowrap; background: none; border-top: none; border-left: none; border-right: none; }
.exam-tab.active { color: #fff; border-bottom-color: #f59e0b; background: #18181b; }

/* Flag Button */
.exam-flag-btn { background: none; border: none; color: #a1a1aa; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 6px; font-size: 0.85rem; }
.exam-flag-btn.flagged { color: #f59e0b; }

/* Toast */
.toast { position: fixed; top: 80px; left: 50%; transform: translateX(-50%); background: #ef4444; color: white; padding: 12px 24px; border-radius: 6px; font-weight: 600; z-index: 1000; box-shadow: 0 4px 12px rgba(0,0,0,0.3); transition: opacity 0.3s; }

/* Modal */
.modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.8); display: flex; align-items: center; justify-content: center; z-index: 1000; }
.modal-content { background: #18181b; padding: 24px; border-radius: 12px; border: 1px solid #27272a; max-width: 400px; width: 90%; text-align: center; color: white; }
.modal-content h2 { color: #f59e0b; margin-top: 0; }
.modal-content p { color: #a1a1aa; margin-bottom: 24px; }
.modal-actions { display: flex; gap: 12px; justify-content: center; }
"""
css_path.write_text(css)

# ==========================================
# 2. UPDATE SETUP JS (Multi-Course Selection)
# ==========================================
setup_js = Path("cbt-app/js/setup_v2.js")
src = setup_js.read_text()

# Replace single select with multi-checkboxes
src = src.replace(
    """        <div class="form-row">
          <label>Course</label>
          <select id="courseSelect" required><option value="" disabled selected>Select a course...</option>${courseOptions}</select>
        </div>""",
    """        <div class="form-row">
          <label>Select Courses (Pick 1 or more)</label>
          <div style="max-height: 150px; overflow-y: auto; background: var(--paper); border: 1px solid var(--grey-line); padding: 8px; border-radius: 6px;">
            ${Object.entries(courseMap).sort((a, b) => a[1].localeCompare(b[1])).map(([slug, name]) => `
              <label style="display: flex; align-items: center; gap: 8px; padding: 6px; font-size: 0.9rem; cursor: pointer;">
                <input type="checkbox" name="courseCheckbox" value="${slug}"> ${name}
              </label>
            `).join("")}
          </div>
        </div>"""
)

# Update the submit handler to gather multiple courses
src = src.replace(
    """    const course = document.getElementById("courseSelect").value;
    const count = document.getElementById("questionCount").value;
    const spq = document.getElementById("secondsPerQuestion").value;
    window.location.href = `practice.html?course=${course}&count=${count}&spq=${spq}`;""",
    """    const checkboxes = document.querySelectorAll('input[name="courseCheckbox"]:checked');
    if (checkboxes.length === 0) { alert("Please select at least one course."); return; }
    const courses = Array.from(checkboxes).map(cb => cb.value).join(",");
    const count = document.getElementById("questionCount").value;
    const spq = document.getElementById("secondsPerQuestion").value;
    window.location.href = `practice.html?courses=${courses}&count=${count}&spq=${spq}`;"""
)
setup_js.write_text(src)

# ==========================================
# 3. UPDATE PRACTICE JS (Tabs, Flags, Catch Skips, Keyboard)
# ==========================================
practice_js = Path("cbt-app/js/practice_v2.js")
src = practice_js.read_text()

# 3a. State variables
src = src.replace(
    "const courseSlug = params.get(\"course\");",
    "const coursesParam = params.get(\"courses\");"
)
src = src.replace(
    "let questions = [], current = 0, answers = [], endTime = null, pauseStartedAt = null, timerInterval = null, attemptId = null;",
    """let subjects = [];
let questions = {}; 
let currentIndexes = {};
let activeSubject = "";
let answers = {}; 
let flags = [];
let endTime = null, pauseStartedAt = null, timerInterval = null, attemptId = null;
let isCatchingSkips = false;"""
)

# 3b. Init logic for multi-course
src = src.replace(
    """      let pool = [];
      if (topicId) pool = await (await fetch(`../data/questions/${topicId}.json`)).json();
      else if (courseSlug) pool = await (await fetch(`../data/course_pools/${courseSlug}.json`)).json();
      else { document.getElementById("examRoot").innerHTML = `<div class="empty-state" style="color:#a1a1aa; text-align:center; padding:40px;">No course or topic specified. <a href="index.html">Go back</a></div>`; return; }

      const count = requestedCount ? Math.min(requestedCount, pool.length) : pool.length;
      questions = shuffle(pool).slice(0, count);
      answers = new Array(questions.length).fill(null);
      endTime = Date.now() + questions.length * secondsPerQuestion * 1000;
      attemptId = generateAttemptId();
      saveState();
      logTestStarted(attemptId, "practice", topicId || courseSlug, questions.length);""",
    """      if (!coursesParam) { document.getElementById("examRoot").innerHTML = `<div class="empty-state" style="color:#a1a1aa; text-align:center; padding:40px;">No courses specified. <a href="index.html">Go back</a></div>`; return; }
      
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
      logTestStarted(attemptId, "practice", coursesParam, totalAllowed);"""
)

# 3c. Timer and Helpers
src = src.replace(
    "function isPaused() { const a = answers[current]; return !!(a && a.showExplanation); }",
    """function isPaused() { const q = questions[activeSubject][currentIndexes[activeSubject]]; const a = answers[q.question_id]; return !!(a && a.showExplanation); }
function getAnsweredCount() { return Object.keys(answers).length; }
function getTotalQuestions() { return subjects.reduce((acc, sub) => acc + questions[sub].length, 0); }
function updateTopSubmit() { const canSubmit = getAnsweredCount() >= Math.floor(getTotalQuestions() / 2); document.getElementById("topSubmitBtn").disabled = !canSubmit; }
function showToast(msg) { const t = document.createElement("div"); t.className = "toast"; t.textContent = msg; document.body.appendChild(t); setTimeout(() => t.remove(), 3000); }"""
)

# 3d. Render function
src = src.replace(
    """function render() {
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
      <div class="exam-actions" style="margin-top:auto">
        <button class="exam-btn exam-btn-prev" onclick="prevQ()" ${current===0?'disabled':''}>← Prev (P)</button>
        ${!ans ? `<button class="exam-btn exam-btn-next" onclick="nextQ()">Next (N) →</button>` : ''}
      </div>
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
}""",
    """function render() {
  reconcilePause();
  updateTopSubmit();
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
  const current = currentIndexes[activeSubject];
  const qList = questions[activeSubject];
  
  if (isCatchingSkips) {
    // Catch skips logic
    let targetSub = '', targetIndex = -1;
    for (let s = subjects.indexOf(activeSubject); s < subjects.length; s++) {
      const sub = subjects[s]; const subQs = questions[sub];
      for (let i = 0; i < subQs.length; i++) {
        if (s === subjects.indexOf(activeSubject) && i <= current) continue;
        if (!answers[subQs[i].question_id]) { targetSub = sub; targetIndex = i; break; }
      }
      if (targetSub) break;
    }
    if (!targetSub) {
      for (let s = 0; s <= subjects.indexOf(activeSubject); s++) {
        const sub = subjects[s]; const subQs = questions[sub];
        for (let i = 0; i < subQs.length; i++) {
          if (s === subjects.indexOf(activeSubject) && i >= current) break;
          if (!answers[subQs[i].question_id]) { targetSub = sub; targetIndex = i; break; }
        }
        if (targetSub) break;
      }
    }
    if (targetSub) { switchTab(targetSub); jumpTo(targetIndex); isCatchingSkips = true; showToast("Jumped to next unanswered"); }
    else { handleSubmitClick(); }
    return;
  }
  
  if (current < qList.length - 1) { jumpTo(current + 1); }
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
}"""
)

# 3e. Keyboard shortcuts
src = src.replace(
    "window.addEventListener(\"load\", async () => {",
    """window.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
  const key = e.key.toUpperCase();
  const q = questions[activeSubject][currentIndexes[activeSubject]];
  if (["A", "B", "C", "D"].includes(key)) selectAnswer(key);
  else if (key === "N") nextQ();
  else if (key === "P") prevQ();
  else if (key === "R") toggleFlag();
  else if (key === "S") handleSubmitClick();
});

window.addEventListener("load", async () => {"""
)

# 3f. Submit Modal and logic
src = src.replace(
    """function finishTest(timedOut) {""",
    """function handleSubmitClick() {
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

function finishTest(timedOut) {"""
)

# Update save/load state for new variables
src = src.replace(
    "function saveState() { sessionStorage.setItem(STORAGE_KEY, JSON.stringify({questions,current,answers,endTime,pauseStartedAt,attemptId})); }",
    "function saveState() { sessionStorage.setItem(STORAGE_KEY, JSON.stringify({subjects,questions,currentIndexes,activeSubject,answers,flags,endTime,pauseStartedAt,attemptId})); }"
)
src = src.replace(
    "({questions,current,answers,endTime,pauseStartedAt,attemptId} = saved);",
    "({subjects,questions,currentIndexes,activeSubject,answers,flags,endTime,pauseStartedAt,attemptId} = saved);"
)

practice_js.write_text(src)

# ==========================================
# 4. UPDATE EXAM V2 JS (Flags, Catch Skips, Keyboard)
# ==========================================
exam_js = Path("cbt-app/js/exam_v2.js")
src = exam_js.read_text()

# 4a. State
src = src.replace(
    "let questions = [], current = 0, answers = [], endTime = null, timerInterval = null, finished = false, attemptId = null;",
    """let questions = [], current = 0, answers = {}, flags = [], endTime = null, timerInterval = null, finished = false, attemptId = null;
let isCatchingSkips = false;"""
)

# 4b. Init
src = src.replace(
    "answers = new Array(questions.length).fill(null);",
    "answers = {}; flags = [];"
)

# 4c. Helpers
src = src.replace(
    "function answeredCount() { return answers.filter(a => a !== null).length; }",
    """function answeredCount() { return Object.keys(answers).length; }
function updateTopSubmit() { const canSubmit = answeredCount() >= Math.floor(questions.length / 2); document.getElementById("topSubmitBtn").disabled = !canSubmit; }
function showToast(msg) { const t = document.createElement("div"); t.className = "toast"; t.textContent = msg; document.body.appendChild(t); setTimeout(() => t.remove(), 3000); }"""
)

# 4d. Render
src = src.replace(
    """function render() {
  if (finished) return;
  const q = questions[current], selected = answers[current];
  const opts = Object.keys(q.options).map(k => {
    const cls = "exam-opt" + (k === selected ? " selected" : "");
    return `<button class="${cls}" onclick="selectAnswer('${k}')"><div class="opt-letter">${k}</div><div>${q.options[k]}</div></button>`;
  }).join("");

  const canSubmit = answeredCount() >= window.submitThreshold;
  const topSubmitBtn = document.getElementById("topSubmitBtn");
  if (topSubmitBtn) topSubmitBtn.disabled = !canSubmit;

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
}""",
    """function render() {
  if (finished) return;
  updateTopSubmit();
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
  if (isCatchingSkips) {
    let targetIndex = -1;
    for (let i = current + 1; i < questions.length; i++) { if (!answers[questions[i].question_id]) { targetIndex = i; break; } }
    if (targetIndex === -1) {
      for (let i = 0; i < current; i++) { if (!answers[questions[i].question_id]) { targetIndex = i; break; } }
    }
    if (targetIndex !== -1) { jumpTo(targetIndex); isCatchingSkips = true; showToast("Jumped to next unanswered"); }
    else { handleSubmitClick(); }
    return;
  }
  if (current < questions.length - 1) { jumpTo(current + 1); }
}

function prevQ() { if (current > 0) { jumpTo(current - 1); } isCatchingSkips = false; }"""
)

# 4e. State save/load
src = src.replace(
    "function saveState() { if (!STORAGE_KEY || finished) return; sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ current, answers, endTime, attemptId })); }",
    "function saveState() { if (!STORAGE_KEY || finished) return; sessionStorage.setItem(STORAGE_KEY, JSON.stringify({ current, answers, flags, endTime, attemptId })); }"
)
src = src.replace(
    "({current, answers, endTime, attemptId} = saved);",
    "({current, answers, flags, endTime, attemptId} = saved);"
)

# 4f. Submit modal
src = src.replace(
    """function finishExam() {""",
    """function handleSubmitClick() {
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

function finishExam() {"""
)

# 4g. Keyboard shortcuts
src = src.replace(
    "window.addEventListener(\"load\", async () => { init(); });",
    """window.addEventListener("keydown", (e) => {
  if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;
  const key = e.key.toUpperCase();
  const q = questions[current];
  if (["A", "B", "C", "D"].includes(key)) selectAnswer(key);
  else if (key === "N") nextQ();
  else if (key === "P") prevQ();
  else if (key === "R") toggleFlag();
  else if (key === "S") handleSubmitClick();
});

window.addEventListener("load", async () => { init(); });"""
)

exam_js.write_text(src)

# ==========================================
# 5. UPDATE HTML TEMPLATES (Candidate Info, Top Submit)
# ==========================================
for f in ["cbt-app/exam-mode.html", "cbt-app/practice.html"]:
    html = Path(f)
    src = html.read_text()
    # Add candidate info
    src = src.replace(
        '<span style="font-size:0.75rem; color:#a1a1aa">Exam Mode</span>',
        '<span style="font-size:0.75rem; color:#a1a1aa">Candidate: [Name] | [Reg No]</span>'
    )
    src = src.replace(
        '<span style="font-size:0.75rem; color:#a1a1aa">Practice Mode</span>',
        '<span style="font-size:0.75rem; color:#a1a1aa">Candidate: [Name] | [Reg No]</span>'
    )
    # Hook up top submit button
    src = src.replace(
        '<button id="topSubmitBtn" class="exam-btn-submit" onclick="finishExam()" disabled>Submit</button>',
        '<button id="topSubmitBtn" class="exam-btn-submit" onclick="handleSubmitClick()" disabled>Submit</button>'
    )
    src = src.replace(
        '<button id="topSubmitBtn" class="exam-btn-submit" onclick="finishTest(false)" disabled>Submit</button>',
        '<button id="topSubmitBtn" class="exam-btn-submit" onclick="handleSubmitClick()" disabled>Submit</button>'
    )
    html.write_text(src)

print("✅ All 6 JAMB features applied successfully.")
