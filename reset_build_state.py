import json
from pathlib import Path

for prog in ["nursing", "midwifery"]:
    p = Path(f"state/{prog}/build_state.json")
    if p.exists():
        data = json.loads(p.read_text())
        data["published_done"] = []
        p.write_text(json.dumps(data, indent=2))
        print(f"♻️  Reset build state for {prog}")
