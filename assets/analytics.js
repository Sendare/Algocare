
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
const SUPABASE_ANON_KEY = "sb_publishable_C_i1zk4P2phfIALmI6C7Iw_pYSMTGfQ";

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
    await fetch(`${SUPABASE_URL}/rest/v1/${table}`, {
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
