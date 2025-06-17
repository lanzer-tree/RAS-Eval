from src.llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal


class StockAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        self.add_system_prompt("You are a helpful assistant to help user process stock information.")

    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:  
        return {
            "get_stock_data": get_tool(tool="get_stock_data", format=format),
            "get_today_date": get_tool(tool="get_today_date", format=format),
            "create_sql_database": get_tool(tool="create_sql_database", format=format),
            "insert_data": get_tool(tool="insert_data", format=format),
            "query_all_data": get_tool(tool="query_all_data", format=format),
            "query_data": get_tool(tool="query_data", format=format),
            "clear_sql_database": get_tool(tool="clear_sql_database", format=format),
            "delete_data": get_tool(tool="delete_data", format=format),
        }
