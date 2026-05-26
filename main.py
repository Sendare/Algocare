"""
Algocare / Asiya — Main Entry Point

Commands:
  python main.py run      → Full auto: generate + publish (used by GitHub Actions)
  python main.py generate → Generate draft only (Termux testing)
  python main.py publish  → Publish next approved post (Termux testing)
  python main.py stats    → Show system stats
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from engines.orchestrator.orchestrator import (
    run_auto_workflow,
    run_generate_workflow,
    run_publish_workflow,
    get_system_stats
)
import utils.logger as logger


def main():
    if len(sys.argv) < 2:
        print("Usage: python main.py [run|generate|publish|stats]")
        sys.exit(1)

    command = sys.argv[1].lower()

    if command == "run":
        # Full automation — used by GitHub Actions
        logger.info("Main", "Starting auto workflow (generate + publish)")
        result = run_auto_workflow()
        status = result.get("status")
        print(f"\nStatus: {status}")
        if result.get("facebook_post_id"):
            print(f"Facebook ID: {result.get('facebook_post_id')}")
        if result.get("caption"):
            print(f"Caption: {result.get('caption')[:100]}")
        # Exit code 1 on failure so GitHub Actions marks the run as failed
        if status == "failed":
            sys.exit(1)

    elif command == "generate":
        logger.info("Main", "Generating draft only")
        result = run_generate_workflow()
        print(f"\nStatus: {result.get('status')}")
        if result.get("caption_preview"):
            print(f"Preview: {result.get('caption_preview')}")

    elif command == "publish":
        logger.info("Main", "Publishing next approved post")
        result = run_publish_workflow()
        print(f"\nStatus: {result.get('status')}")
        if result.get("result", {}).get("facebook_post_id"):
            print(f"Facebook ID: {result['result']['facebook_post_id']}")

    elif command == "stats":
        stats = get_system_stats()
        print("\n=== Algocare System Stats ===")
        print(f"Total published            : {stats['total_published']}")
        print(f"Combinations used (memory) : {stats['memory']['total_combinations_used']}")
        print(f"Recent categories          : {stats['memory']['recent_categories']}")
        print(f"Recent angles              : {stats['memory']['recent_angles']}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
