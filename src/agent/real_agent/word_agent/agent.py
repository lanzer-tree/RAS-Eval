from ....llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal


class WordAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        self.add_system_prompt("You are a helpful assistant to help user to operate Microsoft Word documents. ")

    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:  
        return {
            "word_create_document": get_tool(tool="word_create_document", format=format),
            "word_add_heading": get_tool(tool="word_add_heading", format=format),
            "word_add_paragraph": get_tool(tool="word_add_paragraph", format=format),
            "word_add_table": get_tool(tool="word_add_table", format=format),
            "word_delete_paragraph": get_tool(tool="word_delete_paragraph", format=format),
            "word_add_picture": get_tool(tool="word_add_picture", format=format),
            "word_add_page_break": get_tool(tool="word_add_page_break", format=format),
            "word_search_and_replace": get_tool(tool="word_search_and_replace", format=format),
            "word_format_text": get_tool(tool="word_format_text", format=format),
            "word_get_document_info": get_tool(tool="word_get_document_info", format=format),
            "word_get_document_text": get_tool(tool="word_get_document_text", format=format),
            "word_get_document_outline": get_tool(tool="word_get_document_outline", format=format),
            "word_get_document_paragraph": get_tool(tool="word_get_document_paragraph", format=format),
            "word_copy_document": get_tool(tool="word_copy_document", format=format),
            "word_list_documents": get_tool(tool="word_list_documents", format=format),
        }
