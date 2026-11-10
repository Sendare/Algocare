#!/usr/bin/env python3
"""One-shot PWA patch for Algocare. Idempotent - safe to re-run."""
import datetime
import json
import shutil
from pathlib import Path

# ---------- 1. Patch build_pages.py ----------
bp = Path("build_pages.py")
src = bp.read_text()

if "write_pwa_files" not in src:
    # add datetime import
    src = src.replace("import time\n", "import time\nimport datetime\n", 1)

    PWA_BLOCK = '''
# ---------- PWA ----------
MANIFEST_JSON = {
    "name": "Algocare \\u2014 Nursing & Midwifery Exam Prep",
    "short_name": "Algocare",
    "description": "Study articles, practice tests, and real-feel exams for Nigerian nursing and midwifery students.",
    "theme_color": "#F7F8F7",
    "background_color": "#F7F8F7",
    "display": "standalone",
    "orientation": "portrait",
    "start_url": "/",
    "scope": "/",
    "icons": [
        {"src": "/icon-192x192.png", "sizes": "192x192", "type": "image/png", "purpose": "any maskable"},
        {"src": "/icon-512x512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable"},
    ],
}

SW_TEMPLATE_PATH = Path("assets/sw-template.js")
ICONS_SRC = Path("assets/icons")


def write_pwa_files():
    """Writes manifest + sw + icons at docs/ root. Safe to run from any program build."""
    docs_root = Path("docs")
    docs_root.mkdir(exist_ok=True)
    save_json(docs_root / "manifest.webmanifest", MANIFEST_JSON)

    build_id = datetime.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    template = SW_TEMPLATE_PATH.read_text()
    write_html(docs_root / "sw.js", template.replace("__BUILD_ID__", build_id))

    if ICONS_SRC.exists():
        for name in ("icon-192x192.png", "icon-512x512.png"):
            src_icon = ICONS_SRC / name
            if src_icon.exists():
                shutil.copy2(src_icon, docs_root / name)
            else:
                print(f"\\u26a0\\ufe0f  Missing {src_icon} - PWA install will fail without it")

    print(f"\\U0001f4f1 Wrote manifest.webmanifest + sw.js (build {build_id})")

'''
    src = src.replace("def _inline_md(text):", PWA_BLOCK + "\ndef _inline_md(text):", 1)

    # inject PWA head links into PAGE_HEAD
    old_head_end = '<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=IBM+Plex+Sans:wght@400;500&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">'
    new_head_end = old_head_end + '''
<link rel="manifest" href="{root_rel}manifest.webmanifest">
<meta name="theme-color" content="#F7F8F7">
<link rel="icon" href="{root_rel}icon-192x192.png" sizes="192x192">'''
    src = src.replace(old_head_end, new_head_end, 1)

    # inject SW registration before </body>
    old_body_end = "</body>\n</html>"
    new_body_end = '''<script>
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("{root_rel}sw.js", { scope: "/" }).catch(() => {});
  });
}
</script>
</body>
</html>'''
    src = src.replace(old_body_end, new_body_end, 1)

    # call write_pwa_files at start of run()
    src = src.replace(
        '    print(f"Program: {PROGRAM}")',
        '    print(f"Program: {PROGRAM}")\n\n    write_pwa_files()',
        1,
    )

    bp.write_text(src)
    print("\u2705 Patched build_pages.py")
else:
    print("\u2139\ufe0f  build_pages.py already patched")


# ---------- 2. Patch docs/index.html (picker) ----------
idx = Path("docs/index.html")
if idx.exists():
    src = idx.read_text()
    changed = False
    if 'rel="manifest"' not in src and "</head>" in src:
        src = src.replace(
            "</head>",
            '<link rel="manifest" href="manifest.webmanifest">\n'
            '<meta name="theme-color" content="#F7F8F7">\n'
            '<link rel="icon" href="icon-192x192.png" sizes="192x192">\n'
            "</head>",
            1,
        )
        changed = True
    if "serviceWorker" not in src and "</body>" in src:
        src = src.replace(
            "</body>",
            '<script>\n'
            'if ("serviceWorker" in navigator) {\n'
            '  window.addEventListener("load", () => {\n'
            '    navigator.serviceWorker.register("sw.js", { scope: "/" }).catch(() => {});\n'
            '  });\n'
            '}\n'
            "</script>\n</body>",
            1,
        )
        changed = True
    if changed:
        idx.write_text(src)
        print("\u2705 Patched docs/index.html (picker)")
    else:
        print("\u2139\ufe0f  docs/index.html already has PWA markup")
else:
    print("\u26a0\ufe0f  docs/index.html not found - skipping picker patch")

print("\n\U0001f3c1 Done. Next: `python build_pages.py nursing`")
