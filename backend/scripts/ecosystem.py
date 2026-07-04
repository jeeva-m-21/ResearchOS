#!/usr/bin/env python3
"""
Ecosystem Manager — MCP & Plugin Ecosystem Integration orchestration.

This module is the main entry point for discovering, evaluating, configuring,
validating, and maintaining MCP servers and development plugins.

It integrates with the evolution cycle (learn.py) by providing:
- discover() → called during the OBSERVE phase
- validate() → called during the VALIDATE phase
- evaluate() → called during the ANALYZE phase

Usage:
    docker exec researchos-backend-1 python scripts/ecosystem.py
    docker exec researchos-backend-1 python scripts/ecosystem.py --discover
    docker exec researchos-backend-1 python scripts/ecosystem.py --evaluate
    docker exec researchos-backend-1 python scripts/ecosystem.py --validate
    docker exec researchos-backend-1 python scripts/ecosystem.py --full
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Project root
PROJECT_ROOT = Path(os.environ.get("MEMORY_ROOT", "/app"))
MEMORY_DIR = PROJECT_ROOT / ".opencode" / "memory"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# Import sibling modules
sys.path.insert(0, str(SCRIPTS_DIR))
from discovery import discover_all  # noqa: E402
from evaluator import evaluate_discovery, rank_tools  # noqa: E402
from memory import read_json, write_json  # noqa: E402
from memory import timestamp as _ts  # noqa: E402

# Registry file paths
MCP_REGISTRY_PATH = MEMORY_DIR / "mcp_registry.json"
CAPABILITIES_PATH = MEMORY_DIR / "capabilities.json"


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] [ecosystem] {msg}", file=sys.stderr)


def is_docker() -> bool:
    """Detect if running inside Docker container."""
    return os.path.exists("/.dockerenv")


def discover() -> dict[str, Any]:
    """Run capability discovery and return fresh results."""
    log("Running capability discovery...")
    result = discover_all()

    # Persist to mcp_registry.json
    registry = read_json("mcp_registry.json")
    registry["last_discovered"] = _ts()
    registry["discovery_result"] = result
    registry["discovery_count"] = {
        "mcp_servers": len(result["mcp_servers"]),
        "lsp_servers": len(result["lsp_servers"]),
        "formatters": len(result["formatters"]),
        "linters": len(result["linters"]),
        "test_runners": len(result["test_runners"]),
        "git_hooks": len(result["git_hooks"]),
        "npm_packages": len(result["project_plugins"]["npm"]),
        "pip_packages": len(result["project_plugins"]["pip"]),
    }
    write_json("mcp_registry.json", registry)
    log("Discovery persisted to mcp_registry.json")
    return result


def evaluate(discovery_result: dict[str, Any]) -> dict[str, Any]:
    """Evaluate discovered capabilities and persist to capabilities.json."""
    log("Evaluating capabilities...")
    evaluation = evaluate_discovery(discovery_result)

    # Build capability graph
    capabilities = read_json("capabilities.json")
    capabilities["last_evaluated"] = _ts()
    capabilities["capabilities"] = evaluation["capabilities"]
    capabilities["top_tools"] = evaluation["top_tools"]
    capabilities["ranking"] = rank_tools(evaluation["capabilities"])

    write_json("capabilities.json", capabilities)
    n_caps = len(evaluation["capabilities"])
    log(f"Evaluated {n_caps} capabilities, persisted to capabilities.json")

    return evaluation


def validate() -> dict[str, Any]:
    """Validate that installed capabilities are properly configured and healthy."""
    log("Validating ecosystem...")
    validation: dict[str, Any] = {
        "validated_at": _ts(),
        "status": "healthy",
        "checks": [],
    }

    # Read latest capabilities
    capabilities = read_json("capabilities.json")
    cap_list = capabilities.get("capabilities", [])

    # Check each MCP server
    for cap in cap_list:
        if cap.get("type") != "mcp_server":
            continue
        check: dict[str, Any] = {
            "name": cap["name"],
            "type": "mcp_server",
            "status": "unknown",
        }
        command = cap.get("command")
        if command and isinstance(command, list) and len(command) > 0:
            try:
                # Check if the base command exists
                base_cmd = command[0]
                # For npx/uvx, just check the tool is plausible
                if base_cmd in ("npx", "uvx"):
                    check["status"] = "configured"
                    check["note"] = f"launched via {base_cmd}"
                else:
                    proc = subprocess.run(
                        ["which", base_cmd], capture_output=True, text=True, timeout=5,
                    )
                    check["status"] = "healthy" if proc.returncode == 0 else "missing"
                    check["path"] = (
                        proc.stdout.strip() if proc.returncode == 0 else None
                    )
            except Exception as e:
                check["status"] = "error"
                check["error"] = str(e)
        else:
            check["status"] = "configured"
        validation["checks"].append(check)

    # Determine overall status
    failed = [c for c in validation["checks"] if c["status"] in ("missing", "error")]
    if failed:
        validation["status"] = "degraded"
        validation["issues"] = [
            f"{c['name']}: {c['status']}" for c in failed
        ]
        log(f"Found {len(failed)} issue(s)")
    else:
        log("All capabilities healthy")

    return validation


def full_cycle() -> dict[str, Any]:
    """Run full ecosystem cycle: discover → evaluate → validate."""
    log("=" * 40)
    log("ECOSYSTEM FULL CYCLE")
    log("=" * 40)

    discovery_result = discover()
    evaluation = evaluate(discovery_result)
    validation_result = validate()

    log(f"Cycle complete: {len(evaluation['capabilities'])} capabilities, "
        f"status={validation_result['status']}")

    return {
        "discovery": {"count": discovery_result.get("discovery_count", {})},
        "evaluation": {"count": len(evaluation["capabilities"]),
                       "top": evaluation.get("top_tools", [])},
        "validation": validation_result,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="MCP & Plugin Ecosystem Manager",
    )
    parser.add_argument("--discover", action="store_true", help="Run discovery only")
    parser.add_argument(
        "--evaluate", action="store_true",
        help="Evaluate discovered capabilities",
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="Validate ecosystem health",
    )
    parser.add_argument(
        "--full", action="store_true",
        help="Run full cycle (discover + evaluate + validate)",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Show ecosystem status summary",
    )
    args = parser.parse_args()

    if args.full:
        result = full_cycle()
        print(json.dumps(result, indent=2, default=str))

    elif args.discover:
        result = discover()
        print(json.dumps({
            "mcp_servers": len(result["mcp_servers"]),
            "lsp_servers": len(result["lsp_servers"]),
            "formatters": len(result["formatters"]),
            "linters": len(result["linters"]),
            "project_plugins": {
                "npm": len(result["project_plugins"]["npm"]),
                "pip": len(result["project_plugins"]["pip"]),
            },
        }, indent=2))

    elif args.evaluate:
        registry = read_json("mcp_registry.json")
        discovery_result = registry.get("discovery_result", {})
        if not discovery_result:
            log("No discovery data found. Run --discover first.")
            return
        evaluation = evaluate(discovery_result)
        print(json.dumps({
            "capability_count": len(evaluation["capabilities"]),
            "top_tools": evaluation.get("top_tools", []),
        }, indent=2, default=str))

    elif args.validate:
        result = validate()
        print(json.dumps(result, indent=2))

    elif args.status:
        registry = read_json("mcp_registry.json")
        capabilities = read_json("capabilities.json")
        print("=== Ecosystem Status ===")
        last_disc = registry.get("last_discovered", "never")
        print(f"Last discovered: {last_disc}")
        disc_count = registry.get("discovery_count", {})
        print(f"Discovery count: {json.dumps(disc_count, indent=2)}")
        print(f"Capabilities evaluated: {len(capabilities.get('capabilities', []))}")
        print(f"Last evaluated: {capabilities.get('last_evaluated', 'never')}")
        top = capabilities.get("top_tools", [])
        if top:
            print("\nTop tools:")
            for t in top[:5]:
                print(f"  {t['name']} ({t['type']}): {t['score']}")
    else:
        # Default: show status
        registry = read_json("mcp_registry.json")
        if registry.get("last_discovered"):
            print("Ecosystem has been initialized.")
            print(f"  Last discovered: {registry['last_discovered']}")
            print("  Run with --full to refresh")
        else:
            print("Ecosystem not yet initialized. Run:")
            print("  python scripts/ecosystem.py --full")


if __name__ == "__main__":
    main()
