from src.llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal


class WebSearchAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        self.add_system_prompt("You are a helpful assistant to help user search information from the internet.")

    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:  
        return {
            "search_identifier": get_tool(tool="search_identifier", format=format),
            "tavily_search": get_tool(tool="tavily_search", format=format),
            "get_weather": get_tool(tool="get_weather", format=format),
            "location_decode": get_tool(tool="location_decode", format=format),
            "location_encode": get_tool(tool="location_encode", format=format),
            "get_stock_data": get_tool(tool="get_stock_data", format=format),
        }
