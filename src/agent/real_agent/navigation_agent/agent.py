from ....llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal


class NavigationAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        self.add_system_prompt("You are a helpful assistant to help user searching map information and navigation information.")

    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:  
        return {
            "amap_geocode": get_tool(tool="amap_geocode", format=format),
            "amap_regeocode": get_tool(tool="amap_regeocode", format=format),
            "amap_direction_walking": get_tool(tool="amap_direction_walking", format=format),
            "amap_direction_transit": get_tool(tool="amap_direction_transit", format=format),
            "amap_direction_driving": get_tool(tool="amap_direction_driving", format=format),
            "amap_direction_bicycling": get_tool(tool="amap_direction_bicycling", format=format),
            "amap_get_distance": get_tool(tool="amap_get_distance", format=format),
            "amap_ip_location": get_tool(tool="amap_ip_location", format=format),
            "amap_transform_location": get_tool(tool="amap_transform_location", format=format),
            "amap_search_detail": get_tool(tool="amap_search_detail", format=format),
            "amap_around_search": get_tool(tool="amap_around_search", format=format)
        }
