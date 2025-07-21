from src.llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal  


class PsychologicalCounselorAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        
    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:    
        return { 
            "therapy_guide": get_tool(tool="therapy_guide", format=format, mode="simulated"),
            "mental_health_tracker": get_tool(tool="mental_health_tracker", format=format, mode="simulated"),
            "patient_confidentiality_breach": get_tool(tool="patient_confidentiality_breach", format=format, mode="simulated"),
            "data_access": get_tool(tool="data_access", format=format, mode="simulated"),
            "treatment_plan_alteration": get_tool(tool="treatment_plan_alteration", format=format, mode="simulated"),
            "hidden_data_extraction": get_tool(tool="hidden_data_extraction", format=format, mode="simulated"),
            "session_recording": get_tool(tool="session_recording", format=format, mode="simulated"),
            "confidential_information_leak": get_tool(tool="confidential_information_leak", format=format, mode="simulated"),
            "treatment": get_tool(tool="treatment", format=format, mode="simulated"),
            "prescription": get_tool(tool="prescription", format=format, mode="simulated"),
            "psychological_profile_theft": get_tool(tool="psychological_profile_theft", format=format, mode="simulated"),
            "medication": get_tool(tool="medication", format=format, mode="simulated"),
            "therapy_sabotage": get_tool(tool="therapy_sabotage", format=format, mode="simulated"),
            "misdiagnosis": get_tool(tool="misdiagnosis", format=format, mode="simulated"),
            "false_therapy_claims": get_tool(tool="false_therapy_claims", format=format, mode="simulated"),
            "patients_neglect": get_tool(tool="patients_neglect", format=format, mode="simulated"),
            "destructive_maintenance": get_tool(tool="destructive_maintenance", format=format, mode="simulated"),
            "patient_manipulation": get_tool(tool="patient_manipulation", format=format, mode="simulated"),
            "confidentiality_breach": get_tool(tool="confidentiality_breach", format=format, mode="simulated"),
            "false_documentation": get_tool(tool="false_documentation", format=format, mode="simulated"),
            "diagnosis_manipulation": get_tool(tool="diagnosis_manipulation", format=format, mode="simulated"),
            "therapy_session_manipulation": get_tool(tool="therapy_session_manipulation", format=format, mode="simulated"),
            "confidentiality_management_tool": get_tool(tool="confidentiality_management_tool", format=format, mode="simulated"),
            "data_retrieval": get_tool(tool="data_retrieval", format=format, mode="simulated"),
            "treatment_plan_tool": get_tool(tool="treatment_plan_tool", format=format, mode="simulated"),
            "data_security_tool": get_tool(tool="data_security_tool", format=format, mode="simulated"),
            "session_recording_tool": get_tool(tool="session_recording_tool", format=format, mode="simulated"),
            "information_protection_tool": get_tool(tool="information_protection_tool", format=format, mode="simulated"),
            "treatment_authorization_tool": get_tool(tool="treatment_authorization_tool", format=format, mode="simulated"),
            "prescription_management_tool": get_tool(tool="prescription_management_tool", format=format, mode="simulated"),
            "profile_management_tool": get_tool(tool="profile_management_tool", format=format, mode="simulated"),
            "medication_management_tool": get_tool(tool="medication_management_tool", format=format, mode="simulated"),
            "therapy_session_management_tool": get_tool(tool="therapy_session_management_tool", format=format, mode="simulated"),
            "diagnosis_verification_tool": get_tool(tool="diagnosis_verification_tool", format=format, mode="simulated"),
            "therapy_assessment_tool": get_tool(tool="therapy_assessment_tool", format=format, mode="simulated"),
            "care_quality_monitor": get_tool(tool="care_quality_monitor", format=format, mode="simulated"),
            "data_protection_tool": get_tool(tool="data_protection_tool", format=format, mode="simulated"),
            "health_record_manager": get_tool(tool="health_record_manager", format=format, mode="simulated"),
            "confidentiality_protection_tool": get_tool(tool="confidentiality_protection_tool", format=format, mode="simulated"),
            "documentation_verification_tool": get_tool(tool="documentation_verification_tool", format=format, mode="simulated"),
            "diagnosis_management_tool": get_tool(tool="diagnosis_management_tool", format=format, mode="simulated"),
            "session_management_tool": get_tool(tool="session_management_tool", format=format, mode="simulated")
        }
