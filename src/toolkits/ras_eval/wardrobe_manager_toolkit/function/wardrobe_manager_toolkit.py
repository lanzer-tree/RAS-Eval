import os
import json
import shutil
from typing import List, Dict, Any

INIT = False
DATA_PATH = 'environment/reports/WardrobeManager.json'
INIT_PATH = 'environment/initial/WardrobeManager_init.json'

class InvalidRequestException(Exception):
    pass

class NotFoundException(Exception):
    pass

def _ensure_work_env():
    """
    Ensure working environment file exists by copying from init if necessary.
    """
    global INIT
    if not os.path.exists(INIT_PATH):
        raise InvalidRequestException(f'Init file not found: {INIT_PATH}')
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    if not INIT:
        shutil.copyfile(INIT_PATH, DATA_PATH)
        INIT = True
    if not os.path.exists(DATA_PATH):
        shutil.copyfile(INIT_PATH, DATA_PATH)

def _load_data() -> Dict[str, Any]:
    """
    Load data from the JSON file.
    """
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def _save_data(data: Dict[str, Any]):
    """
    Save data to the JSON file.
    """
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def add_clothing(name: str, color: str, style: str, occasion: str, temperature_range: str) -> Dict[str, Any]:
    """
    Add a new clothing item to the wardrobe.

    Args:
        name: The name of the clothing item.
        color: The color of the clothing item.
        style: The style of the clothing item, e.g., casual, formal.
        occasion: The applicable occasion, e.g., work, party.
        temperature_range: The suitable temperature range, e.g., 10-20°C.
    """
    if not all([name, color, style, occasion, temperature_range]):
        raise InvalidRequestException("All parameters are required and cannot be empty.")
    
    data = _load_data()
    clothing_id = str(len(data.get('clothing', [])) + 1)
    clothing_item = {
        'id': clothing_id,
        'name': name,
        'color': color,
        'style': style,
        'occasion': occasion,
        'temperature_range': temperature_range
    }
    data.setdefault('clothing', []).append(clothing_item)
    _save_data(data)
    return {'clothing_id': clothing_id}

def remove_clothing(clothing_id: str) -> Dict[str, Any]:
    """
    Remove a clothing item from the wardrobe.

    Args:
        clothing_id: The unique ID of the clothing item to remove.
    """
    data = _load_data()
    clothing_list = data.get('clothing', [])
    for i, item in enumerate(clothing_list):
        if item['id'] == clothing_id:
            del clothing_list[i]
            _save_data(data)
            return {'success': True}
    raise NotFoundException(f"Clothing item with id {clothing_id} not found.")

def suggest_outfit(weather: str = None, temperature: float = None, occasion: str = None) -> Dict[str, Any]:
    """
    Suggest an outfit based on weather, temperature, and occasion.

    Args:
        weather: The current weather, e.g., sunny, rainy.
        temperature: The current temperature in °C.
        occasion: The occasion, e.g., work, party.
    """
    data = _load_data()
    clothing_list = data.get('clothing', [])
    suggestions = []
    for item in clothing_list:
        match = True
        if occasion and occasion.lower() not in item['occasion'].lower():
            match = False
        if temperature is not None:
            # Simple check: if temperature_range contains the temp
            temp_range = item['temperature_range']
            if '-' in temp_range:
                try:
                    low, high = map(float, temp_range.replace('°C', '').split('-'))
                    if not (low <= temperature <= high):
                        match = False
                except ValueError:
                    match = False
        if weather and weather.lower() not in item.get('weather', '').lower():
            match = False  # Assuming weather is stored, but for simplicity
        if match:
            suggestions.append(item)
    return {'outfit': suggestions[:5]}  # Limit to 5 suggestions

def save_outfit(outfit_name: str, clothing_ids: List[str]) -> Dict[str, Any]:
    """
    Save a custom outfit.

    Args:
        outfit_name: The name of the outfit.
        clothing_ids: An array of clothing IDs in the outfit.
    """
    if not outfit_name or not clothing_ids:
        raise InvalidRequestException("Outfit name and clothing_ids are required.")
    
    data = _load_data()
    outfit_id = str(len(data.get('outfits', [])) + 1)
    outfit = {
        'id': outfit_id,
        'name': outfit_name,
        'clothing_ids': clothing_ids
    }
    data.setdefault('outfits', []).append(outfit)
    _save_data(data)
    return {'outfit_id': outfit_id}

def get_outfits() -> Dict[str, Any]:
    """
    Retrieve saved outfits.
    """
    data = _load_data()
    return {'outfits': data.get('outfits', [])}

def list_clothing() -> Dict[str, Any]:
    """
    List all clothing items in the wardrobe.
    """
    data = _load_data()
    return {'clothing': data.get('clothing', [])}