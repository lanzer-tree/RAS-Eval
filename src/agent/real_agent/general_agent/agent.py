from src.llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal


class GeneralAgent(ReactAgent):
    def __init__(self, model, tools: list[str], temperature = 0):
        self.tools = tools
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        self.add_system_prompt("You are a helpful assistant.")

    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:  
        toolkit = {}
        for tool in self.tools:
            toolkit[tool] = get_tool(tool=tool, format=format)
        return toolkit