from pathlib import Path

print("🚀 Applying JAMB Results Page UI...")

# ==========================================
# 1. ADD RESULTS CSS
# ==========================================
css_path = Path("cbt-app/exam.css")
css = css_path.read_text()

results_css = """
/* ===== JAMB RESULTS PAGE ===== */
.results-page { background: #09090b; min-height: 100vh; padding: 16px 16px 100px; max-width: 672px; margin: 0 auto; color: #d4d4d8; font-family: var(--body); }
.results-header { display: flex; justify-content: space-between; align-items: center; margin-top: 16px; margin-bottom: 16px; }
.results-header h1 { font-size: 1.25rem; font-weight: 700; color: #fff; margin: 0; }
.results-header-actions { display: flex; gap: 8px; }
.btn-share { background: #f59e0b; color: #000; padding: 6px 12px; border-radius: 8px; font-weight: 700; font-size: 0.875rem; display: flex; align-items: center; gap: 4px; border: none; cursor: pointer; text-decoration: none;}
.btn-home { background: #18181b; color: #a1a1aa; padding: 6px 12px; border-radius: 8px; font-weight: 700; font-size: 0.875rem; display: flex; align-items: center; gap: 4px; border: 1px solid #27272a; cursor: pointer; text-decoration: none;}
.btn-home:hover { color: #fff; }

.score-card { background: #18181b; border: 1px solid #27272a; border-radius: 12px; padding: 24px; text-align: center; margin-top: 8px; }
.score-card h2 { font-size: 0.875rem; font-weight: 700; color: #a1a1aa; text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; margin-top: 0;}
.score-val { font-size: 3rem; font-weight: 700; color: #f59e0b; margin: 8px 0; }
.score-val span { font-size: 1.5rem; color: #52525b; }
.score-sub { font-size: 0.875rem; font-weight: 500; color: #a1a1aa; }

.section-title { font-size: 0.875rem; font-weight: 700; color: #a1a1aa; text-transform: uppercase; letter-spacing: 0.05em; margin: 24px 0 12px; padding: 0 4px; }
.subject-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px; }
.subject-card { background: #18181b; border: 1px solid #27272a; border-radius: 8px; padding: 12px; display: flex; flex-direction: column; justify-content: space-between; }
.subject-name { font-weight: 700; color: #e4e4e7; font-size: 0.875rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; text-transform: capitalize;}
.subject-score-row { display: flex; justify-content: space-between; align-items: flex-end; margin-top: 8px; }
.subject-score-raw { font-size: 0.75rem; color: #a1a1aa; }
.subject-score-bold { font-weight: 700; color: #f59e0b; font-size: 1rem;}
.subject-score-bold span { font-size: 0.7rem; color: #52525b; }

.review-section { background: #18181b; border: 1px solid #27272a; border-radius: 12px; overflow: hidden; margin-top: 24px; }
.review-summary { padding: 16px; font-weight: 700; color: #fff; cursor: pointer; display: flex; justify-content: space-between; align-items: center; background: #09090b; list-style: none; }
.review-summary::-webkit-details-marker { display: none; }
.review-summary:hover { background: #27272a; }
.review-summary-icon { font-size: 0.75rem; color: #a1a1aa; transition: transform 0.2s; }
details[open] .review-summary-icon { transform: rotate(180deg); }
.review-content { padding: 16px; border-top: 1px solid #27272a; }
.wrong-q-card { background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.2); border-radius: 8px; padding: 12px; margin-bottom: 16px; }
.wrong-q-text { font-size: 0.875rem; color: #fff; font-weight: 500; margin-bottom: 8px; }
.ans-line { font-size: 0.75rem; margin-bottom: 4px; }
.ans-yours { color: #f87171; font-weight: 700; }
.ans-correct { color: #34d399; font-weight: 700; }
.expl-box { font-size: 0.75rem; color: #a1a1aa; background: #09090b; padding: 8px; border-radius: 4px; border: 1px solid #27272a; margin-bottom: 12px; }
.learn-more-btn { display: inline-block; background: rgba(245, 158, 11, 0.1); color: #f59e0b; border: 1px solid rgba(245, 158, 11, 0.3); padding: 6px 12px; border-radius: 6px; font-size: 0.75rem; font-weight: 700; text-decoration: none; }
.learn-more-btn:hover { background: rgba(245, 158, 11, 0.2); }

.feedback-section { background: #18181b; border: 1px solid #27272a; border-radius: 12px; overflow: hidden; margin-top: 24px; }
.feedback-header { background: #09090b; padding: 12px; display: flex; align-items: center; gap: 8px; border-bottom: 1px solid #27272a; color: #fff; font-weight: 700; font-size: 0.875rem; }
.feedback-body { padding: 20px; }
.feedback-body p { font-size: 0.875rem; color: #a1a1aa; font-weight: 500; margin-bottom: 16px; margin-top: 0;}
.star-row { display: flex; gap: 8px; margin-bottom: 20px; }
.star-btn { background: none; border: none; color: #3f3f46; cursor: pointer; font-size: 2rem; padding: 0; transition: transform 0.1s; line-height: 1;}
.star-btn.active { color: #f59e0b; }
.star-btn:hover { transform: scale(1.1); }
.cat-row { display: flex; gap: 8px; margin-bottom: 16px; overflow-x: auto; }
.cat-btn { padding: 6px 12px; border-radius: 999px; font-size: 0.75rem; font-weight: 700; border: 1px solid #27272a; background: #09090b; color: #a1a1aa; cursor: pointer; white-space: nowrap; }
.cat-btn.active { background: rgba(245, 158, 11, 0.1); border-color: rgba(245, 158, 11, 0.3); color: #f59e0b; }
.feedback-textarea { width: 100%; background: #09090b; border: 1px solid #27272a; border-radius: 8px; padding: 12px; font-size: 0.875rem; color: #fff; resize: none; height: 96px; margin-bottom: 16px; font-family: var(--body); box-sizing: border-box;}
.feedback-textarea:focus { outline: none; border-color: #f59e0b; }
.btn-submit-feedback { width: 100%; background: #f59e0b; color: #000; padding: 12px; border-radius: 8px; font-weight: 700; border: none; cursor: pointer; font-size: 0.875rem; }
.feedback-success { padding: 32px; display: flex; flex-direction: column; align-items: center; text-align: center; }
.feedback-success h4 { color: #fff; font-weight: 700; margin: 0; }
.feedback-success p { color: #a1a1aa; font-size: 0.875rem; margin-top: 4px; }

.fixed-bottom { position: fixed; bottom: 0; left: 0; right: 0; padding: 16px; background: #09090b; border-top: 1px solid #27272a; z-index: 100; }
.btn-take-another { width: 100%; background: #f59e0b; color: #000; padding: 12px; border-radius: 8px; font-weight: 700; border: none; cursor: pointer; font-size: 1rem; max-width: 672px; margin: 0 auto; display: block; }
"""
if "/* ===== JAMB RESULTS PAGE ===== */" not in css:
    css += results_css
    css_path.write_text(css)
    print("✅ Added JAMB Results CSS")

# ==========================================
# 2. OVERWRITE PRACTICE JS (New Results Page)
# ==========================================
practice_js = Path("cbt-app/js/practice_v2.js")
src = practice_js.read_text()

# Replace the finishTest function
import re
start_idx = src.find("function finishTest(timedOut) {")
end_idx = src.find("window.addEventListener(\"keydown\"")
if start_idx != -1 and end_idx != -1:
    new_finish = """function finishTest(timedOut) {
  clearInterval(timerInterval);
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

  markTestFinished(); logTestFinished(attemptId, "practice", coursesParam, total, attempted, totalCorrect); clearState();

  // Build Subject Breakdown HTML
  const subjectHtml = subjectResults.map(r => `
    <div class="subject-card">
      <div class="subject-name">${r.sub.replace(/-/g, ' ')}</div>
      <div class="subject-score-row">
        <span class="subject-score-raw">${r.correct}/${r.total}</span>
        <span class="subject-score-bold">${r.correct}<span>/${r.total}</span></span>
      </div>
    </div>
  `).join("");

  // Build Review Incorrect HTML
  let reviewHtml = "";
  subjects.forEach(sub => {
    const wrongQs = questions[sub].filter(q => answers[q.question_id] && !answers[q.question_id].isCorrect);
    if (wrongQs.length === 0) return;
    
    reviewHtml += `<div style="margin-bottom: 24px;"><h3 style="color:#e4e4e7; text-transform:capitalize; border-bottom:1px solid #27272a; padding-bottom:4px; margin-bottom:12px; font-size:1rem;">${sub.replace(/-/g, ' ')}</h3>`;
    wrongQs.forEach(q => {
      const uAns = answers[q.question_id].selected;
      const cAns = q.answer;
      const uText = q.options[uAns];
      const cText = q.options[cAns];
      
      // Find learn more link
      const entry = window.siteIndex?.find(i => i.topic_id === q.topic_id);
      const learnMoreBtn = entry ? `<a href="../${entry.url}" class="learn-more-btn">Learn More →</a>` : '';

      reviewHtml += `
        <div class="wrong-q-card">
          <div class="wrong-q-text">${q.question}</div>
          <div class="ans-line"><span class="ans-yours">Your answer:</span> ${uText}</div>
          <div class="ans-line"><span class="ans-correct">Correct answer:</span> ${cText}</div>
          ${q.explanation ? `<div class="expl-box"><strong style="color:#e4e4e7;">Explanation:</strong> ${parseExplanation(q.explanation, q.topic_id)}</div>` : ''}
          ${learnMoreBtn}
        </div>
      `;
    });
    reviewHtml += `</div>`;
  });

  if (!reviewHtml) reviewHtml = `<p style="text-align:center; color:#a1a1aa; font-size:0.875rem;">You got everything right! No corrections to show.</p>`;

  document.body.style.background = "#09090b";
  document.getElementById("examRoot").innerHTML = `
    <div class="results-page">
      <header class="results-header">
        <h1>Results</h1>
        <div class="results-header-actions">
          <button class="btn-share" onclick="handleShare(${totalCorrect}, ${total})">
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
        <h2>Practice Score</h2>
        <div class="score-val">${totalCorrect} <span>/ ${total}</span></div>
        <p class="score-sub">${totalCorrect} correct out of ${total} questions</p>
      </div>

      <h3 class="section-title">Subject Breakdown</h3>
      <div class="subject-grid">${subjectHtml}</div>

      <details class="review-section">
        <summary class="review-summary">
          <span>Review Incorrect Answers</span>
          <span class="review-summary-icon">▼</span>
        </summary>
        <div class="review-content">${reviewHtml}</div>
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
          <button class="btn-submit-feedback" onclick="submitFeedback('practice')">Submit Feedback</button>
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
  const text = `I just scored ${score}/${total} on Algocare Practice! 🎯 Ready for my exams. Practice here:`;
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

"""
    src = src[:start_idx] + new_finish + "\n" + src[end_idx:]
    practice_js.write_text(src)
    print("✅ Overwrote Practice Results")


# ==========================================
# 3. OVERWRITE EXAM JS (Real-Feel Results)
# ==========================================
exam_js = Path("cbt-app/js/exam_v2.js")
src = exam_js.read_text()

start_idx = src.find("function finishExam() {")
end_idx = src.find("window.addEventListener(\"keydown\"")
if start_idx != -1 and end_idx != -1:
    new_finish = """function finishExam() {
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

"""
    src = src[:start_idx] + new_finish + "\n" + src[end_idx:]
    exam_js.write_text(src)
    print("✅ Overwrote Real-Feel Results")

print("🎉 Results Page completely rebuilt to match JAMB.")
