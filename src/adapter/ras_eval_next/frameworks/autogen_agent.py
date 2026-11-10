from __future__ import annotations

from typing import Any

from autogen_core.tools import FunctionTool

from src.adapter.ras_eval_next.frameworks.common_loop import (
    RequestPacer,
    model_id,
    openai_client_kwargs,
    run_openai_tool_loop,
)
from src.adapter.ras_eval_next.tool_runtime import ToolRuntime


def _make_autogen_tools(runtime: ToolRuntime) -> list[FunctionTool]:
    tools = []
    for tool in runtime.tools.values():
        invoke = runtime.callable_for(tool.name)
        try:
            tools.append(FunctionTool(
                invoke,
                name=tool.name,
                description=tool.description,
                strict=False,
            ))
        except Exception:
            continue
    return tools


def _system_text(runtime: ToolRuntime) -> str:
    return "\n\n".join(
        message["content"] for message in runtime.recorder.messages if message.get("role") == "system"
    )


def _result_text(result: Any) -> str:
    messages = getattr(result, "messages", None) or []
    for message in reversed(messages):
        content = getattr(message, "content", None)
        if content:
            return str(content)
    return str(getattr(result, "content", "") or "")


async def run_async(runtime: ToolRuntime, model: str) -> str:
    try:
        from autogen_agentchat.agents import AssistantAgent
        from autogen_ext.models.openai import OpenAIChatCompletionClient
    except Exception:
        return run_openai_tool_loop(runtime, model)

    pacer = RequestPacer.from_env()

    class PacedOpenAIChatCompletionClient(OpenAIChatCompletionClient):
        async def create(self, *args: Any, **kwargs: Any) -> Any:
            await pacer.wait_async()
            return await super().create(*args, **kwargs)

    model_client = PacedOpenAIChatCompletionClient(
        model=model_id(model),
        model_info={
            "vision": False,
            "function_calling": True,
            "json_output": True,
            "structured_output": True,
            "family": "gpt-4o",
        },
        **openai_client_kwargs(),
    )
    try:
        agent = AssistantAgent(
            name="DaedalusAgent",
            model_client=model_client,
            system_message=_system_text(runtime),
            tools=_make_autogen_tools(runtime),
            reflect_on_tool_use=False,
            max_tool_iterations=40,
        )
        result = await agent.run(task=runtime.sample.get("prompt", ""))
        final_text = _result_text(result)
        runtime.recorder.record_assistant(final_text)
        return final_text
    finally:
        close = getattr(model_client, "close", None)
        if close is not None:
            outcome = close()
            if hasattr(outcome, "__await__"):
                await outcome
