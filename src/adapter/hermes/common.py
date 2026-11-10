"""Hermes harness configuration, trace normalization, and lifecycle helpers."""
from __future__ import annotations

import json
import os
import shutil
import threading
from pathlib import Path
from typing import Any

import yaml

from src.adapter.ras_eval_next import common as ras_eval_next_common


PLUGIN_NAME = "daedalus-runtime-verification"
TRACE_FILENAME = ".daedalus_trace.jsonl"
MCP_SERVER_NAME = "ras_eval_next"
MCP_PREFIXES = (
    f"mcp__{MCP_SERVER_NAME}__",
    f"mcp_{MCP_SERVER_NAME}_",
)


def hermes_home_path(sandbox_dir: Path) -> Path:
    sandbox_dir = Path(sandbox_dir)
    return sandbox_dir.parent / f".hermes_home_{sandbox_dir.name}"


def cleanup_hermes_home(sandbox_dir: Path) -> None:
    shutil.rmtree(hermes_home_path(sandbox_dir), ignore_errors=True)


def _mcp_environment(api_keys: dict[str, str]) -> dict[str, str]:
    env = {
        "PYTHONPATH": "/app",
        "RAS_EVAL_SAMPLE_PATH": "/sample.json",
        "RAS_EVAL_ENV_REPLAY_REPORT": "/workspace/.env_replay_warnings.json",
    }
    for name in api_keys:
        env[name] = f"${{{name}}}"
    return env


def build_config(
    sample: dict[str, Any],
    model: str,
    api_keys: dict[str, str],
) -> tuple[dict[str, Any], list[str]]:
    """Build an isolated Hermes configuration and its CLI toolset allow-list."""
    source = str(sample.get("source") or "")
    config: dict[str, Any] = {
        "model": {
            "provider": "custom",
            "default": model,
            "base_url": "${OPENAI_BASE_URL}",
            "api_key": "${OPENAI_API_KEY}",
        },
        "terminal": {
            "backend": "local",
            "cwd": "/workspace",
            "timeout": 300,
        },
        "memory": {
            "memory_enabled": False,
            "user_profile_enabled": False,
        },
        "compression": {"enabled": False},
        "security": {"tirith_enabled": False},
        "tools": {"tool_search": {"enabled": "off"}},
        "agent": {
            "disabled_toolsets": [
                "browser",
                "clarify",
                "code_execution",
                "cronjob",
                "delegation",
                "image_gen",
                "memory",
                "session_search",
                "tts",
                "vision",
                "web",
            ],
        },
        "plugins": {"enabled": [PLUGIN_NAME]},
    }
    if source == "ras-eval-next":
        config["mcp_servers"] = {
            MCP_SERVER_NAME: {
                "command": "python",
                "args": ["/app/src/adapter/ras_eval_next/ras_eval_mcp.py"],
                "env": _mcp_environment(api_keys),
                "enabled": True,
                "timeout": 300,
                "connect_timeout": 60,
                "tools": {
                    "include": list((sample.get("meta") or {}).get("tools") or []),
                    "resources": False,
                    "prompts": False,
                },
            },
        }
        toolsets = ["file", "terminal", "todo", f"mcp-{MCP_SERVER_NAME}"]
    elif source == "skill_inject":
        config["skills"] = {"external_dirs": ["/workspace/.agents/skills"]}
        toolsets = ["file", "terminal", "todo", "skills"]
    else:
        raise NotImplementedError(f"Hermes is not supported for source={source!r}")
    return config, toolsets


def prepare_hermes_home(
    sample: dict[str, Any],
    sandbox_dir: Path,
    model: str,
    api_keys: dict[str, str],
) -> tuple[Path, list[str]]:
    """Create a fresh per-sample Hermes home with only Daedalus configuration."""
    home = hermes_home_path(sandbox_dir)
    shutil.rmtree(home, ignore_errors=True)
    plugin_dir = home / "plugins" / PLUGIN_NAME
    plugin_dir.mkdir(parents=True)
    (home / "tmp").mkdir()
    config, toolsets = build_config(sample, model, api_keys)
    (home / "config.yaml").write_text(
        yaml.safe_dump(config, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    (home / ".no-bundled-skills").touch()
    (plugin_dir / "plugin.yaml").write_text(
        yaml.safe_dump(
            {
                "name": PLUGIN_NAME,
                "version": "1.0.0",
                "description": "Daedalus trajectory and runtime verification hooks",
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    (plugin_dir / "__init__.py").write_text(
        "import sys\n"
        "sys.path.insert(0, '/app')\n"
        "from src.adapter.hermes.runtime_plugin import register\n",
        encoding="utf-8",
    )
    return home, toolsets


def _pick(arguments: dict[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in arguments:
            return arguments[name]
    return default


def normalize_tool_call(provider_tool_name: str, arguments: Any) -> tuple[str, dict[str, Any]]:
    """Map Hermes native/MCP calls to the OpenCode names used by LTL specs."""
    args = dict(arguments) if isinstance(arguments, dict) else {}
    for prefix in MCP_PREFIXES:
        if provider_tool_name.startswith(prefix):
            return provider_tool_name[len(prefix):], args
    if provider_tool_name == "terminal":
        normalized = {"command": _pick(args, "command", default="")}
        if "timeout" in args:
            normalized["timeout"] = args["timeout"]
        if _pick(args, "cwd", "workdir") is not None:
            normalized["workdir"] = _pick(args, "cwd", "workdir")
        return "bash", normalized
    if provider_tool_name == "read_file":
        normalized = {"filePath": _pick(args, "path", "file_path", "filePath", default="")}
        for name in ("offset", "limit"):
            if name in args:
                normalized[name] = args[name]
        return "read", normalized
    if provider_tool_name == "write_file":
        return "write", {
            "filePath": _pick(args, "path", "file_path", "filePath", default=""),
            "content": _pick(args, "content", "file_content", default=""),
        }
    if provider_tool_name == "patch":
        normalized = {
            "filePath": _pick(args, "path", "file_path", "filePath", default=""),
            "oldString": _pick(args, "old_string", "oldString", default=""),
            "newString": _pick(args, "new_string", "newString", default=""),
        }
        if _pick(args, "replace_all", "replaceAll") is not None:
            normalized["replaceAll"] = bool(_pick(args, "replace_all", "replaceAll"))
        return "edit", normalized
    if provider_tool_name == "search_files":
        target = str(_pick(args, "target", default="content") or "content").lower()
        if target in {"file", "files", "filename", "name", "path"}:
            return "glob", {
                "pattern": _pick(args, "query", "pattern", "file_glob", default="**/*"),
                "path": _pick(args, "path", default="."),
            }
        normalized = {
            "pattern": _pick(args, "query", "pattern", default=""),
            "path": _pick(args, "path", default="."),
        }
        file_glob = _pick(args, "file_glob", "glob", "include")
        if file_glob is not None:
            normalized["glob"] = file_glob
        return "grep", normalized
    if provider_tool_name == "todo":
        return "todowrite", {"todos": _pick(args, "todos", default=[])}
    if provider_tool_name == "skill_view":
        return "skill", {"name": _pick(args, "name", "skill", default="")}
    return provider_tool_name, args


def normalize_tool_result(provider_tool_name: str, result: Any) -> Any:
    """Remove Hermes' MCP transport envelope while preserving native results."""
    if not any(provider_tool_name.startswith(prefix) for prefix in MCP_PREFIXES):
        return result
    parsed = result
    if isinstance(result, str):
        try:
            parsed = json.loads(result)
        except json.JSONDecodeError:
            return result
    if isinstance(parsed, dict) and set(parsed) == {"result"}:
        return parsed["result"]
    return result


class HermesTraceRecorder:
    """Crash-resilient JSONL recorder used by Hermes plugin callbacks."""

    def __init__(self, path: Path, initial_messages: list[dict[str, Any]]) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._initialized = False
        self.initialize(initial_messages)

    def initialize(self, initial_messages: list[dict[str, Any]]) -> None:
        with self._lock:
            if self._initialized:
                return
            with self.path.open("w", encoding="utf-8") as file:
                for message in initial_messages:
                    file.write(json.dumps(message, ensure_ascii=False, default=str) + "\n")
                file.flush()
                os.fsync(file.fileno())
            self._initialized = True

    def append(self, message: dict[str, Any]) -> None:
        with self._lock, self.path.open("a", encoding="utf-8") as file:
            file.write(json.dumps(message, ensure_ascii=False, default=str) + "\n")
            file.flush()
            os.fsync(file.fileno())


def initial_messages(sample: dict[str, Any]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    system_prompt = (sample.get("meta") or {}).get("system_prompt")
    if system_prompt:
        messages.append({"role": "system", "content": str(system_prompt)})
    messages.append({"role": "user", "content": str(sample.get("prompt") or "")})
    return messages


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
