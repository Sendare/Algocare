from pathlib import Path

bp = Path("scripts/build.py")
src = bp.read_text()

# 1. Fix the old print statement
src = src.replace('print("🚀 Starting Build (Max 3 minutes)...", flush=True)', 'print("🚀 Starting Full Build...", flush=True)')

# 2. Remove the return that stops the script after Nursing
old_code = """            print(f"  💾 Built {built_count} files this run.", flush=True)
            rebuild_navigation(prog, ctx_lookup)
            print("BATCH_COMPLETE_MORE_REMAINING", flush=True)
            return # Stop processing so Git can commit this batch"""

new_code = """            print(f"  💾 Built {built_count} files for {prog}.", flush=True)
            rebuild_navigation(prog, ctx_lookup)"""

if old_code in src:
    src = src.replace(old_code, new_code)
    bp.write_text(src)
    print("✅ Removed early return so Midwifery builds in the same run")
else:
    print("⚠️ Could not find the exact block. Let me know!")
