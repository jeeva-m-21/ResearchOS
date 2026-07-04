#!/usr/bin/env python3
"""
Evolution Cycle — Continuous Reinforcement Learning & Autonomous Evolution.

This script implements the evolution cycle that runs after every completed task:

Observe → Analyze → Plan → Implement → Validate → Reflect → Learn → Persist

It reads from and writes to .opencode/memory/, collects observations from
the repository, and generates improvement proposals.

Usage:
    docker exec researchos-backend-1 python scripts/learn.py
    docker exec researchos-backend-1 python scripts/learn.py --cycle
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Project root (inside container: /app)
PROJECT_ROOT = Path(os.environ.get("MEMORY_ROOT", "/app"))
MEMORY_DIR = PROJECT_ROOT / ".opencode" / "memory"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Import memory utilities
sys.path.insert(0, str(SCRIPTS_DIR))
from memory import (  # noqa: E402
    append_entry,
    git_log,
    read_json,
    timestamp,
    update_metrics,
)


def observe() -> dict[str, Any]:
    """Phase 1: Collect observations from the repository."""
    log("=== OBSERVE ===")

    observations: dict[str, Any] = {
        "timestamp": timestamp(),
        "git": [],
        "tests": {"pass": 0, "fail": 0, "total": 0},
        "ruff": {"errors": 0},
        "mypy": {"errors": 0},
        "files": [],
        "opportunities": [],
    }

    # 1. Git history
    observations["git"] = git_log(max_count=5)

    # 2. Test results
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "/app/tests/", "-q", "--tb=no"],
            capture_output=True, text=True, timeout=120,
        )
        output = result.stdout + result.stderr
        # Parse summary line like "28 passed in 6.90s"
        fail_match = re.search(r"(\d+) failed", output)
        pass_match = re.search(r"(\d+) passed", output)
        observations["tests"]["pass"] = int(pass_match.group(1)) if pass_match else 0
        observations["tests"]["fail"] = int(fail_match.group(1)) if fail_match else 0
        observations["tests"]["total"] = (
            observations["tests"]["pass"] + observations["tests"]["fail"]
        )
        observations["tests"]["output"] = output[-500:] if len(output) > 500 else output
        log(f"Tests: {observations['tests']['pass']} passed, "
            f"{observations['tests']['fail']} failed")
    except Exception as e:
        log(f"Test observation failed: {e}")

    # 3. Ruff
    try:
        result = subprocess.run(
            ["ruff", "check", str(PROJECT_ROOT / "src"), str(PROJECT_ROOT / "tests")],
            capture_output=True, text=True, timeout=30,
        )
        output = result.stdout.strip()
        observations["ruff"]["errors"] = result.returncode
        if output:
            observations["ruff"]["output"] = output
            issue_lines = [ln for ln in output.split(chr(10)) if ln.strip()]
            log(f"Ruff: {len(issue_lines)} issues")
    except Exception as e:
        log(f"Ruff observation failed: {e}")

    # 4. Mypy (on backend src only)
    try:
        result = subprocess.run(
            ["mypy", str(PROJECT_ROOT / "src")],
            capture_output=True, text=True, timeout=60,
        )
        lines = result.stdout.split("\n")
        error_lines = [ln for ln in lines if "error:" in ln.lower() and ln.strip()]
        observations["mypy"]["errors"] = len(error_lines)
        if error_lines:
            observations["mypy"]["output"] = "\n".join(error_lines[:20])
            log(f"Mypy: {len(error_lines)} errors")
    except Exception as e:
        log(f"Mypy observation failed: {e}")

    log("Observation complete")
    return observations


def analyze(observations: dict[str, Any]) -> dict[str, Any]:
    """Phase 2: Analyze observations for patterns and issues."""
    log("=== ANALYZE ===")

    analysis: dict[str, Any] = {
        "timestamp": timestamp(),
        "issues": [],
        "patterns": [],
        "improvements": [],
    }

    # Check for test failures
    if observations["tests"]["fail"] > 0:
        analysis["issues"].append({
            "severity": "high",
            "category": "test_failure",
            "detail": f"{observations['tests']['fail']} tests failed",
            "count": observations["tests"]["fail"],
        })

    # Check for lint errors
    if observations["ruff"]["errors"] > 0:
        output = observations["ruff"].get("output", "")
        # Count unique error codes
        codes = set(re.findall(r"([A-Z]\d+)", output))
        analysis["issues"].append({
            "severity": "medium",
            "category": "lint_error",
            "detail": f"{' '.join(codes)} issues found",
            "count": len(codes),
        })

    # Check for type errors
    if observations["mypy"]["errors"] > 0:
        analysis["issues"].append({
            "severity": "medium",
            "category": "type_error",
            "detail": f"{observations['mypy']['errors']} mypy errors",
            "count": observations["mypy"]["errors"],
        })

    # Report findings
    if analysis["issues"]:
        log(f"Found {len(analysis['issues'])} issue(s)")
        for issue in analysis["issues"]:
            log(f"  [{issue['severity']}] {issue['detail']}")
    else:
        log("No issues found — clean")

    return analysis


def plan_improvements(
    analysis: dict[str, Any], observations: dict[str, Any],
) -> list[dict[str, Any]]:
    """Phase 3: Generate improvement proposals."""
    log("=== PLAN ===")

    proposals: list[dict[str, Any]] = []
    now = timestamp()

    # Auto-fix ruff issues
    if observations["ruff"]["errors"] > 0:
        proposals.append({
            "type": "auto_fix_ruff",
            "priority": 80,
            "command": ["ruff", "check", "--fix",
                        str(PROJECT_ROOT / "src"),
                        str(PROJECT_ROOT / "tests")],
            "description": "Auto-fix ruff issues",
            "rollback": "git checkout -- .",
        })

    # Check if backend test and SDK test paths conflict
    tests_dir = PROJECT_ROOT / "tests"
    if tests_dir.exists():
        files = list(tests_dir.glob("*.py"))
        sync_test = [f for f in files if "test_sync" in f.name or "test_wal" in f.name]
        if len(sync_test) > 0:
            # Check if they import from researchos (SDK tests in backend dir)
            for f in sync_test:
                content = f.read_text()
                if "from researchos" in content:
                    proposals.append({
                        "type": "opportunity",
                        "priority": 40,
                        "description": f"SDK test {f.name} lives in backend tests/ —"
                                       " consider moving to sdk/python/tests/",
                        "command": None,
                        "rollback": None,
                    })
                    break

    # Persist proposals
    for p in proposals:
        if p["command"] is not None:
            append_entry("improvements.json", {
                "id": f"P-{now[:10]}-{len(proposals)}",
                "problem": p["description"],
                "expected_benefit": "Cleaner code quality",
                "implementation_cost": "low",
                "risk": "low",
                "rollback_strategy": p.get("rollback", ""),
                "priority_score": p["priority"],
                "status": "pending",
                "evidence": observations.get("ruff", {}).get("output", ""),
            })

    log(f"Generated {len(proposals)} proposal(s)")
    return proposals


def implement(proposals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Phase 4: Apply high-confidence, low-risk improvements."""
    log("=== IMPLEMENT ===")

    results: list[dict[str, Any]] = []
    for proposal in proposals:
        if proposal["command"] is None:
            results.append({"proposal": proposal["description"], "status": "skipped"})
            continue

        log(f"Applying: {proposal['description']}")
        try:
            result = subprocess.run(
                proposal["command"],
                capture_output=True, text=True, timeout=60,
            )
            success = result.returncode == 0
            results.append({
                "proposal": proposal["description"],
                "status": "applied" if success else "failed",
                "output": (result.stdout + result.stderr)[-300:],
            })
            if success:
                log("  Applied successfully")
            else:
                log(f"  Failed: {result.stderr[:200]}")
        except Exception as e:
            results.append({
                "proposal": proposal["description"],
                "status": "error",
                "error": str(e),
            })
            log(f"  Error: {e}")

    return results


def validate(observations: dict[str, Any]) -> dict[str, Any]:
    """Phase 5: Re-run quality gates to validate changes."""
    log("=== VALIDATE ===")

    validation: dict[str, Any] = {"passed": True, "checks": {}}

    # Re-run tests
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "/app/tests/", "-q", "--tb=short"],
            capture_output=True, text=True, timeout=120,
        )
        output = result.stdout + result.stderr
        fail_match = re.search(r"(\d+) failed", output)
        error_match = re.search(r"(\d+) error", output)
        failures = int(fail_match.group(1)) if fail_match else 0
        errors = int(error_match.group(1)) if error_match else 0
        validation["checks"]["tests"] = {
            "passed": failures == 0 and errors == 0,
            "failures": failures,
            "errors": errors,
        }
        if not validation["checks"]["tests"]["passed"]:
            validation["passed"] = False
        log(f"Tests: {failures} failed, {errors} errors")
    except Exception as e:
        validation["checks"]["tests"] = {"passed": False, "error": str(e)}
        validation["passed"] = False
        log(f"Test validation error: {e}")

    return validation


def reflect(
    observations: dict[str, Any], analysis: dict[str, Any],
    validation: dict[str, Any],
) -> dict[str, Any]:
    """Phase 6: Generate reflection report."""
    log("=== REFLECT ===")

    report: dict[str, Any] = {
        "timestamp": timestamp(),
        "what_was_accomplished": [],
        "what_failed": [],
        "what_was_learned": [],
        "what_can_improve": [],
    }

    # What was accomplished
    report["what_was_accomplished"].append("Evolution cycle executed")

    # What failed
    if validation.get("checks", {}).get("tests", {}).get("failed"):
        report["what_failed"].append("Tests failed during validation")

    # What was learned
    if analysis.get("issues"):
        report["what_was_learned"].append(
            f"Found {len(analysis['issues'])} issues during analysis"
        )

    # What can improve
    report["what_can_improve"].append("Add coverage tracking to evolution cycle")
    report["what_can_improve"].append("Automate prompt scoring based on success rate")

    return report


def learn(report: dict[str, Any], observations: dict[str, Any]) -> None:
    """Phase 7: Persist learned knowledge."""
    log("=== LEARN ===")

    # Persist reflection report
    append_entry("improvements.json", {
        "id": f"R-{timestamp()[:10]}",
        "type": "reflection",
        "report": report,
        "observations_summary": {
            "tests": observations.get("tests", {}),
            "ruff": observations.get("ruff", {}).get("errors"),
            "mypy": observations.get("mypy", {}).get("errors"),
        },
    })

    # Update metrics
    update_metrics()
    log("Metrics updated")

    # Update STATE.md
    state_path = PROJECT_ROOT / ".opencode" / "tasks" / "STATE.md"
    if state_path.exists():
        content = state_path.read_text()
        evolution_note = (
            f"- {timestamp()[:10]}: Evolution cycle completed."
        )
        if evolution_note not in content:
            # Add after the last log entry
            content = content.rstrip() + f"\n{evolution_note}\n"
            state_path.write_text(content)
        log("STATE.md updated")

    log("Learning persisted")


def persist() -> None:
    """Phase 8: Ensure all memory changes are written to disk."""
    log("=== PERSIST ===")
    # Memory files are already written by append_entry / write_json
    # This phase ensures sync
    mem_files = list(MEMORY_DIR.glob("*"))
    log(f"Memory directory contains {len(mem_files)} file(s)")
    for f in mem_files:
        log(f"  {f.name}: {f.stat().st_size} bytes")


def log(msg: str) -> None:
    """Log with timestamp."""
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] {msg}")


def run_cycle() -> dict[str, Any]:
    """Run the full evolution cycle.

    Observe → Analyze → Plan → Implement → Validate → Reflect → Learn → Persist.
    """
    log("=" * 50)
    log("EVOLUTION CYCLE START")
    log("=" * 50)

    observations = observe()
    analysis = analyze(observations)
    proposals = plan_improvements(analysis, observations)
    impl_results = implement(proposals)
    validation = validate(observations)
    report = reflect(observations, analysis, validation)
    learn(report, observations)
    persist()

    log("=" * 50)
    log("EVOLUTION CYCLE COMPLETE")
    log("=" * 50)

    return {
        "observations": observations,
        "analysis": analysis,
        "proposals": proposals,
        "implemented": impl_results,
        "validation": validation,
        "report": report,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evolution Cycle Runner")
    parser.add_argument("--cycle", action="store_true", help="Run full evolution cycle")
    parser.add_argument(
        "--observe", action="store_true", help="Run observation phase only",
    )
    args = parser.parse_args()

    if args.cycle:
        result = run_cycle()
        print(json.dumps(result["validation"], indent=2))
    elif args.observe:
        observations = observe()
        print(json.dumps(observations, indent=2, default=str))
    else:
        # Default: show summary of current state
        metrics = read_json("metrics.json")
        print("=== ResearchOS Evolution Cycle ===")
        print(f"Latest metrics: {json.dumps(metrics.get('latest', {}), indent=2)}")
        print(f"History entries: {len(metrics.get('history', []))}")
        print()
        print("Usage:")
        print("  python scripts/learn.py --cycle    Run full evolution cycle")
        print("  python scripts/learn.py --observe  Run observation phase only")


if __name__ == "__main__":
    main()
