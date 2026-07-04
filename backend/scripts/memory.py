"""
Memory — persistent project memory read/write utilities.

This module provides utilities for reading and updating the repository's
persistent memory files at .opencode/memory/. It is designed to run
inside the Docker container alongside the backend.

All operations are append-only: existing data is preserved, new data
is added with timestamps.
"""

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, cast

# Paths — resolve relative to the project root (mounted at /app in container)
PROJECT_ROOT = Path(os.environ.get("MEMORY_ROOT", "/app"))
MEMORY_DIR = PROJECT_ROOT / ".opencode" / "memory"


def _ensure_dir() -> None:
    """Ensure memory directory exists."""
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def timestamp() -> str:
    """Return ISO 8601 UTC timestamp string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_json(name: str) -> dict[str, Any]:
    """Read a JSON memory file. Returns empty dict if missing."""
    path = MEMORY_DIR / name
    if path.exists():
        return cast(dict[str, Any], json.loads(path.read_text()))
    return {"schema_version": "1.0", "entries": []}


def write_json(name: str, data: dict[str, Any]) -> None:
    """Write to a JSON memory file atomically."""
    _ensure_dir()
    path = MEMORY_DIR / name
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(data, indent=2, default=str))
    tmp.replace(path)


def append_entry(name: str, entry: dict[str, Any]) -> None:
    """Append an entry to a JSON memory file's 'entries' list."""
    data = read_json(name)
    if "entries" not in data:
        data["entries"] = []
    if "timestamp" not in entry:
        entry["timestamp"] = timestamp()
    data["entries"].insert(0, entry)  # newest first
    write_json(name, data)


def read_markdown(name: str) -> str:
    """Read a Markdown memory file."""
    path = MEMORY_DIR / name
    if path.exists():
        return path.read_text()
    return ""


def append_markdown(name: str, section: str) -> None:
    """Append a section to a Markdown memory file."""
    _ensure_dir()
    path = MEMORY_DIR / name
    existing = path.read_text() if path.exists() else ""
    with open(path, "a") as f:
        if existing and not existing.endswith("\n\n"):
            f.write("\n\n")
        f.write(section.strip() + "\n")


def git_log(max_count: int = 10) -> list[dict[str, Any]]:
    """Read recent git log entries."""
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={max_count}",
             "--format=%H|%ai|%s"],
            capture_output=True, text=True, cwd=PROJECT_ROOT,
        )
        entries = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue
            parts = line.split("|", 2)
            entries.append({
                "commit": parts[0],
                "date": parts[1] if len(parts) > 1 else "",
                "message": parts[2] if len(parts) > 2 else "",
            })
        return entries
    except Exception:
        return []


def update_metrics(commit: Optional[str] = None) -> dict[str, Any]:
    """Collect and persist current metrics. Returns updated metrics dict."""
    metrics = read_json("metrics.json")

    # Count tests
    test_count = 0
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "--collect-only", "-q", "/app/tests/"],
            capture_output=True, text=True, timeout=30,
        )
        # Parse the summary line like "collected 28 items"
        for line in result.stdout.strip().split("\n"):
            if "collected" in line:
                parts = line.split()
                if parts and parts[0].isdigit():
                    test_count = int(parts[0])
    except Exception:
        pass

    # Ruff errors
    ruff_errors = -1
    try:
        result = subprocess.run(
            ["ruff", "check", "/app/src/", "/app/tests/"],
            capture_output=True, text=True, timeout=30,
        )
        ruff_errors = result.returncode
    except Exception:
        pass

    # Mypy errors
    mypy_errors = -1
    try:
        result = subprocess.run(
            ["mypy", "/app/src/"],
            capture_output=True, text=True, timeout=60,
        )
        errors = [ln for ln in result.stdout.split("\n") if "error:" in ln.lower()]
        errors += [ln for ln in result.stderr.split("\n") if "error:" in ln.lower()]
        mypy_errors = len([e for e in errors if e.strip()])
    except Exception:
        pass

    entry = {
        "date": timestamp()[:10],
        "test_count": test_count,
        "ruff_errors": ruff_errors,
        "mypy_errors": mypy_errors,
        "commit": commit or "",
    }

    # Update latest
    metrics["latest"] = {
        "test_count": test_count,
        "ruff_errors": ruff_errors,
        "mypy_errors": mypy_errors,
    }

    # Append to history (dedup by date)
    history = metrics.get("history", [])
    for i, h in enumerate(history):
        if h.get("date") == entry["date"] and h.get("commit") == entry["commit"]:
            history[i] = {**h, **entry}
            break
    else:
        history.append(entry)

    metrics["history"] = history
    write_json("metrics.json", metrics)
    return metrics


def update_backlog_status(task_id: str, status: str) -> bool:
    """Update a task's status in BACKLOG.md. Returns True if updated."""
    path = PROJECT_ROOT / ".opencode" / "tasks" / "BACKLOG.md"
    if not path.exists():
        return False
    content = path.read_text()
    import re
    pattern = rf"(## {task_id} —.*?\n- status: )\w+"
    if re.search(pattern, content, re.DOTALL):
        content = re.sub(
            pattern,
            rf"\g<1>{status}",
            content,
            count=1,
            flags=re.DOTALL,
        )
        path.write_text(content)
        return True
    return False


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "update-metrics":
        result = update_metrics()
        print(json.dumps(result["latest"], indent=2))
    elif len(sys.argv) > 1 and sys.argv[1] == "backlog-status":
        if len(sys.argv) >= 4:
            ok = update_backlog_status(sys.argv[2], sys.argv[3])
            print(f"Updated: {ok}")
