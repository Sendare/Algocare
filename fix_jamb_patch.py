from pathlib import Path

p = Path("patches/apply_jamb_ui.py")
src = p.read_text()

# Fix the head_script injection to escape JS braces for Python's .format()
src = src.replace(
"""    head_script = \"\"\"
<script>
  (function() {
    const t = localStorage.getItem('algocare_theme') || 'clinical';
    document.documentElement.setAttribute('data-theme', t);
  })();
</script>\"\"\"""",
"""    head_script = \"\"\"
<script>
  (function() {{
    const t = localStorage.getItem('algocare_theme') || 'clinical';
    document.documentElement.setAttribute('data-theme', t);
  }})();
</script>\"\"\""""
)

p.write_text(src)
print("✅ Fixed patches/apply_jamb_ui.py to escape JS braces")
