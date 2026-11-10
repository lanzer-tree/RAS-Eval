"""OpenClaw harness configuration, trace normalization, and lifecycle helpers."""
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from src.runner.sandbox import local_state_path


PLUGIN_ID = "daedalus-runtime-verification"
PLUGIN_CONTAINER_PATH = "/app/src/adapter/openclaw/runtime_plugin"
TRACE_FILENAME = ".daedalus_trace.jsonl"
MCP_SERVER_NAME = "ras_eval_next"
MCP_PREFIX = f"{MCP_SERVER_NAME}__"


def openclaw_state_path(sandbox_dir: Path) -> Path:
    return local_state_path(sandbox_dir, "openclaw_state")


def cleanup_openclaw_state(sandbox_dir: Path) -> None:
    shutil.rmtree(openclaw_state_path(sandbox_dir), ignore_errors=True)


def split_model(model: str) -> tuple[str, str]:
    value = str(model).strip()
    if "/" in value:
        provider, model_id = value.split("/", 1)
        if provider and model_id:
            return provider, model_id
    if not value:
        raise ValueError("OpenClaw model must not be empty")
    return "dashscope-inc", value


def _visible_skill_name(meta: dict[str, Any]) -> str:
    return str(meta.get("skill") or meta.get("base_skill") or meta.get("skill_name") or "").strip()


def build_config(sample: dict[str, Any], model: str) -> dict[str, Any]:
    """Build a deterministic, non-interactive OpenClaw config for one sample."""
    source = str(sample.get("source") or "")
    meta = sample.get("meta") or {}
    provider, model_id = split_model(model)
    config: dict[str, Any] = {
        "models": {
            "mode": "replace",
            "pricing": {"enabled": False},
            "providers": {
                provider: {
                    "baseUrl": "${OPENAI_BASE_URL}",
                    "apiKey": "${OPENAI_API_KEY}",
                    "api": "openai-completions",
                    "models": [{"id": model_id, "name": model_id}],
                }
            },
        },
        "agents": {
            "defaults": {
                "workspace": "/workspace",
                "model": {"primary": f"{provider}/{model_id}"},
                "skipBootstrap": True,
            }
        },
        "tools": {
            "profile": "coding",
            "allow": ["exec", "read", "write", "edit", "apply_patch", "bundle-mcp"],
            "deny": [
                "process",
                "code_execution",
                "group:web",
                "group:sessions",
                "group:memory",
                "group:ui",
                "group:automation",
                "group:messaging",
                "group:nodes",
                "group:agents",
                "group:media",
            ],
        },
        "skills": {"allowBundled": []},
        "plugins": {
            "load": {"paths": [PLUGIN_CONTAINER_PATH]},
            "entries": {
                PLUGIN_ID: {"enabled": True}
            },
        },
    }
    if source == "ras-eval-next":
        config["agents"]["defaults"]["skills"] = []
        config["mcp"] = {
            "servers": {
                MCP_SERVER_NAME: {
                    "enabled": True,
                    "command": "python",
                    "args": ["/app/src/adapter/openclaw/mcp_entry.py"],
                    "env": {
                        "RAS_EVAL_SAMPLE_PATH": "/sample.json",
                        "RAS_EVAL_ENV_REPLAY_REPORT": "/workspace/.env_replay_warnings.json",
                    },
                    "connectionTimeoutMs": 60_000,
                    "requestTimeoutMs": 300_000,
                    "supportsParallelToolCalls": False,
                    "toolFilter": {"include": list(meta.get("tools") or [])},
                }
            }
        }
    elif source == "skill_inject" and meta.get("attack_type") == "cia":
        skill_name = _visible_skill_name(meta)
        config["agents"]["defaults"]["skills"] = [skill_name] if skill_name else []
    else:
        raise NotImplementedError(f"OpenClaw is not supported for source={source!r}")
    return config


def prepare_openclaw_state(sample: dict[str, Any], sandbox_dir: Path, model: str) -> Path:
    """Create a fresh state tree whose config contains no resolved secret values."""
    state_dir = openclaw_state_path(sandbox_dir)
    shutil.rmtree(state_dir, ignore_errors=True)
    state_dir.mkdir(parents=True)
    (state_dir / "state").mkdir()
    (state_dir / "home").mkdir()
    (state_dir / "openclaw.json").write_text(
        json.dumps(build_config(sample, model), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (state_dir / "prompt.txt").write_text(str(sample.get("prompt") or ""), encoding="utf-8")
    return state_dir


def _pick(arguments: dict[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in arguments:
            return arguments[name]
    return default


def normalize_tool_call(provider_tool_name: str, arguments: Any) -> tuple[str, dict[str, Any]]:
    """Map OpenClaw tool calls to the OpenCode vocabulary used by LTL specs."""
    name = str(provider_tool_name or "")
    args = dict(arguments) if isinstance(arguments, dict) else {}
    if name.startswith(MCP_PREFIX):
        return name[len(MCP_PREFIX):], args
    if name == "exec":
        normalized = {"command": _pick(args, "command", default="")}
        if "timeout" in args:
            normalized["timeout"] = args["timeout"]
        cwd = _pick(args, "cwd", "workdir")
        if cwd is not None:
            normalized["workdir"] = cwd
        return "bash", normalized
    if name == "read":
        path = _pick(args, "path", "file_path", "filePath", default="")
        path_text = str(path).replace("\\", "/")
        parts = path_text.split("/.agents/skills/", 1)
        if len(parts) == 2 and parts[1].endswith("/SKILL.md"):
            return "skill", {"name": parts[1][:-len("/SKILL.md")].split("/")[0]}
        normalized = {"filePath": path}
        for key in ("offset", "limit"):
            if key in args:
                normalized[key] = args[key]
        return "read", normalized
    if name == "write":
        return "write", {
            "filePath": _pick(args, "path", "file_path", "filePath", default=""),
            "content": _pick(args, "content", default=""),
        }
    if name == "edit":
        normalized = {
            "filePath": _pick(args, "path", "file_path", "filePath", default=""),
            "oldString": _pick(args, "oldText", "old_string", "oldString", default=""),
            "newString": _pick(args, "newText", "new_string", "newString", default=""),
        }
        replace_all = _pick(args, "replaceAll", "replace_all")
        if replace_all is not None:
            normalized["replaceAll"] = bool(replace_all)
        return "edit", normalized
    if name == "apply_patch":
        return "patch", args
    return name, args


def initial_messages(sample: dict[str, Any]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    system_prompt = (sample.get("meta") or {}).get("system_prompt")
    if system_prompt:
        messages.append({"role": "system", "content": str(system_prompt)})
    messages.append({"role": "user", "content": str(sample.get("prompt") or "")})
    return messages


def initialize_trace(path: Path, sample: dict[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for message in initial_messages(sample):
            file.write(json.dumps(message, ensure_ascii=False) + "\n")
        file.flush()


def append_assistant(path: Path, content: str) -> None:
    if not content:
        return
    messages = read_trace(path)
    if messages and messages[-1].get("role") == "assistant" and messages[-1].get("content") == content:
        return
    with Path(path).open("a", encoding="utf-8") as file:
        file.write(json.dumps({"role": "assistant", "content": content}, ensure_ascii=False) + "\n")
        file.flush()


def read_trace(path: Path) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    if not Path(path).exists():
        return messages
    for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            messages.append(value)
    return messages
