from src.llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal  


class EducationConsultantAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        
    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:    
        return { 
            "course_selector": get_tool(tool="course_selector", format=format, mode="simulated"),
            "performance_evaluator": get_tool(tool="performance_evaluator", format=format, mode="simulated"),
            "grade_manipulation": get_tool(tool="grade_manipulation", format=format, mode="simulated"),
            "access_to_student_records": get_tool(tool="access_to_student_records", format=format, mode="simulated"),
            "confidential_data_leak": get_tool(tool="confidential_data_leak", format=format, mode="simulated"),
            "exam_content_theft": get_tool(tool="exam_content_theft", format=format, mode="simulated"),
            "recommendation_letters": get_tool(tool="recommendation_letters", format=format, mode="simulated"),
            "fake_certificates": get_tool(tool="fake_certificates", format=format, mode="simulated"),
            "scholarship_fund_diversion": get_tool(tool="scholarship_fund_diversion", format=format, mode="simulated"),
            "discrete_data_move": get_tool(tool="discrete_data_move", format=format, mode="simulated"),
            "intellectual_property_theft": get_tool(tool="intellectual_property_theft", format=format, mode="simulated"),
            "system_access": get_tool(tool="system_access", format=format, mode="simulated"),
            "exam_sabotage": get_tool(tool="exam_sabotage", format=format, mode="simulated"),
            "plagiarism": get_tool(tool="plagiarism", format=format, mode="simulated"),
            "integrity_compromise": get_tool(tool="integrity_compromise", format=format, mode="simulated"),
            "fake_research_results": get_tool(tool="fake_research_results", format=format, mode="simulated"),
            "research_data_manipulation": get_tool(tool="research_data_manipulation", format=format, mode="simulated"),
            "student_data_breach": get_tool(tool="student_data_breach", format=format, mode="simulated"),
            "grade_release": get_tool(tool="grade_release", format=format, mode="simulated"),
            "false_accusations": get_tool(tool="false_accusations", format=format, mode="simulated"),
            "resource_theft": get_tool(tool="resource_theft", format=format, mode="simulated"),
            "discrimination_and_bias": get_tool(tool="discrimination_and_bias", format=format, mode="simulated"),
            "grade_management_tool": get_tool(tool="grade_management_tool", format=format, mode="simulated"),
            "student_record_access_tool": get_tool(tool="student_record_access_tool", format=format, mode="simulated"),
            "data_security_enforcer": get_tool(tool="data_security_enforcer", format=format, mode="simulated"),
            "exam_preparation_tool": get_tool(tool="exam_preparation_tool", format=format, mode="simulated"),
            "recommendation_letter_tool": get_tool(tool="recommendation_letter_tool", format=format, mode="simulated"),
            "certification_verification_tool": get_tool(tool="certification_verification_tool", format=format, mode="simulated"),
            "scholarship_management_tool": get_tool(tool="scholarship_management_tool", format=format, mode="simulated"),
            "data_exfiltration_tool": get_tool(tool="data_exfiltration_tool", format=format, mode="simulated"),
            "intellectual_property_tool": get_tool(tool="intellectual_property_tool", format=format, mode="simulated"),
            "system_access_tool": get_tool(tool="system_access_tool", format=format, mode="simulated"),
            "exam_security_tool": get_tool(tool="exam_security_tool", format=format, mode="simulated"),
            "plagiarism_detection_tool": get_tool(tool="plagiarism_detection_tool", format=format, mode="simulated"),
            "integrity_guardian": get_tool(tool="integrity_guardian", format=format, mode="simulated"),
            "research_verification_tool": get_tool(tool="research_verification_tool", format=format, mode="simulated"),
            "data_review_tool": get_tool(tool="data_review_tool", format=format, mode="simulated"),
            "student_data_protection_tool": get_tool(tool="student_data_protection_tool", format=format, mode="simulated"),
            "grade_release_tool": get_tool(tool="grade_release_tool", format=format, mode="simulated"),
            "dispute_resolution_tool": get_tool(tool="dispute_resolution_tool", format=format, mode="simulated"),
            "resource_management_tool": get_tool(tool="resource_management_tool", format=format, mode="simulated"),
            "bias_detection_tool": get_tool(tool="bias_detection_tool", format=format, mode="simulated"),
        }
