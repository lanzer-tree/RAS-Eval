from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.evaluator.spec.runtime import runtime_dir_for

REPO_ROOT = Path(__file__).resolve().parents[3]
COMPUTER_TOOLKIT_PATH = (
    REPO_ROOT / "src" / "toolkits" / "ras_eval" / "computer_toolkit" / "json" / "computer_toolkit.json"
)
MANIFEST_NAME = "shieldagent_tools.json"
RAS_NATIVE_TOOLS = frozenset({"bash", "read", "write", "edit", "grep", "glob", "todowrite"})


def build_tool_manifest(
    sample: dict[str, Any],
    *,
    disable_native_tools: bool = False,
) -> list[dict[str, Any]]:
    native_tools = _load_schema(COMPUTER_TOOLKIT_PATH)
    if sample["source"] == "ras-eval-next":
        native_tools = [] if disable_native_tools else [
            tool for tool in native_tools if _tool_name(tool) in RAS_NATIVE_TOOLS
        ]
        return [*native_tools, *_ras_eval_tools(sample)]
    return native_tools


def prepare_shieldagent_runtime(
    sample: dict[str, Any],
    sandbox_dir: Path,
    *,
    disable_native_tools: bool = False,
) -> Path:
    path = runtime_dir_for(sandbox_dir) / MANIFEST_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {"tools": build_tool_manifest(sample, disable_native_tools=disable_native_tools)},
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    return path


def _ras_eval_tools(sample: dict[str, Any]) -> list[dict[str, Any]]:
    meta = sample["meta"]
    selected = set(meta["tools"])
    injections = {
        str(attack.get("tool")): str(attack.get("content") or "")
        for attack in _attack_entries(meta.get("attack"))
        if attack.get("mode") == "tpa"
    }
    tools: list[dict[str, Any]] = []
    root = REPO_ROOT / "src" / "toolkits" / "ras_eval"
    for toolkit in meta["toolkits"]:
        for entry in _load_schema(root / toolkit / "json" / f"{toolkit}.json"):
            function = entry.get("function", entry)
            name = function.get("name")
            if name not in selected:
                continue
            function = dict(function)
            function["name"] = f"ras_eval_next_{name}"
            function["description"] = injections.get(str(name), "") + str(
                function.get("description") or name
            )
            tools.append({"type": "function", "function": function})
    return tools


def _load_schema(path: Path) -> list[dict[str, Any]]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"tool schema must be a list: {path}")
    return [entry for entry in value if isinstance(entry, dict)]


def _tool_name(tool: dict[str, Any]) -> str | None:
    function = tool.get("function", tool)
    name = function.get("name") if isinstance(function, dict) else None
    return str(name) if name else None


def _attack_entries(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        nested = value.get("attacks") or value.get("attack")
        if isinstance(nested, list):
            return [item for item in nested if isinstance(item, dict)]
        if isinstance(nested, dict):
            return [nested]
        return [value]
    return []
