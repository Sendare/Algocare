
function generateAttemptId() {
  return crypto.randomUUID();
}

function logTestStarted(attemptId, testType, testIdentifier, questionCount) {
  logEvent("test_events", {
    attempt_id: attemptId,
    user_id: getUserId(),
    program: getProgram() || "nursing",
    event_type: "started",
    test_type: testType,
    test_identifier: testIdentifier,
    question_count: questionCount
  });
}

const SUPABASE_URL = "https://uhrjtcocwejddtzyjyhr.supabase.co";
const API_URL = "https://api.algocare.pages.dev";

function getUserId() {
  let id = localStorage.getItem("algocare_uid");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("algocare_uid", id);
  }
  return id;
}

function getProgram() {
  const segments = window.location.pathname.split("/").filter(Boolean);
  for (const segment of segments) {
    if (["nursing", "midwifery"].includes(segment)) return segment;
  }
  return null;
}

async function logEvent(table, row) {
  try {
    const res = await fetch(`${API_URL}/log-event?table=${table}`, {
      method: "POST",
      keepalive: true,
      headers: {
        "Content-Type": "application/json",
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": `Bearer ${SUPABASE_ANON_KEY}`,
        "Prefer": "return=minimal",
      },
      body: JSON.stringify(row),
    });

    if (!res.ok) {
      const err = await res.text();
      // Show a red banner on the screen
      const debugEl = document.createElement("div");
      debugEl.style.cssText = "position:fixed; bottom:0; left:0; right:0; background:#b14a3a; color:white; padding:16px; z-index:9999; font-family:monospace; font-size:12px; word-wrap:break-word;";
      debugEl.innerHTML = `<strong>Save Error:</strong> ${res.status} ${err}`;
      document.body.appendChild(debugEl);
    }
  } catch (err) {
    console.warn("Analytics log failed:", err);
  }
}

function logTestFinished(attemptId, testType, testIdentifier, questionCount, attempted, correct) {
  logEvent("test_events", {
    attempt_id: attemptId,
    user_id: getUserId(),
    program: getProgram() || "nursing",
    event_type: "finished",
    test_type: testType,
    test_identifier: testIdentifier,
    question_count: questionCount,
    attempted: attempted,
    correct: correct
  });
}

function logReview(testType, stars, comment) {
  logEvent("reviews", {
    user_id: getUserId(),
    program: getProgram() || "nursing",
    test_type: testType || null,
    stars,
    comment: comment || null,
  });
}

function logArticleViewed(topicId) {
  logEvent("article_events", {
    user_id: getUserId(),
    program: getProgram(),
    topic_id: topicId,
    event_type: "viewed"
  });
}
