from __future__ import annotations

import asyncio
import json
import os
import time
from typing import Any

from openai import OpenAI

from src.adapter.ras_eval_next.tool_runtime import ToolRuntime


class RequestPacer:
    def __init__(self, qps: float) -> None:
        self.interval = 0.0 if qps <= 0 else 1.0 / qps
        self.next_time = 0.0

    @classmethod
    def from_env(cls) -> RequestPacer:
        return cls(float(os.environ.get("RAS_EVAL_REQUEST_QPS", "0")))

    def wait(self) -> None:
        if self.interval <= 0:
            return
        now = time.monotonic()
        if now < self.next_time:
            time.sleep(self.next_time - now)
            now = time.monotonic()
        self.next_time = now + self.interval

    async def wait_async(self) -> None:
        if self.interval <= 0:
            return
        now = time.monotonic()
        if now < self.next_time:
            await asyncio.sleep(self.next_time - now)
            now = time.monotonic()
        self.next_time = now + self.interval


def openai_client_kwargs() -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "api_key": os.environ.get("OPENAI_API_KEY"),
        "base_url": os.environ.get("OPENAI_BASE_URL"),
    }
    max_retries = os.environ.get("RAS_EVAL_REQUEST_MAX_RETRIES")
    if max_retries is not None:
        kwargs["max_retries"] = int(max_retries)
    return kwargs


def _message_to_dict(message: Any) -> dict[str, Any]:
    if hasattr(message, "model_dump"):
        data = message.model_dump(exclude_none=True)
    else:
        data = dict(message)
    return {
        key: value
        for key, value in data.items()
        if key in {"role", "content", "tool_calls", "tool_call_id", "name"}
    }


def _tool_call_name(call: Any) -> str:
    function = getattr(call, "function", None)
    if function is None and isinstance(call, dict):
        function = call.get("function")
    if isinstance(function, dict):
        return str(function.get("name"))
    return str(getattr(function, "name"))


def _tool_call_arguments(call: Any) -> str:
    function = getattr(call, "function", None)
    if function is None and isinstance(call, dict):
        function = call.get("function")
    if isinstance(function, dict):
        return str(function.get("arguments") or "{}")
    return str(getattr(function, "arguments", "{}") or "{}")


def _tool_call_id(call: Any) -> str:
    if isinstance(call, dict):
        return str(call.get("id") or call.get("tool_call_id") or "")
    return str(getattr(call, "id", "") or "")


def model_id(model: str) -> str:
    return model.split("/", 1)[1] if "/" in model else model


def run_openai_tool_loop(runtime: ToolRuntime, model: str, *, max_turns: int = 40) -> str:
    client = OpenAI(**openai_client_kwargs())
    pacer = RequestPacer.from_env()
    messages = runtime.messages_for_model()
    final_text = ""
    for _ in range(max_turns):
        pacer.wait()
        response = client.chat.completions.create(
            model=model_id(model),
            messages=messages,
            tools=runtime.openai_tools(),
            tool_choice="auto",
            temperature=0,
        )
        message = response.choices[0].message
        content = message.content or ""
        assistant_message = _message_to_dict(message)
        messages.append(assistant_message)
        tool_calls = message.tool_calls or []
        if not tool_calls:
            final_text = content
            runtime.recorder.record_assistant(content)
            break
        for call in tool_calls:
            name = _tool_call_name(call)
            raw_arguments = _tool_call_arguments(call)
            try:
                arguments = json.loads(raw_arguments) if raw_arguments.strip() else {}
            except json.JSONDecodeError:
                arguments = {}
            output = runtime.call_tool(name, arguments)
            messages.append({
                "role": "tool",
                "tool_call_id": _tool_call_id(call),
                "name": name,
                "content": output,
            })
    else:
        final_text = "Max turns reached before the agent produced a final answer."
        runtime.recorder.record_assistant(final_text)
    return final_text
