from __future__ import annotations

import json
import os
from contextlib import AsyncExitStack
from typing import Any

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import AsyncOpenAI

from src.adapter.ras_eval_next.frameworks.common_loop import (
    RequestPacer,
    _message_to_dict,
    _tool_call_arguments,
    _tool_call_id,
    _tool_call_name,
    model_id,
    openai_client_kwargs,
    run_openai_tool_loop,
)
from src.adapter.ras_eval_next.tool_runtime import NATIVE_TOOL_FUNCTIONS, ToolRuntime


def _schema_parameters(schema: Any) -> dict[str, Any]:
    if not isinstance(schema, dict):
        return {"type": "object", "properties": {}, "required": []}
    parameters = dict(schema)
    parameters.setdefault("type", "object")
    parameters.setdefault("properties", {})
    parameters.setdefault("required", [])
    return parameters


def _mcp_tool_to_openai(tool: Any) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or tool.name,
            "parameters": _schema_parameters(getattr(tool, "inputSchema", None)),
        },
    }


def _mcp_content_to_text(result: Any) -> str:
    if getattr(result, "isError", False):
        prefix = "MCP tool error: "
    else:
        prefix = ""
    content = getattr(result, "content", result)
    if isinstance(content, list):
        parts = []
        for item in content:
            text = getattr(item, "text", None)
            if text is not None:
                parts.append(str(text))
            else:
                parts.append(json.dumps(item.model_dump() if hasattr(item, "model_dump") else item, ensure_ascii=False, default=str))
        return prefix + "\n".join(parts)
    if isinstance(content, str):
        return prefix + content
    return prefix + json.dumps(content, ensure_ascii=False, default=str)


async def _run_ras_eval_next_mcp(runtime: ToolRuntime, model: str, *, max_turns: int = 40) -> str:
    server_env = os.environ.copy()
    server_env.update({
        "PYTHONPATH": "/app",
        "RAS_EVAL_SAMPLE_PATH": os.environ["RAS_EVAL_SAMPLE_PATH"],
        "RAS_EVAL_ENV_REPLAY_REPORT": "/workspace/.env_replay_warnings.json",
    })
    params = StdioServerParameters(
        command="python",
        args=["/app/src/adapter/ras_eval_next/ras_eval_mcp.py"],
        env=server_env,
        cwd="/workspace",
    )
    pacer = RequestPacer.from_env()
    messages = runtime.messages_for_model()
    async with AsyncExitStack() as stack:
        client = await stack.enter_async_context(AsyncOpenAI(**openai_client_kwargs()))
        read, write = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        listed = await session.list_tools()
        mcp_tools = list(listed.tools)
        mcp_names = {tool.name for tool in mcp_tools}
        openai_tools = [_mcp_tool_to_openai(tool) for tool in mcp_tools]
        for name, tool in runtime.tools.items():
            if name not in mcp_names and name in NATIVE_TOOL_FUNCTIONS:
                openai_tools.append(tool.schema)
        final_text = ""
        for _ in range(max_turns):
            await pacer.wait_async()
            response = await client.chat.completions.create(
                model=model_id(model),
                messages=messages,
                tools=openai_tools,
                tool_choice="auto",
                temperature=0,
            )
            message = response.choices[0].message
            content = message.content or ""
            messages.append(_message_to_dict(message))
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
                if name in mcp_names:
                    if runtime.verifier is not None:
                        runtime.verifier.before_tool()
                    runtime.recorder.record_tool_call(name, arguments)
                    result = await session.call_tool(name, arguments)
                    output = _mcp_content_to_text(result)
                    runtime.recorder.record_tool_result(name, output)
                    if runtime.verifier is not None:
                        runtime.verifier.after_tool(name, arguments, output)
                else:
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


async def run_async(runtime: ToolRuntime, model: str) -> str:
    if runtime.source != "ras-eval-next":
        return run_openai_tool_loop(runtime, model)
    return await _run_ras_eval_next_mcp(runtime, model)
