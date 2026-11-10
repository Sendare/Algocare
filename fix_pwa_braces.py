#!/usr/bin/env python3
"""Fix: literal braces in PAGE_HEAD SW block break .format(); also utcnow deprecation."""
from pathlib import Path

bp = Path("build_pages.py")
src = bp.read_text()

broken = '''<script>
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("{root_rel}sw.js", { scope: "/" }).catch(() => {});
  });
}
</script>'''

fixed = '''<script>
if ("serviceWorker" in navigator) {{
  window.addEventListener("load", () => {{
    navigator.serviceWorker.register("{root_rel}sw.js", {{ scope: "/" }}).catch(() => {{}});
  }});
}}
</script>'''

if broken in src:
    src = src.replace(broken, fixed, 1)
    print("✅ Escaped braces in PAGE_HEAD SW block")
elif fixed in src:
    print("ℹ️  PAGE_HEAD already escaped")
else:
    print("⚠️  SW block not found — manual check needed")

if "datetime.datetime.utcnow()" in src:
    src = src.replace(
        "datetime.datetime.utcnow()",
        "datetime.datetime.now(datetime.timezone.utc)", 1)
    print("✅ Fixed utcnow() deprecation")

bp.write_text(src)
