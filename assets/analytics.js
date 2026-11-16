const API_URL = "https://algocare-api.abdul01abdul03.workers.dev";

function getUserId() {
  // If logged in, use Supabase ID. Otherwise, anonymous UUID.
  const user = window.getUser ? window.getUser() : null;
  if (user) return user.id;
  
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
      // Visual error banner
      const debugEl = document.createElement("div");
      debugEl.style.cssText = "position:fixed; bottom:0; left:0; right:0; background:#b14a3a; color:white; padding:16px; z-index:99999; font-family:monospace; font-size:12px; word-wrap:break-word;";
      debugEl.innerHTML = `<strong>DB Save Error (${table}):</strong> ${err}`;
      document.body.appendChild(debugEl);
    }
  } catch (err) {
    console.warn("Analytics network error:", err);
  }
}

function logTestStarted(attemptId, testType, testIdentifier, questionCount) {
  logEvent("exam_logs", {
    attempt_id: attemptId,
    user_id: getUserId(),
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
    program: getProgram(),
    test_type: testType || null,
    stars: stars,
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
