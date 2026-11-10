from __future__ import annotations

import json
from pathlib import Path
from typing import Any

TRACE_FILENAME = ".daedalus_trace.jsonl"


def initial_messages(sample: dict[str, Any]) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    system_prompt = (sample.get("meta") or {}).get("system_prompt")
    if system_prompt:
        messages.append({"role": "system", "content": str(system_prompt)})
    messages.append({"role": "user", "content": str(sample.get("prompt") or "")})
    return messages


def initialize_trace(path: Path, sample: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for message in initial_messages(sample):
            file.write(json.dumps(message, ensure_ascii=False) + "\n")
        file.flush()


def append_assistant(path: Path, content: str) -> None:
    content = str(content or "").strip()
    if not content:
        return
    messages = read_trace(path)
    if messages and messages[-1].get("role") == "assistant" and messages[-1].get("content") == content:
        return
    with path.open("a", encoding="utf-8") as file:
        file.write(json.dumps({"role": "assistant", "content": content}, ensure_ascii=False) + "\n")
        file.flush()


def read_trace(path: Path) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    if not path.exists():
        return messages
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            messages.append(value)
    return messages


def pick(arguments: dict[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in arguments:
            return arguments[name]
    return default


def skill_read(arguments: dict[str, Any]) -> tuple[str, dict[str, Any]] | None:
    path = pick(arguments, "path", "file_path", "filePath", default="")
    normalized = str(path).replace("\\", "/")
    marker = "/.agents/skills/"
    if marker not in normalized or not normalized.endswith("/SKILL.md"):
        return None
    suffix = normalized.split(marker, 1)[1]
    return "skill", {"name": suffix[:-len("/SKILL.md")].split("/")[0]}
