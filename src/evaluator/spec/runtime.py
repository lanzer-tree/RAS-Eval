from __future__ import annotations

import argparse
import fcntl
import json
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

from src.evaluator.spec.verifier import OBSERVERS, env_atom_keys, verify_task

RUNTIME_DIR = "/runtime_verification"
REQUEST_PATH = f"{RUNTIME_DIR}/request.json"
STATE_PATH = f"{RUNTIME_DIR}/state.json"
RESULT_PATH = f"{RUNTIME_DIR}/result.json"
LOCK_PATH = f"{RUNTIME_DIR}/lock"
NUXMV_BIN = "/opt/nuXmv/usr/local/bin/nuXmv-portable.sh"
SPEC_KEYS = ("completion_specifications", "safety_specifications", "security_specifications")


def runtime_dir_for(sandbox_dir: Path) -> Path:
    sandbox_dir = Path(sandbox_dir)
    return sandbox_dir.parent / f".runtime_verification_{sandbox_dir.name}"


def prepare_runtime_dir(sample: dict[str, Any], sandbox_dir: Path) -> Path:
    state_dir = runtime_dir_for(sandbox_dir)
    if state_dir.exists():
        import shutil

        shutil.rmtree(state_dir)
    state_dir.mkdir(parents=True)
    meta = sample.get("meta", {})
    specs = [
        item["formal_spec"]
        for key in SPEC_KEYS
        for item in (meta.get(key) or [])
    ]
    response: list[dict[str, Any]] = []
    if meta.get("system_prompt"):
        response.append({"role": "system", "content": str(meta["system_prompt"])})
    response.append({"role": "user", "content": str(sample.get("prompt") or "")})
    request = {
        "traceid": sample["traceid"],
        "specs": specs,
        "response": response,
        "env_dir": "/workspace/environment" if sample.get("source") == "ras-eval-next" else "/workspace",
        "nuxmv_bin": NUXMV_BIN,
    }
    _write_json(state_dir / "request.json", request)
    return state_dir


def read_result_history(state_dir: Path, count: int) -> tuple[list[list[str]], list[str]]:
    state_dir = Path(state_dir)
    path = state_dir / "result.json"
    plugin_errors_path = state_dir / "plugin_errors.log"
    plugin_errors = (
        [line for line in plugin_errors_path.read_text(encoding="utf-8", errors="replace").splitlines() if line]
        if plugin_errors_path.exists()
        else []
    )
    if not path.exists():
        return [[] for _ in range(count)], plugin_errors
    data = json.loads(path.read_text(encoding="utf-8"))
    histories = data.get("results") or []
    normalized = [list(histories[index]) if index < len(histories) else [] for index in range(count)]
    return normalized, [*list(data.get("errors") or []), *plugin_errors]


def cleanup_runtime_dir(sandbox_dir: Path) -> None:
    import shutil

    shutil.rmtree(runtime_dir_for(sandbox_dir), ignore_errors=True)


def _write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=path.parent, delete=False) as file:
        json.dump(value, file, ensure_ascii=False)
        temporary = Path(file.name)
    temporary.replace(path)


def _capture_environment(specs: list[str], env_dir: str) -> list[dict[str, Any]]:
    snapshot = []
    for observer, arguments in env_atom_keys(specs):
        value = OBSERVERS[observer](env_dir, **dict(arguments))
        snapshot.append({"observer": observer, "arguments": list(arguments), "value": value})
    return snapshot


def _decode_snapshot(snapshot: list[dict[str, Any]]) -> dict[tuple[str, tuple[tuple[str, Any], ...]], Any]:
    return {
        (item["observer"], tuple(tuple(pair) for pair in item["arguments"])): item["value"]
        for item in snapshot
    }


def _stringify(value: Any) -> str:
    return value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, default=str)


def _initial_state(request: dict[str, Any]) -> dict[str, Any]:
    specs = list(request.get("specs") or [])
    return {
        "response": list(request.get("response") or []),
        "env_history": [_capture_environment(specs, request["env_dir"])],
        "results": [[] for _ in specs],
        "steps": [],
        "errors": [],
    }


def initialize(request_path: Path = Path(REQUEST_PATH), state_path: Path = Path(STATE_PATH)) -> None:
    if state_path.exists():
        return
    request = json.loads(request_path.read_text(encoding="utf-8"))
    state = _initial_state(request)
    _write_json(state_path, state)
    _write_json(state_path.with_name("result.json"), {"results": state["results"], "errors": []})


def record_step(
    tool_name: str,
    arguments: Any,
    result: Any,
    provider_tool_name: str | None = None,
    request_path: Path = Path(REQUEST_PATH),
    state_path: Path = Path(STATE_PATH),
) -> list[str]:
    request = json.loads(request_path.read_text(encoding="utf-8"))
    if not state_path.exists():
        initialize(request_path, state_path)
    state = json.loads(state_path.read_text(encoding="utf-8"))
    args_text = _stringify(arguments if arguments is not None else {})
    result_text = _stringify(result)
    state["response"].append({
        "role": "assistant",
        "content": "",
        "tool_calls": [{"type": "function", "function": {"name": tool_name, "arguments": args_text}}],
    })
    state["response"].append({"role": "tool", "name": tool_name, "content": result_text})
    state["env_history"].append(_capture_environment(request["specs"], request["env_dir"]))
    outcome = verify_task(
        state["response"],
        request["specs"],
        None,
        request.get("nuxmv_bin") or NUXMV_BIN,
        env_history=[_decode_snapshot(item) for item in state["env_history"]],
    )
    for history, verdict in zip(state["results"], outcome["results"]):
        history.append(verdict)
    state["steps"].append({
        "tool_name": tool_name,
        "provider_tool_name": provider_tool_name or tool_name,
        "arguments": args_text,
        "result": result_text,
    })
    _write_json(state_path, state)
    _write_json(state_path.with_name("result.json"), {
        "results": state["results"],
        "errors": state["errors"],
        "steps": state["steps"],
    })
    return outcome["results"]


def record_error(
    tool_name: str,
    arguments: Any,
    result: Any,
    error: Exception,
    provider_tool_name: str | None = None,
    request_path: Path = Path(REQUEST_PATH),
    state_path: Path = Path(STATE_PATH),
) -> None:
    if not state_path.exists():
        initialize(request_path, state_path)
    request = json.loads(request_path.read_text(encoding="utf-8"))
    state = json.loads(state_path.read_text(encoding="utf-8"))
    args_text = _stringify(arguments if arguments is not None else {})
    result_text = _stringify(result)
    message = f"{type(error).__name__}: {error}"
    state["response"].extend([
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"type": "function", "function": {"name": tool_name, "arguments": args_text}}],
        },
        {"role": "tool", "name": tool_name, "content": result_text},
    ])
    try:
        state["env_history"].append(_capture_environment(request["specs"], request["env_dir"]))
    except Exception:
        state["env_history"].append(state["env_history"][-1] if state["env_history"] else [])
    for history in state["results"]:
        history.append(f"error: {message}")
    state["steps"].append({
        "tool_name": tool_name,
        "provider_tool_name": provider_tool_name or tool_name,
        "arguments": args_text,
        "result": result_text,
    })
    state["errors"].append(message)
    _write_json(state_path, state)
    _write_json(state_path.with_name("result.json"), {
        "results": state["results"],
        "errors": state["errors"],
        "steps": state["steps"],
    })


class RuntimeVerifier:
    def __init__(self, request_path: Path = Path(REQUEST_PATH), state_path: Path = Path(STATE_PATH)) -> None:
        self.request_path = request_path
        self.state_path = state_path
        self._lock = threading.Lock()

    @classmethod
    def from_env(cls) -> "RuntimeVerifier":
        return cls(
            Path(os.environ.get("DAEDALUS_RUNTIME_REQUEST", REQUEST_PATH)),
            Path(os.environ.get("DAEDALUS_RUNTIME_STATE", STATE_PATH)),
        )

    def before_tool(self) -> None:
        with self._lock:
            try:
                initialize(self.request_path, self.state_path)
            except Exception:
                pass

    def after_tool(
        self,
        tool_name: str,
        arguments: Any,
        result: Any,
        provider_tool_name: str | None = None,
    ) -> list[str]:
        with self._lock:
            try:
                initialize(self.request_path, self.state_path)
                return record_step(
                    tool_name,
                    arguments,
                    result,
                    provider_tool_name,
                    self.request_path,
                    self.state_path,
                )
            except Exception as error:
                try:
                    record_error(
                        tool_name,
                        arguments,
                        result,
                        error,
                        provider_tool_name,
                        self.request_path,
                        self.state_path,
                    )
                except Exception:
                    pass
                return []


def _locked(action) -> None:
    lock_path = Path(os.environ.get("DAEDALUS_RUNTIME_LOCK", LOCK_PATH))
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("w", encoding="utf-8") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        action()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["init", "step"])
    args = parser.parse_args()
    request_path = Path(os.environ.get("DAEDALUS_RUNTIME_REQUEST", REQUEST_PATH))
    state_path = Path(os.environ.get("DAEDALUS_RUNTIME_STATE", STATE_PATH))
    if args.command == "init":
        _locked(lambda: initialize(request_path, state_path))
        return
    payload = json.load(os.fdopen(os.dup(0), encoding="utf-8"))

    def step() -> None:
        try:
            record_step(
                str(payload["tool_name"]),
                payload.get("arguments"),
                payload.get("result", ""),
                str(payload.get("provider_tool_name") or payload["tool_name"]),
                request_path,
                state_path,
            )
        except Exception as error:
            record_error(
                str(payload["tool_name"]),
                payload.get("arguments"),
                payload.get("result", ""),
                error,
                str(payload.get("provider_tool_name") or payload["tool_name"]),
                request_path,
                state_path,
            )

    _locked(step)


if __name__ == "__main__":
    main()
