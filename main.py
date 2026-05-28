"""
MAIN ENTRY POINT
Routes automated cron workflows and manual operational flags smoothly.
"""

import os
import sys
from pathlib import Path

# Absolute Path Resolution: Force Python to treat the project root folder as a top-level package path
_CURRENT_DIR = Path(__file__).resolve().parent
if str(_CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(_CURRENT_DIR))

import utils.logger as logger
from engines.orchestrator.orchestrator import run_auto_workflow, run_manual_workflow
from engines.publishing.publishing_engine import publish_next_approved, process_comment_queue

def print_help():
    print("""
Algocare Content System CLI Options:
  python main.py run       - Run automated workflow cycle & check comment queues
  python main.py approve   - Run structural drafting workflow
  python main.py publish   - Post next locally approved draft (Termux testing)
    """)

def main():
    if len(sys.argv) < 2:
        print_help()
        return

    cmd = sys.argv[1].strip().lower()

    if cmd == "run":
        logger.info("Main", "Checking comment queue pipeline...")
        try:
            process_comment_queue()
        except Exception as e:
            logger.error("Main", f"Failed to check or execute queue stack item: {e}")

        logger.info("Main", "Starting auto workflow (generate + publish)")
        run_auto_workflow()

    elif cmd == "approve":
        logger.info("Main", "Starting manual/draft strategy preparation engine...")
        run_manual_workflow()

    elif cmd == "publish":
        logger.info("Main", "Executing deployment loop for oldest approved file...")
        result = publish_next_approved()
        print(f"Publish execution output status matrix: {result}")

    else:
        print(f"Unknown system flag command received: {cmd}")
        print_help()

if __name__ == "__main__":
    main()
