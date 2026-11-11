from pathlib import Path

print("🚀 Fixing Real-Feel routing, Results theme, and Cache Busting...")

# 1. Overwrite HTML (Ensures real_feel.html loads real_feel.js)
practice_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="theme-color" content="#09090b">
<title>Algocare — Exam</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="../assets/style.css">
<link rel="stylesheet" href="exam.css?v=5">
</head>
<body class="exam-theme">
<div class="exam-header">
  <div class="exam-header-left">
    <span class="exam-header-title">Algocare CBT</span>
    <span style="font-size:0.75rem; color:#a1a1aa">Practice Mode</span>
  </div>
  <div class="exam-header-right">
    <button class="exam-btn-submit" style="background:#18181b; border:1px solid #27272a; color:#fff" onclick="toggleCalculator()">Calc</button>
    <div class="exam-timer" id="examTimer">--:--</div>
    <button class="exam-btn-submit" onclick="finishTest(true)">Submit</button>
  </div>
</div>
<div id="examRoot" style="display:flex; flex-direction:column; flex:1; overflow:hidden;"></div>

<div id="calcModal" class="calc-modal">
  <div class="calc-header">
    <span>Calculator</span>
    <button class="calc-close" onclick="toggleCalculator()">✕</button>
  </div>
  <div class="calc-display" id="calcDisplay">0</div>
  <div class="calc-grid">
    <button class="calc-btn" onclick="calcInput('7')">7</button>
    <button class="calc-btn" onclick="calcInput('8')">8</button>
    <button class="calc-btn" onclick="calcInput('9')">9</button>
    <button class="calc-btn op" onclick="calcInput('/')">÷</button>
    <button class="calc-btn" onclick="calcInput('4')">4</button>
    <button class="calc-btn" onclick="calcInput('5')">5</button>
    <button class="calc-btn" onclick="calcInput('6')">6</button>
    <button class="calc-btn op" onclick="calcInput('*')">×</button>
    <button class="calc-btn" onclick="calcInput('1')">1</button>
    <button class="calc-btn" onclick="calcInput('2')">2</button>
    <button class="calc-btn" onclick="calcInput('3')">3</button>
    <button class="calc-btn op" onclick="calcInput('-')">-</button>
    <button class="calc-btn" onclick="calcInput('0')">0</button>
    <button class="calc-btn" onclick="calcInput('.')">.</button>
    <button class="calc-btn op" onclick="calcInput('+')">+</button>
    <button class="calc-btn op" onclick="calcInput('C')">C</button>
    <button class="calc-btn eq" onclick="calcInput('=')">=</button>
  </div>
</div>

<script src="../assets/analytics.js"></script>
<script src="js/util.js"></script>
<script src="js/practice.js"></script>
</body>
</html>"""
Path("cbt-app/practice.html").write_text(practice_html)

real_feel_html = practice_html.replace('practice.js', 'real_feel.js').replace('Practice Mode', 'Real-Feel Exam').replace('finishTest(true)', 'finishExam()')
Path("cbt-app/real_feel.html").write_text(real_feel_html)


# 2. Hardcode Light Theme colors in Results JS (Bypasses cache/CSS issues)
for js_file in ["practice.js", "real_feel.js"]:
    path = Path(f"cbt-app/js/{js_file}")
    if not path.exists(): continue
    src = path.read_text()
    
    # Replace variables with hardcoded light theme hex codes
    src = src.replace(
        '<div class="score-summary" style="background: var(--paper); min-height: 100vh; padding: 40px 20px; color: var(--ink);">',
        '<div class="score-summary" style="background: #F7F8F7 !important; min-height: 100vh; padding: 40px 20px; color: #16232E !important;">'
    )
    src = src.replace(
        '<div class="big-score" style="color: var(--ink);">',
        '<div class="big-score" style="color: #16232E !important;">'
    )
    src = src.replace(
        '<div style="color: var(--ink-soft); margin-top: 8px;">',
        '<div style="color: #46545F !important; margin-top: 8px;">'
    )
    src = src.replace(
        '<p style="color: var(--ink-soft); font-size: 0.85rem;">',
        '<p style="color: #46545F !important; font-size: 0.85rem;">'
    )
    path.write_text(src)

# 3. Bump Service Worker Version to force cache clear on user devices
sw_path = Path("assets/sw-template.js")
if sw_path.exists():
    sw = sw_path.read_text()
    sw = sw.replace('`algocare-${BUILD_ID}`', '`algocare-v5-${BUILD_ID}`')
    sw_path.write_text(sw)

print("✅ HTML, JS, and Service Worker updated.")
