const API_URL = "https://algocare-api.abdul01abdul03.workers.dev";

// Helper: Get the ID (Logged in user, or Anonymous)
function getUserId() {
  const user = window.getUser ? window.getUser() : null;
  if (user) return user.id;
  
  let id = localStorage.getItem("algocare_uid");
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem("algocare_uid", id);
  }
  return id;
}

// Helper: Get the Name (Logged in user, or Anonymous)
function getUserName() {
  const user = window.getUser ? window.getUser() : null;
  if (user) {
    return user.user_metadata?.name || user.email.split('@')[0];
  }
  return "Anonymous";
}

function getProgram() {
  const segments = window.location.pathname.split("/").filter(Boolean);
  for (const segment of segments) {
    if (["nursing", "midwifery"].includes(segment)) return segment;
  }
  return "nursing";
}

function generateAttemptId() { return crypto.randomUUID(); }

async function logEvent(table, row) {
  try {
    const res = await fetch(`${API_URL}/log-event?table=${table}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(row),
    });

    if (!res.ok) {
      const err = await res.text();
      console.error(`Worker DB Error (${table}):`, err);
    }
  } catch (err) {
    console.warn("Analytics network error:", err);
  }
}

function logTestStarted(attemptId, testType, testIdentifier, questionCount) {
  logEvent("exam_logs", {
    attempt_id: attemptId,
    user_id: getUserId(),
    user_name: getUserName(),
    program: getProgram(),
    event_type: "started",
    test_type: testType,
    test_identifier: testIdentifier,
    question_count: questionCount
  });
}

function logTestFinished(attemptId, testType, testIdentifier, questionCount, attempted, correct) {
  logEvent("exam_logs", {
    attempt_id: attemptId,
    user_id: getUserId(),
    user_name: getUserName(),
    program: getProgram(),
    event_type: "finished",
    test_type: testType,
    test_identifier: testIdentifier,
    question_count: questionCount,
    attempted: attempted,
    correct: correct
  });
}

function logReview(testType, stars, comment) {
  logEvent("feedback", {
    user_id: getUserId(),
    user_name: getUserName(),
    program: getProgram(),
    test_type: testType || null,
    stars: stars,
    comment: comment || null,
  });
}

function logArticleViewed(topicId) {
  logEvent("article_events", {
    user_id: getUserId(),
    user_name: getUserName(),
    program: getProgram(),
    topic_id: topicId,
    event_type: "viewed"
  });
}
