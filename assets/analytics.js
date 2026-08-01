/**
 * Anonymous analytics for Algocare CBT. No PII is collected - just a random
 * ID generated once per browser (localStorage) plus test-attempt events and
 * optional star ratings. Every failure here is swallowed silently - a
 * broken analytics call must never disrupt the actual test experience.
 */

const SUPABASE_URL = "https://uhrjtcocwejddtzyjyhr.supabase.co"; // <-- replace with your Project URL
const SUPABASE_ANON_KEY = "sb_publishable_C_i1zk4P2phfIALmI6C7Iw_pYSMTGfQ";           // <-- replace with your anon public key

function getUserId() {
  let id = localStorage.getItem("algocare_uid");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("algocare_uid", id);
  }
  return id;
}

function generateAttemptId() {
  return crypto.randomUUID();
}

async function logEvent(table, row) {
  try {
    await fetch(`${SUPABASE_URL}/rest/v1/${table}`, {
      method: "POST",
      keepalive: true, // lets this survive page unload - needed for abandon events
      headers: {
        "Content-Type": "application/json",
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": `Bearer ${SUPABASE_ANON_KEY}`,
        "Prefer": "return=minimal",
      },
      body: JSON.stringify(row),
    });
  } catch (err) {
    console.warn("Analytics log failed (non-fatal):", err);
  }
}

function logTestStarted(attemptId, testType, testIdentifier, questionCount) {
  logEvent("test_events", {
    attempt_id: attemptId,
    user_id: getUserId(),
    event_type: "started",
    test_type: testType,
    test_identifier: testIdentifier,
    question_count: questionCount,
  });
}

function logTestFinished(attemptId, testType, testIdentifier, questionCount, attempted, correct) {
  logEvent("test_events", {
    attempt_id: attemptId,
    user_id: getUserId(),
    event_type: "finished",
    test_type: testType,
    test_identifier: testIdentifier,
    question_count: questionCount,
    attempted,
    correct,
  });
}

function logTestAbandoned(attemptId, testType, testIdentifier, questionCount, attempted) {
  logEvent("test_events", {
    attempt_id: attemptId,
    user_id: getUserId(),
    event_type: "abandoned",
    test_type: testType,
    test_identifier: testIdentifier,
    question_count: questionCount,
    attempted,
  });
}

function logReview(testType, stars, comment) {
  logEvent("reviews", {
    user_id: getUserId(),
    test_type: testType || null,
    stars,
    comment: comment || null,
  });
}

/**
 * Call once right after a test starts (or resumes). Arms a listener that
 * fires exactly one "abandoned" event if the tab is hidden/closed before
 * markFinished() is called. Note: if someone abandons, comes back later,
 * and actually finishes, the earlier abandon event still stays in the data
 * (a small, standard limitation of unload-based tracking - not worth
 * over-engineering around for this use case).
 *
 * Returns a markFinished() function - call it exactly when the test ends.
 */
function trackAbandonment(attemptId, testType, testIdentifier, questionCount, getAttemptedFn) {
  let finished = false;
  let abandonLogged = false;

  const handler = () => {
    if (finished || abandonLogged) return;
    abandonLogged = true;
    logTestAbandoned(attemptId, testType, testIdentifier, questionCount, getAttemptedFn());
  };

  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") handler();
  });
  window.addEventListener("pagehide", handler);

  return function markFinished() {
    finished = true;
  };
}

/**
 * Renders a simple 5-star + optional comment widget into the given
 * container element, and wires up submission.
 */
function attachReviewWidget(containerId, testType) {
  const container = document.getElementById(containerId);
  if (!container) return;

  let selectedStars = 0;

  function render() {
    container.innerHTML = `
      <div class="review-widget">
        <p class="review-prompt">How did this feel?</p>
        <div class="star-row">
          ${[1, 2, 3, 4, 5].map(n => `<button type="button" class="star-btn ${n <= selectedStars ? "filled" : ""}" data-star="${n}">★</button>`).join("")}
        </div>
        <textarea id="reviewComment" placeholder="Anything you want to tell us? (optional)" rows="2"></textarea>
        <button class="btn secondary" id="submitReviewBtn" ${selectedStars ? "" : "disabled"}>Submit feedback</button>
      </div>
    `;
    container.querySelectorAll(".star-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        selectedStars = parseInt(btn.dataset.star, 10);
        render();
      });
    });
    const submitBtn = document.getElementById("submitReviewBtn");
    if (submitBtn) {
      submitBtn.addEventListener("click", () => {
        const comment = document.getElementById("reviewComment").value.trim();
        logReview(testType, selectedStars, comment);
        container.innerHTML = `<p style="color: var(--scrub); font-weight:600;">Thanks for the feedback!</p>`;
      });
    }
  }

  render();
}

