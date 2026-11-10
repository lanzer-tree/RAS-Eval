from __future__ import annotations

from typing import Any

from src.adapter.native_cli.common import pick, skill_read

PLUGIN_CONTAINER_PATH = "/app/src/adapter/pi/extension.mjs"


def split_model(model: str) -> tuple[str, str]:
    value = str(model).strip()
    if "/" in value:
        provider, model_id = value.split("/", 1)
        if provider and model_id:
            return provider, model_id
    if not value:
        raise ValueError("Pi model must not be empty")
    return "dashscope-inc", value


def selected_builtin_tools(sample: dict[str, Any]) -> list[str]:
    # Pi's find tool is the closest equivalent to OpenCode glob. ls is omitted
    # because it has no direct OpenCode LTL vocabulary counterpart.
    return ["read", "bash", "edit", "write", "grep", "find"]


def target_skill_path(sample: dict[str, Any]) -> str | None:
    if sample.get("source") != "skill_inject":
        return None
    meta = sample.get("meta") or {}
    name = str(meta.get("skill") or meta.get("base_skill") or meta.get("skill_name") or "").strip()
    return f"/workspace/.agents/skills/{name}/SKILL.md" if name else None


def normalize_tool_call(provider_tool_name: str, arguments: Any) -> tuple[str, dict[str, Any]]:
    name = str(provider_tool_name or "")
    args = dict(arguments) if isinstance(arguments, dict) else {}
    if name == "find":
        normalized = {
            "pattern": pick(args, "pattern", default="*"),
            "path": pick(args, "path", default="."),
        }
        return "glob", normalized
    if name == "read":
        skill = skill_read(args)
        if skill is not None:
            return skill
        normalized = {"filePath": pick(args, "path", "file_path", "filePath", default="")}
        for key in ("offset", "limit"):
            if key in args:
                normalized[key] = args[key]
        return "read", normalized
    if name == "write":
        return "write", {
            "filePath": pick(args, "path", "file_path", "filePath", default=""),
            "content": pick(args, "content", default=""),
        }
    if name == "edit":
        normalized = {
            "filePath": pick(args, "path", "file_path", "filePath", default=""),
            "oldString": pick(args, "oldText", "old_string", "oldString", default=""),
            "newString": pick(args, "newText", "new_string", "newString", default=""),
        }
        return "edit", normalized
    return name, args
