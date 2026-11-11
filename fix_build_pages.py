from pathlib import Path

bp = Path("build_pages.py")
src = bp.read_text()

# 1. Replace .format() with .replace() to avoid all KeyError issues
old_render = 'return PAGE_HEAD.format(title=title, rel=rel, root_rel=root_rel, breadcrumb=breadcrumb_html, body=body_html)'
new_render = '''html = PAGE_HEAD.replace("{title}", title)
    html = html.replace("{rel}", rel)
    html = html.replace("{root_rel}", root_rel)
    html = html.replace("{breadcrumb}", breadcrumb_html)
    html = html.replace("{body}", body_html)
    return html'''

if old_render in src:
    src = src.replace(old_render, new_render)
    print("✅ Replaced .format() with .replace()")
else:
    print("ℹ️ render_page already fixed.")

# 2. Replace PAGE_HEAD with a clean version that uses single braces for JS
start = src.find('PAGE_HEAD = """')
end = src.find('"""', start + 15)

new_page_head = '''PAGE_HEAD = """<!DOCTYPE html>
<html lang="en">
<head>
<script>
  (function() {
    const t = localStorage.getItem('algocare_theme') || 'clinical';
    document.documentElement.setAttribute('data-theme', t);
  })();
</script>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Algocare</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<link rel="manifest" href="{root_rel}manifest.webmanifest">
<meta name="theme-color" content="#F7F8F7">
<link rel="icon" href="{root_rel}icon-192x192.png" sizes="192x192">
<link rel="stylesheet" href="{rel}assets/style.css">
<script src="{rel}assets/analytics.js"></script>
</head>
<body>
<div class="topbar">
  <div class="brand"><span class="pulse-dot"></span>Algocare</div>
  <div>
    <a href="{rel}cbt/index.html" style="font-size: 0.85rem; color: var(--scrub); font-weight: 600; margin-right: 16px;">Practice tests</a>
    <a href="{rel}index.html" style="font-size: 0.85rem; color: var(--ink-soft); margin-right: 16px;">Home</a>
    <a href="{root_rel}index.html" style="font-size: 0.85rem; color: var(--ink-soft);">All programs</a>
  </div>
</div>
<div class="container">
{breadcrumb}
{body}
</div>
<div style="text-align: center; margin-top: 40px; padding: 16px 0; font-size: 0.8rem;">
  <a href="{root_rel}privacy.html" style="color: var(--ink-soft); margin-right: 16px;">Privacy Policy</a>
  <a href="{root_rel}terms.html" style="color: var(--ink-soft);">Terms &amp; Disclaimer</a>
</div>
<script>
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("{root_rel}sw.js", { scope: "/" }).catch(() => {});
  });
}
</script>
</body>
</html>
"""'''

if start != -1 and end != -1:
    src = src[:start] + new_page_head + src[end+3:]
    bp.write_text(src)
    print("✅ Replaced PAGE_HEAD with clean single-brace JavaScript")
