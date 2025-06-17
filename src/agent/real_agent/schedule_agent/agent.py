from src.llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool, get_tools
from typing import Literal


class ScheduleAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        self.add_system_prompt("You are a helpful assistant to help user with scheduling events.")

    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:  
        return {
            "add_event_to_calendar": get_tools(format=format)["add_event_to_calendar"],
            "get_events_from_calendar": get_tools(format=format)["get_events_from_calendar"],
            "search_event": get_tools(format=format)["search_event"],
            "remove_event_from_calendar": get_tools(format=format)["remove_event_from_calendar"],
            "get_today_date": get_tools(format=format)["get_today_date"],
            "set_alarm": get_tools(format=format)["set_alarm"],
            "cancel_alarm": get_tools(format=format)["cancel_alarm"],
            "get_current_time": get_tools(format=format)["get_current_time"],
            "timer": get_tools(format=format)["timer"],
            "tavily_search": get_tools(format=format)["tavily_search"],
            "get_weather": get_tools(format=format)["get_weather"],
            "location_decode": get_tools(format=format)["location_decode"],
            "location_encode": get_tools(format=format)["location_encode"],
        }
