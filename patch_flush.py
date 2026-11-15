from pathlib import Path

bp = Path("scripts/build.py")
src = bp.read_text()

# Replace all print statements with print(..., flush=True)
import re
src = re.sub(r"print\((.*?)\)", r"print(\1, flush=True)", src)

bp.write_text(src)
print("✅ Added flush=True to all print statements")
