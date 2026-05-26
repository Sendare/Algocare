"""
utils/file_store.py
Abstracts all file read/write operations.
Phase 1: local JSON files in Termux.
Phase 2: swap to GitHub API by changing this file only — nothing else changes.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Any, Optional

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import utils.logger as logger

ENGINE = "FileStore"


def read_json(path: Path) -> Optional[Any]:
    """Read and return parsed JSON from a file. Returns None on failure."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning(ENGINE, f"File not found: {path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(ENGINE, f"JSON parse error in {path}: {e}")
        return None
    except Exception as e:
        logger.error(ENGINE, f"Unexpected read error for {path}: {e}")
        return None


def write_json(path: Path, data: Any, indent: int = 2) -> bool:
    """Write data as JSON to a file. Creates parent dirs if needed."""
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(ENGINE, f"Write error for {path}: {e}")
        return False


def append_to_list(path: Path, item: Any) -> bool:
    """Read existing JSON list, append item, write back."""
    existing = read_json(path)
    if existing is None:
        existing = []
    if not isinstance(existing, list):
        logger.error(ENGINE, f"Expected list in {path}, got {type(existing)}")
        return False
    existing.append(item)
    return write_json(path, existing)


def list_json_files(directory: Path) -> list:
    """Return sorted list of all .json files in a directory."""
    directory = Path(directory)
    if not directory.exists():
        return []
    return sorted(directory.glob("*.json"))


def timestamped_filename(prefix: str, ext: str = "json") -> str:
    """Generate a filename like: PREFIX_20260525_143022.json"""
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}.{ext}"
