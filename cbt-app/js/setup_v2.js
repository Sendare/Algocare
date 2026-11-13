
const params = new URLSearchParams(window.location.search);
const quickTopic = params.get("topic");

function showDeviceBanner() {
  if (window.innerWidth < 768) {
    document.getElementById("deviceBanner").innerHTML = `<div class="device-banner">Desktop mode is recommended for the best experience if you're on a mobile device.</div>`;
  }
}

async function init() {
  showDeviceBanner();
  if (quickTopic) {
    window.location.href = `practice.html?topic=${quickTopic}`;
    return;
  }

  const root = document.getElementById("root");
  root.innerHTML = `<div class="empty-state">Loading...</div>`;

  let siteIndex = [];
  let realFeelIndex = { tests: [] };

  try {
    const [siteRes, rfRes] = await Promise.all([
      fetch("../site_index.json"),
      fetch("../data/real_feel_tests/index.json").catch(() => null),
    ]);
    siteIndex = await siteRes.json();
    if (rfRes && rfRes.ok) realFeelIndex = await rfRes.json();
  } catch (err) {
    root.innerHTML = `<div class="empty-state">Couldn't load test data. Try again shortly.</div>`;
    return;
  }

  const courseMap = {};
  siteIndex.forEach(item => { if (!courseMap[item.course_slug]) courseMap[item.course_slug] = item.course; });
  const courseOptions = Object.entries(courseMap).sort((a, b) => a[1].localeCompare(b[1])).map(([slug, name]) => `<option value="${slug}">${name}</option>`).join("");

  const realFeelHtml = realFeelIndex.tests.length
    ? realFeelIndex.tests.map(n => `
        <div class="topic-card">
          <div class="topic-title">Real-Feel Exam ${n}</div>
          <div class="topic-actions"><a href="exam-mode.html?test=${n}">Attempt →</a></div>
        </div>
      `).join("")
    : `<div class="empty-state">No real-feel exams available yet — check back soon.</div>`;

  root.innerHTML = `
    <h1>Practice tests</h1>
    <div class="mode-card">
      <h3>Real-Feel Exam</h3>
      <p>250 questions, timed, no explanations shown — mirrors the real CBT exam experience.</p>
      ${realFeelHtml}
    </div>
    <div class="mode-card">
      <h3>Practice Mode</h3>
      <p>Choose a course, how many questions, and time per question. Explanations and "learn more" links available after each answer.</p>
      <form id="practiceForm">
        <div class="form-row">
          <label>Select Courses (Pick 1 or more)</label>
          <div style="max-height: 150px; overflow-y: auto; background: var(--paper); border: 1px solid var(--grey-line); padding: 8px; border-radius: 6px;">
            ${Object.entries(courseMap).sort((a, b) => a[1].localeCompare(b[1])).map(([slug, name]) => `
              <label style="display: flex; align-items: center; gap: 8px; padding: 6px; font-size: 0.9rem; cursor: pointer;">
                <input type="checkbox" name="courseCheckbox" value="${slug}"> ${name}
              </label>
            `).join("")}
          </div>
        </div>
        <div class="form-row">
          <label>Number of questions</label>
          <input type="number" id="questionCount" min="1" value="20" required>
        </div>
        <div class="form-row">
          <label>Seconds per question</label>
          <select id="secondsPerQuestion"><option value="15">15 seconds</option><option value="30" selected>30 seconds</option><option value="45">45 seconds</option><option value="60">60 seconds</option></select>
        </div>
        <button type="submit" class="btn">Start practice test</button>
      </form>
    </div>
  `;

  document.getElementById("practiceForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const checkboxes = document.querySelectorAll('input[name="courseCheckbox"]:checked');
    if (checkboxes.length === 0) { alert("Please select at least one course."); return; }
    const courses = Array.from(checkboxes).map(cb => cb.value).join(",");
    const count = document.getElementById("questionCount").value;
    const spq = document.getElementById("secondsPerQuestion").value;
    window.location.href = `practice.html?courses=${courses}&count=${count}&spq=${spq}`;
  });
}
init();
