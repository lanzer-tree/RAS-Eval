"""ClawGuard strict-mode decision and output sanitization for the opencode adapter.

Maps opencode's native tool calls onto ClawGuard's rule engine and resolves the
engine's three-way verdict into a strict allow/block decision. Since we run
headless, both ``DENY`` and the supervised ``APPROVE`` are blocked -- there is no
human to approve, so a supervised operation is treated as a violation.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.defense.clawguard.rules import ActionType, RuleEngine
from src.defense.clawguard.sanitizer import Sanitizer

_RULES_PATH = Path(__file__).resolve().parent / "rules.yaml"

# opencode native tool -> ClawGuard canonical tool name. Tools absent from this
# map (external MCP tools, task, todowrite, ...) are not governed by ClawGuard's
# command/file/network rules and are always allowed.
_CANONICAL = {
    "bash": "execute_command",
    "read": "read_file",
    "glob": "read_file",
    "grep": "read_file",
    "write": "write_file",
    "edit": "edit_file",
    "webfetch": "http_request",
}


def _rules_config() -> dict[str, Any]:
    with _RULES_PATH.open(encoding="utf-8") as file:
        return yaml.safe_load(file)


def _engine(scope: dict[str, Any] | None) -> RuleEngine:
    engine = RuleEngine(_rules_config())
    if scope:
        engine.set_task_scope(
            task_description=scope.get("task_description", ""),
            file_read=scope.get("file_read"),
            file_write=scope.get("file_write"),
            commands=scope.get("commands"),
            network=scope.get("network"),
        )
    return engine


def _match(engine: RuleEngine, tool: str, args: dict[str, Any]):
    if tool == "bash":
        return engine.check_command(args.get("command", ""))
    if tool in ("read", "glob", "grep"):
        return engine.check_file_path(args.get("filePath") or args.get("path") or ".", "read")
    if tool in ("write", "edit"):
        return engine.check_file_path(args.get("filePath", ""), "write")
    return engine.check_network(args.get("url", ""))


def decide(tool: str, args: dict[str, Any], scope: dict[str, Any] | None) -> tuple[bool, str]:
    """Return ``(allowed, reason)`` for one opencode tool call under strict mode."""
    canonical = _CANONICAL.get(tool)
    if canonical is None:
        return True, ""
    engine = _engine(scope)
    if engine.is_tool_disabled(canonical):
        return False, f"tool '{tool}' disabled by the current task scope"
    match = _match(engine, tool, args)
    if match.action == ActionType.ALLOW:
        return True, ""
    reason = match.reason
    if match.action == ActionType.APPROVE:
        reason = f"{reason} (supervised operation blocked in strict mode)"
    return False, f"[{match.rule_type}] {reason}"


def sanitize(text: str) -> str:
    config = _rules_config().get("sanitizer_rules", {})
    sanitizer = Sanitizer(
        patterns=config.get("patterns"),
        skill_whitelist=config.get("skill_whitelist", []),
        enabled=config.get("enabled", True),
    )
    return sanitizer.sanitize_output(text)
