import os
import re
from pathlib import Path

workflows_dir = Path(".github/workflows")
count = 0

for filepath in workflows_dir.glob("*.yml"):
    content = filepath.read_text()
    
    # Remove the schedule/cron block
    # Matches "  schedule:" and everything indented under it until the next top-level key
    new_content = re.sub(r"^\s*schedule:.*?(?=^\s*[a-zA-Z]|$)", "", content, flags=re.MULTILINE | re.DOTALL)
    
    if content != new_content:
        filepath.write_text(new_content)
        print(f"🛑 Removed cron schedule from {filepath.name}")
        count += 1

print(f"\n✅ Done. Disabled cron in {count} workflow(s).")
