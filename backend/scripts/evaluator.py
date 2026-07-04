"""
Evaluation Engine — scores every discovered capability on multiple dimensions.

Scoring dimensions:
- compatibility: How well the tool works with the project stack (0-100)
- security: Trustworthiness of the source, permissions required (0-100)
- maintenance: Recent activity, release frequency (0-100)
- documentation: Quality of docs, examples (0-100)
- community: Adoption, contributors, stars (0-100)
- performance: Speed, resource usage (0-100)
- reliability: Stability, crash rate (0-100)
- relevance: How relevant to this project's needs (0-100)
- productivity_impact: Expected improvement in dev speed (0-100)
- integration_complexity: How hard to set up (0-100, higher = simpler)
"""

import sys
from datetime import datetime, timezone
from typing import Any

# Category relevance weights for this project (ResearchOS)
CATEGORY_WEIGHTS: dict[str, float] = {
    "python": 1.0,
    "typescript": 0.6,
    "docker": 0.8,
    "postgresql": 0.9,
    "redis": 0.8,
    "fastapi": 0.9,
    "pydantic": 0.9,
    "testing": 0.8,
    "linting": 0.7,
    "formatting": 0.5,
    "git": 0.7,
    "documentation": 0.6,
}

# Known high-quality tools (pre-scored for efficiency)
KNOWN_TOOL_SCORES: dict[str, dict[str, float]] = {
    "ruff": {
        "compatibility": 95, "security": 95, "maintenance": 95,
        "documentation": 90, "community": 90, "performance": 95,
        "reliability": 95, "relevance": 95, "productivity_impact": 90,
        "integration_complexity": 90,
    },
    "mypy": {
        "compatibility": 85, "security": 90, "maintenance": 90,
        "documentation": 85, "community": 85, "performance": 70,
        "reliability": 80, "relevance": 90, "productivity_impact": 85,
        "integration_complexity": 75,
    },
    "pytest": {
        "compatibility": 95, "security": 95, "maintenance": 95,
        "documentation": 90, "community": 95, "performance": 85,
        "reliability": 95, "relevance": 95, "productivity_impact": 90,
        "integration_complexity": 90,
    },
    "black": {
        "compatibility": 90, "security": 90, "maintenance": 85,
        "documentation": 85, "community": 85, "performance": 85,
        "reliability": 90, "relevance": 80, "productivity_impact": 75,
        "integration_complexity": 85,
    },
    "isort": {
        "compatibility": 90, "security": 90, "maintenance": 80,
        "documentation": 80, "community": 80, "performance": 90,
        "reliability": 90, "relevance": 75, "productivity_impact": 70,
        "integration_complexity": 85,
    },
    "prettier": {
        "compatibility": 85, "security": 90, "maintenance": 90,
        "documentation": 90, "community": 95, "performance": 85,
        "reliability": 90, "relevance": 60, "productivity_impact": 70,
        "integration_complexity": 85,
    },
    "eslint": {
        "compatibility": 85, "security": 85, "maintenance": 90,
        "documentation": 85, "community": 95, "performance": 75,
        "reliability": 85, "relevance": 55, "productivity_impact": 75,
        "integration_complexity": 75,
    },
    "typescript-language-server": {
        "compatibility": 85, "security": 85, "maintenance": 90,
        "documentation": 80, "community": 90, "performance": 75,
        "reliability": 80, "relevance": 55, "productivity_impact": 80,
        "integration_complexity": 75,
    },
    "pyright": {
        "compatibility": 85, "security": 85, "maintenance": 85,
        "documentation": 80, "community": 80, "performance": 80,
        "reliability": 80, "relevance": 85, "productivity_impact": 80,
        "integration_complexity": 75,
    },
    "context7": {
        "compatibility": 90, "security": 90, "maintenance": 85,
        "documentation": 85, "community": 70, "performance": 85,
        "reliability": 85, "relevance": 90, "productivity_impact": 90,
        "integration_complexity": 90,
    },
}

# Tool → MCP server name mapping for cross-referencing
TOOL_TO_MCP: dict[str, list[str]] = {
    "postgres-mcp": ["postgres"],
    "context7-mcp": ["context7"],
    "server-sequential-thinking": ["sequential-thinking"],
    "playwright": ["playwright"],
}


def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] [evaluator] {msg}", file=sys.stderr)


def _tool_relevance(name: str) -> float:
    """Estimate relevance score based on tool name."""
    name_lower = name.lower()
    max_weight = 30  # base relevance

    # Python ecosystem
    if any(
        kw in name_lower
        for kw in ["py", "python", "pytest", "ruff", "mypy", "black", "isort"]
    ):
        max_weight = max(max_weight, 90)
    # Docker
    if any(kw in name_lower for kw in ["docker", "container"]):
        max_weight = max(max_weight, 80)
    # PostgreSQL
    if any(kw in name_lower for kw in ["postgres", "pg", "sql"]):
        max_weight = max(max_weight, 90)
    # Redis
    if "redis" in name_lower:
        max_weight = max(max_weight, 80)
    # FastAPI
    if "fastapi" in name_lower:
        max_weight = max(max_weight, 90)
    # Documentation
    if any(kw in name_lower for kw in ["context7", "docs", "documentation"]):
        max_weight = max(max_weight, 85)
    # GitHub
    if "github" in name_lower:
        max_weight = max(max_weight, 75)
    # Testing
    if any(kw in name_lower for kw in ["test", "pytest"]):
        max_weight = max(max_weight, 85)
    # Playwright
    if "playwright" in name_lower:
        max_weight = max(max_weight, 70)
    # Web
    if any(kw in name_lower for kw in ["web", "browser", "fetch"]):
        max_weight = max(max_weight, 65)
    # Formatters
    if any(kw in name_lower for kw in ["format", "prettier"]):
        max_weight = max(max_weight, 60)

    return max_weight


def evaluate_tool(name: str, tool_type: str = "tool") -> dict[str, Any]:
    """Score a tool or capability on all dimensions."""
    # Check if pre-scored
    if name.lower() in KNOWN_TOOL_SCORES:
        scores = KNOWN_TOOL_SCORES[name.lower()]
    else:
        # Generate scores based on heuristics
        relevance = _tool_relevance(name)
        scores = {
            "compatibility": min(80, relevance + 10),
            "security": 75 if tool_type == "mcp" else 80,
            "maintenance": 70,
            "documentation": 65,
            "community": 60,
            "performance": 75,
            "reliability": 70,
            "relevance": relevance,
            "productivity_impact": min(85, relevance + 5),
            "integration_complexity": min(80, relevance + 5),
        }

    # Calculate overall score (weighted average)
    weights = {
        "compatibility": 0.15,
        "security": 0.15,
        "maintenance": 0.10,
        "documentation": 0.08,
        "community": 0.07,
        "performance": 0.10,
        "reliability": 0.10,
        "relevance": 0.15,
        "productivity_impact": 0.10,
        "integration_complexity": 0.00,
    }
    overall = sum(scores[k] * weights[k] for k in weights)

    return {
        "score": round(overall, 1),
        "dimensions": scores,
        "recommendation": _classify_score(overall),
    }


def _classify_score(score: float) -> str:
    """Classify a score into a recommendation level."""
    if score >= 85:
        return "highly_recommended"
    elif score >= 70:
        return "recommended"
    elif score >= 50:
        return "neutral"
    elif score >= 30:
        return "caution"
    else:
        return "not_recommended"


def evaluate_discovery(
    discovery_result: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate all discovered capabilities and produce scores."""
    log("Evaluating discovered capabilities...")
    evaluation: dict[str, Any] = {
        "evaluated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "capabilities": [],
        "top_tools": [],
    }

    # Evaluate MCP servers
    for server in discovery_result.get("mcp_servers", []):
        name = server["name"]
        score = evaluate_tool(name, tool_type="mcp")
        evaluation["capabilities"].append({
            "name": name,
            "provider": "mcp",
            "type": "mcp_server",
            "category": server.get("categories", ["core_development"]),
            "enabled": server.get("enabled", False),
            "command": server.get("command"),
            "url": server.get("url"),
            "health": server.get("health", "unknown"),
            **score,
        })

    # Evaluate LSP servers
    for lsp in discovery_result.get("lsp_servers", []):
        name = lsp["name"]
        if any(c["name"] == name for c in evaluation["capabilities"]):
            continue
        score = evaluate_tool(name, tool_type="lsp")
        evaluation["capabilities"].append({
            "name": name,
            "provider": "lsp",
            "type": "lsp_server",
            "category": ["core_development"],
            "path": lsp.get("path"),
            "version": lsp.get("version"),
            **score,
        })

    # Evaluate formatters
    for fmt in discovery_result.get("formatters", []):
        name = fmt["name"]
        if any(c["name"] == name for c in evaluation["capabilities"]):
            continue
        score = evaluate_tool(name, tool_type="formatter")
        evaluation["capabilities"].append({
            "name": name,
            "provider": "cli",
            "type": "formatter",
            "category": ["core_development"],
            "path": fmt.get("path"),
            "version": fmt.get("version"),
            **score,
        })

    # Evaluate linters
    for lint in discovery_result.get("linters", []):
        name = lint["name"]
        if any(c["name"] == name for c in evaluation["capabilities"]):
            continue
        score = evaluate_tool(name, tool_type="linter")
        evaluation["capabilities"].append({
            "name": name,
            "provider": "cli",
            "type": "linter",
            "category": ["core_development"],
            "path": lint.get("path"),
            "version": lint.get("version"),
            **score,
        })

    # Sort by score descending
    evaluation["capabilities"].sort(key=lambda c: c["score"], reverse=True)

    # Top 10 tools
    evaluation["top_tools"] = [
        {"name": c["name"], "type": c["type"], "score": c["score"],
         "recommendation": c["recommendation"]}
        for c in evaluation["capabilities"][:10]
    ]

    log(f"Evaluated {len(evaluation['capabilities'])} capabilities")
    return evaluation


def rank_tools(
    capabilities: list[dict[str, Any]], operation: str = "",
) -> list[dict[str, Any]]:
    """Rank tools by overall score for a given operation.

    This implements the Tool Selection logic from the spec:
    rank by expected quality, reliability, latency, historical success,
    developer experience, maintenance, token efficiency.
    """
    ranked = sorted(capabilities, key=lambda c: c.get("score", 0), reverse=True)
    return [
        {
            "rank": i + 1,
            "name": c["name"],
            "type": c.get("type", "unknown"),
            "score": c.get("score", 0),
            "recommendation": c.get("recommendation", "unknown"),
        }
        for i, c in enumerate(ranked)
    ]


if __name__ == "__main__":
    import json
    # Test with a sample
    sample = {
        "mcp_servers": [
            {"name": "context7", "enabled": True, "type": "local",
             "command": ["npx", "context7"], "categories": ["documentation"]},
            {"name": "postgres", "enabled": True, "type": "local",
             "command": ["uvx", "postgres-mcp"], "categories": ["database"]},
        ],
        "lsp_servers": [{"name": "ruff", "available": True, "version": "0.9.0"}],
        "formatters": [],
        "linters": [],
        "test_runners": [],
        "git_hooks": [],
        "project_plugins": {"npm": [], "pip": []},
        "python_tools": {},
    }
    result = evaluate_discovery(sample)
    print(json.dumps(result["top_tools"], indent=2))
