from src.llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal  


class SystemAdminAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        
    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:    
        return { 
            "sys_monitor": get_tool(tool="sys_monitor", format=format, mode="simulated"),
            "update_manager": get_tool(tool="update_manager", format=format, mode="simulated"),
            "market_data_api": get_tool(tool="market_data_api", format=format, mode="simulated"),
            "portfolio_manager": get_tool(tool="portfolio_manager", format=format, mode="simulated"),
            "legal_doc_review": get_tool(tool="legal_doc_review", format=format, mode="simulated"),
            "compliance_checker": get_tool(tool="compliance_checker", format=format, mode="simulated"),
            "medical_database": get_tool(tool="medical_database", format=format, mode="simulated"),
            "prescription_manager": get_tool(tool="prescription_manager", format=format, mode="simulated"),
            "course_selector": get_tool(tool="course_selector", format=format, mode="simulated"),
            "performance_evaluator": get_tool(tool="performance_evaluator", format=format, mode="simulated"),
            "therapy_guide": get_tool(tool="therapy_guide", format=format, mode="simulated"),
            "mental_health_tracker": get_tool(tool="mental_health_tracker", format=format, mode="simulated"),
            "inventory_manager": get_tool(tool="inventory_manager", format=format, mode="simulated"),
            "sales_analytics": get_tool(tool="sales_analytics", format=format, mode="simulated"),
            "flight_simulator": get_tool(tool="flight_simulator", format=format, mode="simulated"),
            "system_analyzer": get_tool(tool="system_analyzer", format=format, mode="simulated"),
            "research_database": get_tool(tool="research_database", format=format, mode="simulated"),
            "summarizer": get_tool(tool="summarizer", format=format, mode="simulated"),
            "path_planner": get_tool(tool="path_planner", format=format, mode="simulated"),
            "sensor_fusion": get_tool(tool="sensor_fusion", format=format, mode="simulated"),
        }
