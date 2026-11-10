from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

import yaml

from src.adapter.native_cli.common import pick, skill_read

PLUGIN_CONTAINER_PATH = "/app/src/adapter/deepseek_harness/plugin.mjs"


def split_model(model: str) -> tuple[str, str]:
    value = str(model).strip()
    if "/" in value:
        provider, model_id = value.split("/", 1)
        if provider and model_id:
            return provider, model_id
    if not value:
        raise ValueError("DeepSeek-Harness model must not be empty")
    return "dashscope-inc", value


def state_path(sandbox_dir: Path) -> Path:
    sandbox_dir = Path(sandbox_dir)
    return sandbox_dir.parent / f".deepseek_harness_state_{sandbox_dir.name}"


def cleanup_state(sandbox_dir: Path) -> None:
    shutil.rmtree(state_path(sandbox_dir), ignore_errors=True)


def _disabled_rows(sample: dict[str, Any]) -> list[str]:
    if sample.get("source") != "ras-eval-next":
        return []
    return [
        "tool-jobs",
        "tool-skill",
        "tool-subagent-control",
        "tool-subagent-list-agents",
        "tool-subagent",
        "tool-subagent-fork",
        "tool-subagent-report",
        "tool-workflow",
        "tool-goal",
        "tool-ralph",
        "tool-str-replace-editor",
        "tool-web",
    ]


def build_patch(sample: dict[str, Any], model: str, base_url: str) -> list[dict[str, Any]]:
    provider, model_id = split_model(model)
    rows: list[dict[str, Any]] = [
        {
            "id": "llm-pi-ai",
            "config": {
                "providers": {
                    provider: {
                        "displayName": provider,
                        "apiKeyEnv": "OPENAI_API_KEY",
                        "api": "openai-completions",
                        "baseURL": base_url,
                        "compat": {
                            "supportsDeveloperRole": False,
                            "supportsReasoningEffort": False,
                        },
                        "models": [{
                            "id": model_id,
                            "name": model_id,
                            "contextWindow": 262144,
                            "maxTokens": 32768,
                        }],
                    }
                }
            },
        },
        {"id": "agent-default-model", "config": {"provider": provider, "model": model_id}},
        {"id": "approval", "config": {"policy": "never"}},
        {
            "insert": [{
                "id": "daedalus-native-cli-adapter",
                "name": f"file://{PLUGIN_CONTAINER_PATH}",
            }]
        },
    ]
    rows.extend({"id": row_id, "disabled": True} for row_id in _disabled_rows(sample))
    return rows


def prepare_state(sample: dict[str, Any], sandbox_dir: Path, model: str, base_url: str) -> Path:
    root = state_path(sandbox_dir)
    shutil.rmtree(root, ignore_errors=True)
    root.mkdir(parents=True)
    patch_path = root / "daedalus.cordis.yml"
    patch_path.write_text(
        yaml.safe_dump(build_patch(sample, model, base_url), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return root


def normalize_tool_call(provider_tool_name: str, arguments: Any) -> tuple[str, dict[str, Any]]:
    name = str(provider_tool_name or "")
    args = dict(arguments) if isinstance(arguments, dict) else {}
    if name == "todo_write":
        return "todowrite", args
    if name == "read":
        skill = skill_read(args)
        if skill is not None:
            return skill
        normalized = {"filePath": pick(args, "file_path", "filePath", "path", default="")}
        for key in ("offset", "limit"):
            if key in args:
                normalized[key] = args[key]
        return "read", normalized
    if name == "write":
        return "write", {
            "filePath": pick(args, "file_path", "filePath", "path", default=""),
            "content": pick(args, "content", default=""),
        }
    if name == "edit":
        normalized = {
            "filePath": pick(args, "file_path", "filePath", "path", default=""),
            "oldString": pick(args, "old_string", "oldString", "oldText", default=""),
            "newString": pick(args, "new_string", "newString", "newText", default=""),
        }
        replace_all = pick(args, "replace_all", "replaceAll")
        if replace_all is not None:
            normalized["replaceAll"] = bool(replace_all)
        return "edit", normalized
    return name, args
