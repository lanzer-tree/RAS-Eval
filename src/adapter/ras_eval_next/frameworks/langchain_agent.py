from __future__ import annotations

from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import StructuredTool

from src.adapter.ras_eval_next.frameworks.common_loop import (
    RequestPacer,
    model_id,
    openai_client_kwargs,
    run_openai_tool_loop,
)
from src.adapter.ras_eval_next.tool_runtime import ToolRuntime


def _make_langchain_tools(runtime: ToolRuntime) -> list[StructuredTool]:
    tools = []
    for tool in runtime.tools.values():
        invoke = runtime.callable_for(tool.name)
        tools.append(StructuredTool.from_function(
            func=invoke,
            name=tool.name,
            description=tool.description,
        ))
    return tools


def _system_text(runtime: ToolRuntime) -> str:
    return "\n\n".join(
        message["content"] for message in runtime.recorder.messages if message.get("role") == "system"
    )


def _content_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    return str(content or "")


def run(runtime: ToolRuntime, model: str) -> str:
    tools = _make_langchain_tools(runtime)
    try:
        from langchain.chat_models import init_chat_model

        chat = init_chat_model(
            model_id(model),
            model_provider="openai",
            temperature=0,
            **openai_client_kwargs(),
        ).bind_tools(tools)
    except Exception:
        return run_openai_tool_loop(runtime, model)

    pacer = RequestPacer.from_env()
    messages: list[Any] = []
    system = _system_text(runtime)
    if system:
        messages.append(SystemMessage(content=system))
    messages.append(HumanMessage(content=runtime.sample.get("prompt", "")))
    final_text = ""
    for _ in range(40):
        pacer.wait()
        response = chat.invoke(messages)
        messages.append(response)
        tool_calls = getattr(response, "tool_calls", None) or []
        if not tool_calls:
            final_text = _content_text(response.content)
            runtime.recorder.record_assistant(final_text)
            break
        for call in tool_calls:
            name = str(call.get("name"))
            arguments = call.get("args") or {}
            output = runtime.call_tool(name, arguments)
            messages.append(ToolMessage(content=output, tool_call_id=str(call.get("id") or ""), name=name))
    else:
        final_text = "Max turns reached before the agent produced a final answer."
        runtime.recorder.record_assistant(final_text)
    return final_text
