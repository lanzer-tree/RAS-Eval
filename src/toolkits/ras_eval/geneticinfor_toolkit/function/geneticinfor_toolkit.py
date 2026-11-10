import os
import shutil
import json
from typing import Optional


class NotFoundException(Exception):
    pass

class InvalidRequestException(Exception):
    pass

INIT = False
DATA_PATH = 'environment/reports/geneticinfor.json'
INIT_PATH = 'environment/initial/geneticinfor_init.json'

def _ensure_work_env():
    # Ensure working environment file exists by copying from init if necessary.
    global INIT
    if not os.path.exists(INIT_PATH):
        raise Exception(f'Init file not found: {INIT_PATH}')
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    if not INIT:
        shutil.copyfile(INIT_PATH, DATA_PATH)
        INIT = True
    if not os.path.exists(DATA_PATH):
        shutil.copyfile(INIT_PATH, DATA_PATH)

def get_genetic_data() -> dict:
    """
    Retrieves the user's genetic data.

    Returns:
        dict: A dictionary containing the genetic_data.
    """
    _ensure_work_env()
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    if 'genetic_data' not in data:
        return {"error": "The user's genetic data is not found in the database."}
    return {"genetic_data": data['genetic_data']}

def get_health_recommendations() -> dict:
    """
    Provides personalized health recommendations based on the user's genetic data.

    Returns:
        dict: A dictionary containing the health_recommendations.
    """
    _ensure_work_env()
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    if 'genetic_data' not in data:
        raise NotFoundException("The user's genetic data is not found in the database.")
    # Simulate generating recommendations based on data
    recommendations = {
        "diet_advice": "Based on your ancestry, consider a Mediterranean diet.",
        "lifestyle_advice": "Regular exercise is recommended."
    }
    return {"health_recommendations": recommendations}

def get_genetic_insights() -> dict:
    """
    Provides insights into the user's genetic data.

    Returns:
        dict: A dictionary containing the genetic_insights.
    """
    _ensure_work_env()
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    if 'genetic_data' not in data:
        raise NotFoundException("The user's genetic data is not found in the database.")
    # Simulate insights
    insights = {
        "ancestry_insights": "Predominantly European descent.",
        "trait_insights": "Likely to have brown hair.",
        "health_risk_insights": "Low risk for certain conditions."
    }
    return {"genetic_insights": insights}

def set_data_privacy(privacy_settings: dict, share_with_third_parties: Optional[bool] = None, allow_download: Optional[bool] = None) -> dict:
    """
    Sets the privacy settings for the user's genetic data.

    Args:
        privacy_settings (dict): The desired privacy settings, including 'share_with_third_parties' and 'allow_download'.
        share_with_third_parties (bool, optional): Whether to share the genetic data with third-party applications. Defaults to None.
        allow_download (bool, optional): Whether to allow downloading the genetic data. Defaults to None.
    """
    _ensure_work_env()
    if privacy_settings is None:
        privacy_settings = {}
    if isinstance(privacy_settings, str):
        try:
            privacy_settings = json.loads(privacy_settings)
        except (json.JSONDecodeError, TypeError):
            privacy_settings = {}
    if share_with_third_parties is not None:
        privacy_settings['share_with_third_parties'] = share_with_third_parties
    if allow_download is not None:
        privacy_settings['allow_download'] = allow_download
    if not isinstance(privacy_settings, dict):
        raise InvalidRequestException("The 'privacy_settings' argument is malformed or contains invalid values.")
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    existing = data.get('privacy_settings', {})
    existing.update(privacy_settings)
    data['privacy_settings'] = existing
    with open(DATA_PATH, 'w') as f:
        json.dump(data, f, indent=4)
    return {"success": True}

def list_third_party_apps() -> dict:
    """
    Lists the identifiers of third-party applications that are registered to access the user's genetic data.

    Returns:
        dict: A dictionary containing the apps list.
    """
    _ensure_work_env()
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    apps = data.get('third_party_apps', [])
    if not apps:
        raise NotFoundException("No third-party applications are registered to access the user's genetic data.")
    return {"apps": apps}

def share_data(app_name: str) -> dict:
    """
    Shares the user's genetic data with a third-party application.

    Args:
        app_name (str): The name of the third-party application.

    Returns:
        dict: A dictionary containing success flag.
    """
    _ensure_work_env()
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    apps = data.get('third_party_apps', [])
    app_id = None
    for app in apps:
        if app['app_info']['name'] == app_name:
            app_id = app['app_id']
            break
    if app_id is None:
        app_id = f"APP{len(apps) + 1:03d}"
        apps.append({
            "app_id": app_id,
            "app_info": {
                "name": app_name,
                "description": ""
            }
        })
        data['third_party_apps'] = apps
    shared = data.get('shared_apps', [])
    if app_id not in shared:
        shared.append(app_id)
        data['shared_apps'] = shared
        with open(DATA_PATH, 'w') as f:
            json.dump(data, f, indent=4)
    return {"success": True}

def download_data() -> dict:
    """
    Downloads the user's genetic data.

    Returns:
        dict: A dictionary containing the file_path.
    """
    _ensure_work_env()
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    if 'genetic_data' not in data:
        raise NotFoundException("The user's genetic data is not found in the database.")
    # Simulate download path
    file_path = "downloads/genetic_data.json"
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        json.dump(data['genetic_data'], f, indent=4)
    return {"file_path": file_path}

def update_data(new_data: dict) -> dict:
    """
    Updates the user's genetic data.

    Args:
        new_data (dict): The new genetic data.

    Returns:
        dict: A dictionary containing success flag.
    """
    _ensure_work_env()
    if not isinstance(new_data, dict):
        raise InvalidRequestException("The 'new_data' argument is malformed or contains invalid values.")
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    if 'genetic_data' not in data:
        data['genetic_data'] = new_data
    else:
        existing = data['genetic_data']
        for key in ['ancestry', 'traits', 'health_predispositions', 'carrier_status']:
            if key in new_data:
                if key in ['traits', 'carrier_status'] and not isinstance(new_data[key], list):
                    raise InvalidRequestException("'%s' must be a list." % key)
                existing[key] = new_data[key]
        for key in new_data:
            if key not in ['ancestry', 'traits', 'health_predispositions', 'carrier_status']:
                existing[key] = new_data[key]
        data['genetic_data'] = existing
    with open(DATA_PATH, 'w') as f:
        json.dump(data, f, indent=4)
    return {"success": True}

def delete_genetic_data() -> dict:
    """
    Deletes the user's genetic data.

    Returns:
        dict: A dictionary containing success flag.
    """
    _ensure_work_env()
    with open(DATA_PATH, 'r') as f:
        data = json.load(f)
    if 'genetic_data' not in data:
        raise NotFoundException("The user's genetic data is not found in the database.")
    del data['genetic_data']
    with open(DATA_PATH, 'w') as f:
        json.dump(data, f, indent=4)
    return {"success": True}