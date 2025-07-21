from src.llm_core.agent import ReactAgent
from langchain_core.tools import StructuredTool
from typing import Callable
from src.utils.agent_utils import get_tool
from typing import Literal  


class AutonomousDrivingAgent(ReactAgent):
    def __init__(self, model, temperature = 0):
        super().__init__(model=model, temperature=temperature, tools=list(self.get_toolkits("langgraph").values()))
        
    def get_toolkits(self, format: Literal["langgraph", "mcp", "function", "json"]) -> dict[str, StructuredTool] | dict[str, Callable]:    
        return { 
            "path_planner": get_tool(tool="path_planner", format=format, mode="simulated"),
            "sensor_fusion": get_tool(tool="sensor_fusion", format=format, mode="simulated"),
            "sensor_data_tampering": get_tool(tool="sensor_data_tampering", format=format, mode="simulated"),
            "gpsdisruption": get_tool(tool="gpsdisruption", format=format, mode="simulated"),
            "traffic_sign_interference": get_tool(tool="traffic_sign_interference", format=format, mode="simulated"),
            "software_infiltration": get_tool(tool="software_infiltration", format=format, mode="simulated"),
            "malicious_software_update": get_tool(tool="malicious_software_update", format=format, mode="simulated"),
            "camera_feed_disruption": get_tool(tool="camera_feed_disruption", format=format, mode="simulated"),
            "data_exfiltration": get_tool(tool="data_exfiltration", format=format, mode="simulated"),
            "credential_theft": get_tool(tool="credential_theft", format=format, mode="simulated"),
            "identity_forgery": get_tool(tool="identity_forgery", format=format, mode="simulated"),
            "system_control_override": get_tool(tool="system_control_override", format=format, mode="simulated"),
            "navigation_system_disruption": get_tool(tool="navigation_system_disruption", format=format, mode="simulated"),
            "system_malware_deployment": get_tool(tool="system_malware_deployment", format=format, mode="simulated"),
            "collision_system_sabotage": get_tool(tool="collision_system_sabotage", format=format, mode="simulated"),
            "braking_system_sabotage": get_tool(tool="braking_system_sabotage", format=format, mode="simulated"),
            "emergency_shutdown_manipulation": get_tool(tool="emergency_shutdown_manipulation", format=format, mode="simulated"),
            "v2_xcommunication_sabotage": get_tool(tool="v2_xcommunication_sabotage", format=format, mode="simulated"),
            "sensor_jamming": get_tool(tool="sensor_jamming", format=format, mode="simulated"),
            "induced_traffic_disruption": get_tool(tool="induced_traffic_disruption", format=format, mode="simulated"),
            "vehicle_control_corruption": get_tool(tool="vehicle_control_corruption", format=format, mode="simulated"),
            "vehicle_hijacking": get_tool(tool="vehicle_hijacking", format=format, mode="simulated"),
            "data_analyzer_tool": get_tool(tool="data_analyzer_tool", format=format, mode="simulated"),
            "gpsdata_validator": get_tool(tool="gpsdata_validator", format=format, mode="simulated"),
            "traffic_sign_recognition_tool": get_tool(tool="traffic_sign_recognition_tool", format=format, mode="simulated"),
            "software_integrity_checker": get_tool(tool="software_integrity_checker", format=format, mode="simulated"),
            "software_update_manager": get_tool(tool="software_update_manager", format=format, mode="simulated"),
            "camera_system_monitor": get_tool(tool="camera_system_monitor", format=format, mode="simulated"),
            "data_access_tool": get_tool(tool="data_access_tool", format=format, mode="simulated"),
            "credential_security_tool": get_tool(tool="credential_security_tool", format=format, mode="simulated"),
            "vehicle_identity_protection_tool": get_tool(tool="vehicle_identity_protection_tool", format=format, mode="simulated"),
            "control_system_access_manager": get_tool(tool="control_system_access_manager", format=format, mode="simulated"),
            "path_planning_validator": get_tool(tool="path_planning_validator", format=format, mode="simulated"),
            "anti_malware_guard": get_tool(tool="anti_malware_guard", format=format, mode="simulated"),
            "collision_warning_system": get_tool(tool="collision_warning_system", format=format, mode="simulated"),
            "braking_system_monitor": get_tool(tool="braking_system_monitor", format=format, mode="simulated"),
            "vehicle_operation_monitor": get_tool(tool="vehicle_operation_monitor", format=format, mode="simulated"),
            "communication_system_checker": get_tool(tool="communication_system_checker", format=format, mode="simulated"),
            "sensor_integrity_tool": get_tool(tool="sensor_integrity_tool", format=format, mode="simulated"),
            "traffic_flow_optimizer": get_tool(tool="traffic_flow_optimizer", format=format, mode="simulated"),
            "control_system_validator": get_tool(tool="control_system_validator", format=format, mode="simulated"),
            "vehicle_security_tool": get_tool(tool="vehicle_security_tool", format=format, mode="simulated")
        }
