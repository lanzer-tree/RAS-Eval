"""Hermes plugin hooks for crash-safe trajectory and per-tool LTL checks."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.adapter.hermes.common import (
    HermesTraceRecorder,
    initial_messages,
    normalize_tool_call,
    normalize_tool_result,
)
from src.evaluator.spec.runtime import RuntimeVerifier


_recorder: HermesTraceRecorder | None = None
_verifier: RuntimeVerifier | None = None


def _load_sample() -> dict[str, Any]:
    with Path(os.environ["RAS_EVAL_SAMPLE_PATH"]).open(encoding="utf-8") as file:
        return json.load(file)


def _get_recorder() -> HermesTraceRecorder:
    global _recorder
    if _recorder is None:
        trace_path = Path(os.environ.get("DAEDALUS_TRACE_PATH", "/workspace/.daedalus_trace.jsonl"))
        sample = _load_sample()
        _recorder = HermesTraceRecorder(trace_path, initial_messages(sample))
    return _recorder


def _get_verifier() -> RuntimeVerifier | None:
    global _verifier
    if _verifier is None and os.environ.get("DAEDALUS_RUNTIME_REQUEST"):
        _verifier = RuntimeVerifier.from_env()
    return _verifier


def _arguments(args: Any = None, params: Any = None, tool_input: Any = None) -> dict[str, Any]:
    for value in (args, params, tool_input):
        if isinstance(value, dict):
            return dict(value)
    return {}


def _pre_tool_call(
    tool_name: str = "",
    args: Any = None,
    params: Any = None,
    tool_input: Any = None,
    **_: Any,
) -> None:
    arguments = _arguments(args, params, tool_input)
    normalized_name, normalized_args = normalize_tool_call(str(tool_name), arguments)
    verifier = _get_verifier()
    if verifier is not None:
        verifier.before_tool()
    _get_recorder().append({
        "role": "assistant",
        "content": "",
        "tool_calls": [{
            "type": "function",
            "function": {"name": normalized_name, "arguments": normalized_args},
        }],
    })


def _post_tool_call(
    tool_name: str = "",
    args: Any = None,
    params: Any = None,
    tool_input: Any = None,
    result: Any = "",
    **_: Any,
) -> None:
    arguments = _arguments(args, params, tool_input)
    normalized_name, normalized_args = normalize_tool_call(str(tool_name), arguments)
    normalized_result = normalize_tool_result(str(tool_name), result)
    _get_recorder().append({"role": "tool", "name": normalized_name, "content": normalized_result})
    verifier = _get_verifier()
    if verifier is not None:
        verifier.after_tool(
            normalized_name,
            normalized_args,
            normalized_result,
            provider_tool_name=str(tool_name),
        )


def _on_session_start(**_: Any) -> None:
    _get_recorder()
    verifier = _get_verifier()
    if verifier is not None:
        verifier.before_tool()


def _post_llm_call(assistant_response: str = "", **_: Any) -> None:
    if assistant_response:
        _get_recorder().append({"role": "assistant", "content": assistant_response})


def register(ctx: Any) -> None:
    """Register observers only; hook failures remain non-fatal by Hermes design."""
    _get_recorder()
    ctx.register_hook("on_session_start", _on_session_start)
    ctx.register_hook("pre_tool_call", _pre_tool_call)
    ctx.register_hook("post_tool_call", _post_tool_call)
    ctx.register_hook("post_llm_call", _post_llm_call)
