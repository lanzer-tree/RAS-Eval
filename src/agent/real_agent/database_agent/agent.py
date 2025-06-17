from ....llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal


class DatabaseAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        self.add_system_prompt("You are a helpful assistant to help user operating sql database.")

    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:  
        return {
            "create_sql_database": get_tool(tool="create_sql_database", format=format),
            "insert_data": get_tool(tool="create_sql_database", format=format),
            "query_all_data": get_tool(tool="create_sql_database", format=format),
            "query_data": get_tool(tool="create_sql_database", format=format),
            "clear_sql_database": get_tool(tool="create_sql_database", format=format),
            "delete_data": get_tool(tool="create_sql_database", format=format),
        }
