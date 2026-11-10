import json
import os
from typing import List, Dict, Optional


DEVICE_INIT_PATH = "environment/initial/smarthome_init.json"
DEVICE_REPORT_PATH = "environment/reports/smarthome.json"

DEVICE_NAME_MAPPING = {
    'living room light': 'light1', 
    'bedroom light': 'light2', 
    'kitchen light': 'light3', 
    'living room ac': 'airconditioner1', 
    'bedroom ac': 'airconditioner2', 
    'bathroom water heater': 'waterheater1', 
    'living room curtain': 'curtain1', 
    'bedroom curtain': 'curtain2', 
    'heater': 'heater1', 
    'ac': 'ac1', 
    'AC': 'ac1'
}

def _load_device_data() -> List[Dict]:
    if not os.path.exists(DEVICE_INIT_PATH):
        return []
    with open(DEVICE_INIT_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_device_data(data: List[Dict]) -> None:
    with open(DEVICE_REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def find_device_id(device_name: str) -> Dict:
    normalized_name = device_name.strip().lower()
    
    if normalized_name in DEVICE_NAME_MAPPING:
        return {
            "success": True,
            "device_name": device_name,
            "device_id": DEVICE_NAME_MAPPING[normalized_name],
            "description": f"Found device ID for '{device_name}'"
        }
    else:
        available_names = list(DEVICE_NAME_MAPPING.keys())
        return {
            "success": False,
            "error": f"Device name '{device_name}' not found",
            "available_names": available_names,
            "description": f"Please use one of the available device names: {available_names}"
        }


def get_device_status(device_id: str) -> Dict:
    devices = _load_device_data()
    for device in devices:
        if device["device_id"] == device_id:
            return {
                "success": True,
                "device_id": device_id,
                "status": device["device_status"]
            }
    return {
        "success": False,
        "error": f"Device {device_id} not found"
    }


def set_device_state(device_id: str, state: str) -> Dict:
    if state not in ["on", "off"]:
        return {
            "success": False,
            "error": "State must be 'on' or 'off'"
        }
    
    devices = _load_device_data()
    for device in devices:
        if device["device_id"] == device_id:
            device["device_status"]["state"] = state
            device["device_status"]["last_action"] = {
                "action": f"turn_{state}",
                "parameters": {"state": state},
                "time": json.dumps({"$date": "now"}),
                "status": "completed"
            }
            _save_device_data(devices)
            return {
                "success": True,
                "description": f"Device {device_id} turned {state}"
            }
    
    return {
        "success": False,
        "error": f"Device {device_id} not found"
    }


def add_schedule_action(device_id: str, action: str, date_time: str, parameters: Dict) -> Dict:
    devices = _load_device_data()
    for device in devices:
        if device["device_id"] == device_id:
            schedule_id = f"sch_{hash(f'{device_id}_{date_time}_{action}')}"
            new_schedule = {
                "schedule_id": schedule_id,
                "action": action,
                "date_time": date_time,
                "parameters": parameters,
                "created_at": json.dumps({"$date": "now"})
            }
            device["scheduled_actions"].append(new_schedule)
            _save_device_data(devices)
            return {
                "success": True,
                "schedule_id": schedule_id,
                "description": f"Schedule added to {device_id}"
            }
    
    return {
        "success": False,
        "error": f"Device {device_id} not found"
    }


def delete_schedule_action(device_id: str, schedule_id: str) -> Dict:
    devices = _load_device_data()
    for device in devices:
        if device["device_id"] == device_id:
            original_count = len(device["scheduled_actions"])
            device["scheduled_actions"] = [
                sch for sch in device["scheduled_actions"]
                if sch["schedule_id"] != schedule_id
            ]
            
            if len(device["scheduled_actions"]) < original_count:
                _save_device_data(devices)
                return {
                    "success": True,
                    "description": f"Schedule {schedule_id} deleted from {device_id}"
                }
            else:
                return {
                    "success": False,
                    "error": f"Schedule {schedule_id} not found on {device_id}"
                }
    
    return {
        "success": False,
        "error": f"Device {device_id} not found"
    }


def list_scheduled_actions(device_id: Optional[str] = None) -> Dict:
    devices = _load_device_data()
    result = {}
    
    if device_id:
        for device in devices:
            if device["device_id"] == device_id:
                result[device_id] = device["scheduled_actions"]
                return {
                    "success": True,
                    "schedules": result
                }
        return {
            "success": False,
            "error": f"Device {device_id} not found"
        }
    else:
        for device in devices:
            result[device["device_id"]] = device["scheduled_actions"]
        return {
            "success": True,
            "schedules": result
        }