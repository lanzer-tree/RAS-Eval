from __future__ import annotations

import json
import os
from typing import Any

from agents import Agent, FunctionTool, ModelSettings, Runner, set_tracing_disabled
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel
from openai import AsyncOpenAI

from src.adapter.ras_eval_next.frameworks.common_loop import model_id
from src.adapter.ras_eval_next.tool_runtime import ToolRuntime


def _make_openai_agent_tools(runtime: ToolRuntime) -> list[FunctionTool]:
    tools = []
    for tool in runtime.tools.values():
        async def invoke(_ctx: Any, raw_input: str, _tool_name: str = tool.name) -> str:
            try:
                arguments = json.loads(raw_input) if raw_input else {}
            except json.JSONDecodeError:
                arguments = {}
            return runtime.call_tool(_tool_name, arguments)

        tools.append(FunctionTool(
            name=tool.name,
            description=tool.description,
            params_json_schema=tool.schema["function"]["parameters"],
            on_invoke_tool=invoke,
            strict_json_schema=False,
        ))
    return tools


async def run_async(runtime: ToolRuntime, model: str) -> str:
    set_tracing_disabled(True)
    client = AsyncOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url=os.environ.get("OPENAI_BASE_URL"),
    )
    agent = Agent(
        name="DaedalusAgent",
        instructions="\n\n".join(
            message["content"] for message in runtime.recorder.messages if message.get("role") == "system"
        ),
        model=OpenAIChatCompletionsModel(model=model_id(model), openai_client=client),
        tools=_make_openai_agent_tools(runtime),
        model_settings=ModelSettings(temperature=0),
    )
    result = await Runner.run(agent, input=runtime.sample.get("prompt", ""), max_turns=40)
    final_text = str(result.final_output or "")
    runtime.recorder.record_assistant(final_text)
    return final_text
