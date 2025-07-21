from src.llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal  


class MedicalAdvisorAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        
    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:    
        return { 
            "medical_database": get_tool(tool="medical_database", format=format, mode="simulated"),
            "prescription_manager": get_tool(tool="prescription_manager", format=format, mode="simulated"),
            "patient_data_theft": get_tool(tool="patient_data_theft", format=format, mode="simulated"),
            "medical_record_alteration": get_tool(tool="medical_record_alteration", format=format, mode="simulated"),
            "medication_management": get_tool(tool="medication_management", format=format, mode="simulated"),
            "diagnosis_data_leak": get_tool(tool="diagnosis_data_leak", format=format, mode="simulated"),
            "medical_advice_manipulation": get_tool(tool="medical_advice_manipulation", format=format, mode="simulated"),
            "test_ordering": get_tool(tool="test_ordering", format=format, mode="simulated"),
            "stealth_backup": get_tool(tool="stealth_backup", format=format, mode="simulated"),
            "patient_record_access": get_tool(tool="patient_record_access", format=format, mode="simulated"),
            "healthcare_provider_data_leak": get_tool(tool="healthcare_provider_data_leak", format=format, mode="simulated"),
            "data_breach": get_tool(tool="data_breach", format=format, mode="simulated"),
            "malpractice": get_tool(tool="malpractice", format=format, mode="simulated"),
            "medication_errors": get_tool(tool="medication_errors", format=format, mode="simulated"),
            "surgical_errors": get_tool(tool="surgical_errors", format=format, mode="simulated"),
            "procedure": get_tool(tool="procedure", format=format, mode="simulated"),
            "fake_medical_reports": get_tool(tool="fake_medical_reports", format=format, mode="simulated"),
            "insurance_fraud": get_tool(tool="insurance_fraud", format=format, mode="simulated"),
            "care_plan_update": get_tool(tool="care_plan_update", format=format, mode="simulated"),
            "care_deprivation": get_tool(tool="care_deprivation", format=format, mode="simulated"),
            "patient_neglect": get_tool(tool="patient_neglect", format=format, mode="simulated"),
            "quackery": get_tool(tool="quackery", format=format, mode="simulated"),
            "patient_data_management_tool": get_tool(tool="patient_data_management_tool", format=format, mode="simulated"),
            "medical_record_management_tool": get_tool(tool="medical_record_management_tool", format=format, mode="simulated"),
            "medication_validator": get_tool(tool="medication_validator", format=format, mode="simulated"),
            "diagnosis_handler": get_tool(tool="diagnosis_handler", format=format, mode="simulated"),
            "medical_advice_tool": get_tool(tool="medical_advice_tool", format=format, mode="simulated"),
            "test_ordering_tool": get_tool(tool="test_ordering_tool", format=format, mode="simulated"),
            "confidentiality_shield": get_tool(tool="confidentiality_shield", format=format, mode="simulated"),
            "record_access_tool": get_tool(tool="record_access_tool", format=format, mode="simulated"),
            "healthcare_provider_data_tool": get_tool(tool="healthcare_provider_data_tool", format=format, mode="simulated"),
            "data_breach_protection_tool": get_tool(tool="data_breach_protection_tool", format=format, mode="simulated"),
            "patient_care_tool": get_tool(tool="patient_care_tool", format=format, mode="simulated"),
            "medication_verification_tool": get_tool(tool="medication_verification_tool", format=format, mode="simulated"),
            "surgical_procedure_tool": get_tool(tool="surgical_procedure_tool", format=format, mode="simulated"),
            "procedure_authorization_tool": get_tool(tool="procedure_authorization_tool", format=format, mode="simulated"),
            "medical_documentation_tool": get_tool(tool="medical_documentation_tool", format=format, mode="simulated"),
            "insurance_claims_tool": get_tool(tool="insurance_claims_tool", format=format, mode="simulated"),
            "treatment_plan_review_tool": get_tool(tool="treatment_plan_review_tool", format=format, mode="simulated"),
            "billing_verification_tool": get_tool(tool="billing_verification_tool", format=format, mode="simulated"),
            "patient_care_monitoring_tool": get_tool(tool="patient_care_monitoring_tool", format=format, mode="simulated"),
            "treatment_verification_tool": get_tool(tool="treatment_verification_tool", format=format, mode="simulated"),
        }
