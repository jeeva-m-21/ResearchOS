"""
Discovery — Capability and plugin discovery scanner.

Scans for:
- MCP servers configured in opencode.json
- Language servers (LSP) available in the environment
- Project plugins (npm packages, pip packages, git hooks)
- Development tools (formatters, linters, test runners, build systems)
- Docker, system tools
"""

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

# Discovered capability categories (maps to the categories in the spec)
CAPABILITY_CATEGORIES = [
    "core_development",
    "source_control",
    "documentation",
    "web_intelligence",
    "browser_automation",
    "database",
    "cloud",
    "observability",
    "productivity",
    "research",
]

# Tool name patterns for discovery
LSP_SERVERS = [
    "pyright", "pylsp", "mypy", "ruff", "typescript-language-server",
    "typescript-language-server-fork", "vscode-typescript-language-server",
    "rust-analyzer", "gopls", "clangd", "taplo", "docker-langserver",
    "yamlls", "json-language-server", "helm-ls", "sql-language-server",
]

FORMATTERS = [
    "ruff", "black", "isort", "prettier", "rustfmt", "gofmt",
    "shfmt", "stylua", "deno fmt",
]

LINTERS = [
    "ruff", "mypy", "pylint", "flake8", "eslint", "prettier",
    "rustfmt", "clippy", "shellcheck", "hadolint",
]

TEST_RUNNERS = [
    "pytest", "unittest", "vitest", "jest", "mocha", "cargo test", "go test",
]

BUILD_SYSTEMS = [
    "make", "cmake", "cargo", "go build", "tsc", "webpack", "vite", "next build",
]

GIT_HOOKS = ["pre-commit", "commit-msg", "pre-push", "prepare-commit-msg"]

def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{ts}] [discovery] {msg}", file=sys.stderr)


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _check_command(name: str) -> dict[str, Any]:
    """Check if a command-line tool is available and get its version."""
    result: dict[str, Any] = {
        "name": name, "available": False, "version": None, "path": None,
    }
    try:
        proc = subprocess.run(
            ["which", name], capture_output=True, text=True, timeout=5,
        )
        if proc.returncode == 0:
            result["available"] = True
            result["path"] = proc.stdout.strip()
            # Try to get version
            for flag in ["--version", "-V", "version"]:
                try:
                    vproc = subprocess.run(
                        [name, flag], capture_output=True, text=True, timeout=5,
                    )
                    out = (vproc.stdout + vproc.stderr).strip()
                    if out:
                        result["version"] = out.split("\n")[0][:100]
                        break
                except Exception:
                    continue
    except Exception:
        pass
    return result


def _check_npx_module(name: str) -> dict[str, Any]:
    """Check if an npx-installable module is available."""
    result: dict[str, Any] = {"name": name, "available": False, "version": None}
    try:
        proc = subprocess.run(
            ["npx", "--yes", name, "--version"],
            capture_output=True, text=True, timeout=15,
        )
        out = (proc.stdout + proc.stderr).strip()
        result["available"] = proc.returncode == 0
        if out:
            result["version"] = out.split("\n")[0][:100]
    except Exception:
        pass
    return result


def discover_mcp_servers() -> list[dict[str, Any]]:
    """Discover MCP servers configured in opencode.json."""
    log("Discovering MCP servers...")
    servers: list[dict[str, Any]] = []
    opencode_path = PROJECT_ROOT / "opencode.json"
    if not opencode_path.exists():
        log("opencode.json not found")
        return servers

    try:
        config = json.loads(opencode_path.read_text())
        mcp_config = config.get("mcp", {})
        for name, cfg in mcp_config.items():
            server: dict[str, Any] = {
                "name": name,
                "type": cfg.get("type", "unknown"),
                "enabled": cfg.get("enabled", False),
                "command": cfg.get("command"),
                "url": cfg.get("url"),
                "timeout": cfg.get("timeout"),
                "discovered_at": timestamp(),
                "health": "unknown",
                "categories": _classify_mcp_server(name, cfg),
            }
            # Check if the command is available
            if cfg.get("type") == "local" and cfg.get("command"):
                cmd = cfg["command"]
                if isinstance(cmd, list) and len(cmd) > 0:
                    tool = cmd[0].replace("npx", "").replace("uvx", "").strip()
                    if tool:
                        result = (
                            _check_command(tool)
                            if tool != "npx" else {"available": True}
                        )
                        server["command_available"] = result.get("available", False)
            servers.append(server)
        log(f"Found {len(servers)} MCP server(s)")
    except Exception as e:
        log(f"Error reading opencode.json: {e}")
    return servers


def _classify_mcp_server(name: str, cfg: dict[str, Any]) -> list[str]:
    """Classify an MCP server by capability category."""
    name_lower = name.lower()
    cmd_str = str(cfg.get("command", "")).lower() + str(cfg.get("url", "")).lower()

    categories = []

    # Core development
    if any(kw in cmd_str for kw in ["filesystem", "git", "shell", "docker", "github"]):
        categories.append("core_development")
    if "context7" in cmd_str or "docs" in cmd_str:
        categories.append("documentation")
    if "playwright" in name_lower or "browser" in cmd_str:
        categories.append("browser_automation")
    if "postgres" in name_lower or "database" in cmd_str or "sql" in cmd_str:
        categories.append("database")
    if "sequential" in name_lower or "thinking" in name_lower:
        categories.append("core_development")
    if "github" in name_lower:
        categories.append("source_control")
    if "web" in cmd_str or "fetch" in cmd_str or "search" in cmd_str:
        categories.append("web_intelligence")

    if not categories:
        categories.append("core_development")

    return categories


def discover_lsp_servers() -> list[dict[str, Any]]:
    """Discover available LSP servers in the environment."""
    log("Discovering LSP servers...")
    servers: list[dict[str, Any]] = []
    for name in LSP_SERVERS:
        result = _check_command(name)
        if result["available"]:
            servers.append(result)
    log(f"Found {len(servers)} LSP server(s)")
    return servers


def discover_formatters() -> list[dict[str, Any]]:
    """Discover available code formatters."""
    log("Discovering formatters...")
    formatters: list[dict[str, Any]] = []
    for name in FORMATTERS:
        result = _check_command(name)
        if result["available"]:
            formatters.append(result)
    return formatters


def discover_linters() -> list[dict[str, Any]]:
    """Discover available linters."""
    log("Discovering linters...")
    linters: list[dict[str, Any]] = []
    for name in LINTERS:
        result = _check_command(name)
        if result["available"]:
            linters.append(result)
    return linters


def discover_test_runners() -> list[dict[str, Any]]:
    """Discover available test runners."""
    log("Discovering test runners...")
    runners: list[dict[str, Any]] = []
    for name in TEST_RUNNERS:
        result = _check_command(name.split()[0])
        if result["available"]:
            runners.append(result)
    return runners


def discover_git_hooks() -> list[dict[str, Any]]:
    """Discover installed git hooks."""
    log("Discovering git hooks...")
    hooks: list[dict[str, Any]] = []
    git_hooks_dir = PROJECT_ROOT / ".git" / "hooks"
    if git_hooks_dir.exists():
        for hook_name in GIT_HOOKS:
            hook_path = git_hooks_dir / hook_name
            if hook_path.exists() and os.access(str(hook_path), os.X_OK):
                hooks.append({
                    "name": hook_name,
                    "path": str(hook_path),
                    "available": True,
                })
    return hooks


def discover_project_plugins() -> dict[str, Any]:
    """Discover plugins from package.json and pyproject.toml."""
    log("Discovering project plugins...")
    plugins: dict[str, Any] = {"npm": [], "pip": [], "git": []}

    # NPM packages
    package_json = PROJECT_ROOT / "package.json"
    if package_json.exists():
        try:
            pkg = json.loads(package_json.read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            for name, ver in deps.items():
                plugins["npm"].append({"name": name, "version": ver})
        except Exception as e:
            log(f"Error reading package.json: {e}")

    # Check .opencode/package.json too
    opencode_pkg = PROJECT_ROOT / ".opencode" / "package.json"
    if opencode_pkg.exists():
        try:
            pkg = json.loads(opencode_pkg.read_text())
            deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
            for name, ver in deps.items():
                # Deduplicate
                if not any(p["name"] == name for p in plugins["npm"]):
                    plugins["npm"].append({"name": name, "version": ver})
        except Exception:
            pass

    log(f"Found {len(plugins['npm'])} npm package(s)")

    # pip packages
    for req_file in ["requirements.txt", "requirements-dev.txt"]:
        req_path = PROJECT_ROOT / req_file
        if req_path.exists():
            for line in req_path.read_text().split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    parts = re.split(r"[=<>~!]", line, maxsplit=1)
                    pkg_name = parts[0].strip()
                    pkg_ver = parts[1].strip() if len(parts) > 1 else "*"
                    plugins["pip"].append({
                        "name": pkg_name, "version": pkg_ver, "source": req_file,
                    })

    # pyproject.toml
    pyproject = PROJECT_ROOT / "pyproject.toml"
    if pyproject.exists():
        content = pyproject.read_text()
        # Simple TOML parsing for dependencies
        for match in re.finditer(
            r'(?:dependencies|dev-dependencies|optional-dependencies)\s*=\s*\[(.*?)\]',
            content, re.DOTALL,
        ):
            block = match.group(1)
            for dep_match in re.finditer(r'"([^"]+)"', block):
                dep = dep_match.group(1)
                parts = re.split(r"[=<>~!]", dep, maxsplit=1)
                pkg_name = parts[0].strip()
                if not any(p["name"] == pkg_name for p in plugins["pip"]):
                    pkg_ver = parts[1].strip() if len(parts) > 1 else "*"
                    plugins["pip"].append({
                        "name": pkg_name, "version": pkg_ver,
                        "source": "pyproject.toml",
                    })

    log(f"Found {len(plugins['pip'])} pip package(s)")
    return plugins


def discover_python_tools() -> dict[str, Any]:
    """Check Python development tools available in the environment."""
    log("Discovering Python tools...")
    tools: dict[str, Any] = {}
    for name in ["python", "pip", "pytest", "ruff", "mypy", "black", "isort"]:
        tools[name] = _check_command(name)
    return tools


def discover_all() -> dict[str, Any]:
    """Run all discovery scanners and return combined results."""
    log("=" * 40)
    log("FULL CAPABILITY DISCOVERY")
    log("=" * 40)

    result: dict[str, Any] = {
        "discovered_at": timestamp(),
        "mcp_servers": discover_mcp_servers(),
        "lsp_servers": discover_lsp_servers(),
        "formatters": discover_formatters(),
        "linters": discover_linters(),
        "test_runners": discover_test_runners(),
        "git_hooks": discover_git_hooks(),
        "project_plugins": discover_project_plugins(),
        "python_tools": discover_python_tools(),
    }

    log(f"Discovery complete: "
        f"{len(result['mcp_servers'])} MCP, "
        f"{len(result['lsp_servers'])} LSP, "
        f"{len(result['formatters'])} formatters, "
        f"{len(result['linters'])} linters, "
        f"{len(result['test_runners'])} test runners, "
        f"{len(result['git_hooks'])} git hooks, "
        f"{len(result['project_plugins']['npm'])} npm + "
        f"{len(result['project_plugins']['pip'])} pip packages")

    return result


if __name__ == "__main__":
    import json as _json
    result = discover_all()
    print(_json.dumps(result, indent=2, default=str))
