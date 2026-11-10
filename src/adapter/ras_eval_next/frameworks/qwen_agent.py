from __future__ import annotations

import json
import os
from typing import Any

from src.adapter.ras_eval_next.frameworks.common_loop import model_id, run_openai_tool_loop
from src.adapter.ras_eval_next.tool_runtime import ToolRuntime


def _make_qwen_tools(runtime: ToolRuntime) -> list[Any]:
    try:
        from qwen_agent.tools.base import BaseTool
    except Exception:
        return []

    qwen_tools = []
    for tool in runtime.tools.values():
        schema = tool.schema["function"]

        class DynamicTool(BaseTool):
            name = schema["name"]
            description = schema["description"]
            parameters = schema["parameters"]

            def call(self, params, **kwargs):
                if isinstance(params, str):
                    try:
                        arguments = json.loads(params) if params else {}
                    except json.JSONDecodeError:
                        arguments = {}
                else:
                    arguments = params or {}
                return runtime.call_tool(self.name, arguments)

        qwen_tools.append(DynamicTool())
    return qwen_tools


def run(runtime: ToolRuntime, model: str) -> str:
    try:
        from qwen_agent.agents import Assistant
    except Exception:
        return run_openai_tool_loop(runtime, model)
    llm_cfg = {
        "model": model_id(model),
        "api_key": os.environ.get("OPENAI_API_KEY"),
        "model_server": os.environ.get("OPENAI_BASE_URL"),
        "generate_cfg": {"temperature": 0},
    }
    system = "\n\n".join(
        message["content"] for message in runtime.recorder.messages if message.get("role") == "system"
    )
    agent = Assistant(llm=llm_cfg, system_message=system, function_list=_make_qwen_tools(runtime))
    last = ""
    for chunk in agent.run(messages=[{"role": "user", "content": runtime.sample.get("prompt", "")}], lang="en"):
        if isinstance(chunk, list) and chunk:
            message = chunk[-1]
            if isinstance(message, dict):
                last = str(message.get("content") or last)
            else:
                last = str(getattr(message, "content", last) or last)
    runtime.recorder.record_assistant(last)
    return last
