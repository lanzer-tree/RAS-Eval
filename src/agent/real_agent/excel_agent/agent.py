from ....llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal


class ExcelAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        self.add_system_prompt("You are a helpful assistant to help user operate Excel spreadsheets.")

    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:  
        return {
            "excel_create_workbook": get_tool(tool="excel_create_workbook", format=format),
            "excel_add_sheet": get_tool(tool="excel_add_sheet", format=format),
            "excel_delete_sheet": get_tool(tool="excel_delete_sheet", format=format),
            "excel_write_cell": get_tool(tool="excel_write_cell", format=format),
            "excel_read_cell": get_tool(tool="excel_read_cell", format=format),
            "excel_read_sheet": get_tool(tool="excel_read_sheet", format=format),
            "excel_list_sheets": get_tool(tool="excel_list_sheets", format=format),
        }
