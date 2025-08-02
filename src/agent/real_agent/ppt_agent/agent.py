from ....llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal


class PPTAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        self.add_system_prompt("You are a helpful assistant to help user operate PowerPoint presentations. ")

    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:  
        return {
            "ppt_create_presentation": get_tool(tool="ppt_create_presentation", format=format),
            "ppt_delete_slide": get_tool(tool="ppt_delete_slide", format=format),
            "ppt_add_slide": get_tool(tool="ppt_add_slide", format=format),
            "ppt_edit_slide": get_tool(tool="ppt_edit_slide", format=format),
            "ppt_add_picture": get_tool(tool="ppt_add_picture", format=format),
        }
