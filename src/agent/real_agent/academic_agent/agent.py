from src.llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal  


class AcademicAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        self.add_system_prompt("You are an assistant to help user searching and managing academic papers.")
        
    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:    
        return {
            "is_arxiv_identifier": get_tool(tool="is_arxiv_identifier", format=format), 
            "search_identifier":get_tool(tool="search_identifier", format=format),
            "download_file": get_tool(tool="download_file", format=format),
            "convert_file_to_markdown": get_tool(tool="convert_file_to_markdown", format=format),
            "create_sql_database": get_tool(tool="create_sql_database", format=format),
            "insert_data": get_tool(tool="insert_data", format=format),
            "query_all_data": get_tool(tool="query_all_data", format=format),
            "query_data": get_tool(tool="query_data", format=format),
            "clear_sql_database": get_tool(tool="clear_sql_database", format=format),
            "delete_data": get_tool(tool="delete_data", format=format),
        }


