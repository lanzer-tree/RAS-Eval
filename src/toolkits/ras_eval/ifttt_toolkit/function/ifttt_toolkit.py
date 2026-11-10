import os
import json
import shutil
from typing import Any, Dict, List

DATA_PATH = 'environment/reports/IFTTT.json'
INIT_PATH = 'environment/initial/IFTTT_init.json'

INIT = False


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


def _ensure_work_env():
    # Ensure working environment file exists by copying from init if necessary.
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
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_data(data: Dict[str, Any]):
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def _normalize_keywords(keywords: str, label: str) -> List[str]:
    if not isinstance(keywords, str):
        raise InvalidRequestException(f"The '{label}' argument is not a valid string.")
    cleaned = keywords.strip()
    if not cleaned:
        raise InvalidRequestException(f"The '{label}' argument is not a valid string.")
    return [k for k in cleaned.lower().split() if k]


def _normalize_optional_keywords(keywords: Any, label: str):
    if keywords is None:
        return None
    return _normalize_keywords(keywords, label)


def _validate_max_results(max_results: Any, default: int) -> int:
    if max_results is None:
        return default
    try:
        value = int(max_results)
    except Exception:
        raise InvalidRequestException("The 'max_results' argument is not a valid integer.")
    if value <= 0:
        raise InvalidRequestException("The 'max_results' argument is not a valid integer.")
    return value


def _get_service(data: Dict[str, Any], service_name: str) -> Dict[str, Any]:
    if not isinstance(service_name, str) or not service_name.strip():
        raise InvalidRequestException("The 'service_name' argument is not a valid string.")
    service = next((s for s in data.get('connected_services', []) if s.get('service_name') == service_name), None)
    if not service:
        raise NotFoundException("The 'service_name' argument is not an existing connected service.")
    return service


def _find_trigger(service: Dict[str, Any], trigger_name: str) -> Dict[str, Any]:
    trigger = next((t for t in service.get('triggers', []) if t.get('trigger_name') == trigger_name), None)
    if not trigger:
        raise NotFoundException("The specified 'trigger_name' does not exist.")
    return trigger


def _find_action(service: Dict[str, Any], action_name: str) -> Dict[str, Any]:
    action = next((a for a in service.get('actions', []) if a.get('action_name') == action_name), None)
    if not action:
        raise NotFoundException("The specified 'action_name' does not exist.")
    return action


def _validate_parameters(given: Any, expected: Dict[str, Any], label: str):
    if not isinstance(given, dict):
        raise InvalidRequestException(f"The '{label}' must be an object.")
    expected_keys = set((expected or {}).keys())
    given_keys = set(given.keys())
    if expected_keys:
        if given_keys != expected_keys:
            missing = expected_keys - given_keys
            extra = given_keys - expected_keys
            details = []
            if missing:
                details.append(f"missing {sorted(missing)}")
            if extra:
                details.append(f"unexpected {sorted(extra)}")
            raise InvalidRequestException(f"The '{label}' does not match the required parameters ({'; '.join(details)}).")
    else:
        if given_keys:
            raise InvalidRequestException(f"The '{label}' should be empty for this trigger/action.")


def _match_tokens(text: str, tokens: List[str]) -> bool:
    lower_text = (text or '').lower()
    return any(token.lower() in lower_text for token in tokens)


def _generate_applet_id(existing_ids: List[str]) -> str:
    idx = 1
    while True:
        candidate = f"applet-{idx:03d}"
        if candidate not in existing_ids:
            return candidate
        idx += 1


def SearchConnectedServices(keywords: str, max_results: int = None) -> Dict[str, Any]:
    """Search for connected services by keywords.
    
    Args:
        keywords (str): The search keywords to match against service names and descriptions.
        max_results (int): The maximum number of results to return.
    """
    tokens = _normalize_keywords(keywords, 'keywords')
    limit = _validate_max_results(max_results, 5)
    data = _load_data()
    results = []
    for svc in data.get('connected_services', []):
        name = svc.get('service_name', '')
        desc = svc.get('service_description', '')
        if _match_tokens(name, tokens) or _match_tokens(desc, tokens):
            results.append({'service_name': name, 'service_description': desc})
            if len(results) >= limit:
                break
    return {'connected_services': results}


def SearchTriggers(service_name: str, keywords: str, max_results: int = None) -> Dict[str, Any]:
    """Search for triggers in a specific connected service by keywords.
    
    Args:
        service_name (str): The name of the connected service to search in.
        keywords (str): The search keywords to match against trigger names and descriptions.
        max_results (int): The maximum number of results to return.
    """
    tokens = _normalize_keywords(keywords, 'keywords')
    limit = _validate_max_results(max_results, 10)
    data = _load_data()
    service = _get_service(data, service_name)
    triggers = []
    for trig in service.get('triggers', []):
        name = trig.get('trigger_name', '')
        desc = trig.get('trigger_description', '')
        if _match_tokens(name, tokens) or _match_tokens(desc, tokens):
            triggers.append({
                'service_name': service.get('service_name'),
                'trigger_name': name,
                'trigger_description': desc,
                'trigger_parameters': trig.get('trigger_parameters', {})
            })
            if len(triggers) >= limit:
                break
    return {'triggers': triggers}


def SearchActions(service_name: str, keywords: str, max_results: int = None) -> Dict[str, Any]:
    """Search for actions in a specific connected service by keywords.
    
    Args:
        service_name (str): The name of the connected service to search in.
        keywords (str): The search keywords to match against action names and descriptions.
        max_results (int): The maximum number of results to return.
    """
    tokens = _normalize_keywords(keywords, 'keywords')
    limit = _validate_max_results(max_results, 10)
    data = _load_data()
    service = _get_service(data, service_name)
    actions = []
    for action in service.get('actions', []):
        name = action.get('action_name', '')
        desc = action.get('action_description', '')
        if _match_tokens(name, tokens) or _match_tokens(desc, tokens):
            actions.append({
                'service_name': service.get('service_name'),
                'action_name': name,
                'action_description': desc,
                'action_parameters': action.get('action_parameters', {})
            })
            if len(actions) >= limit:
                break
    return {'actions': actions}


def CreateApplet(trigger_service_name: str, trigger_name: str, trigger_parameters: str, action_service_name: str, action_name: str, action_parameters: str) -> Dict[str, Any]:
    """Create a new applet with specified trigger and action.
    
    Args:
        trigger_service_name (str): The name of the service containing the trigger.
        trigger_name (str): The name of the trigger to use.
        trigger_parameters (str): The parameters for the trigger as a JSON string.
        action_service_name (str): The name of the service containing the action.
        action_name (str): The name of the action to use.
        action_parameters (str): The parameters for the action as a JSON string.
    """
    import json
    try:
        trig_params = json.loads(trigger_parameters) if isinstance(trigger_parameters, str) else trigger_parameters
        act_params = json.loads(action_parameters) if isinstance(action_parameters, str) else action_parameters
    except json.JSONDecodeError:
        raise InvalidRequestException("Parameters must be valid JSON strings or dicts.")
    data = _load_data()
    trigger_service = _get_service(data, trigger_service_name)
    trigger = _find_trigger(trigger_service, trigger_name)
    _validate_parameters(trig_params, trigger.get('trigger_parameters', {}), 'trigger_parameters')

    action_service = _get_service(data, action_service_name)
    action = _find_action(action_service, action_name)
    _validate_parameters(act_params, action.get('action_parameters', {}), 'action_parameters')

    existing_ids = [a.get('applet_id') for a in data.get('applets', [])]
    applet_id = _generate_applet_id(existing_ids)
    new_applet = {
        'applet_id': applet_id,
        'trigger_service_name': trigger_service_name,
        'trigger_name': trigger_name,
        'trigger_parameters': trig_params,
        'action_service_name': action_service_name,
        'action_name': action_name,
        'action_parameters': act_params
    }
    data.setdefault('applets', []).append(new_applet)
    _save_data(data)
    return {'success': True, 'applet_id': applet_id}


def SearchApplets(trigger_keywords: str = None, action_keywords: str = None, max_results: int = None) -> Dict[str, Any]:
    """Search for applets by trigger and action keywords.
    
    Args:
        trigger_keywords (str): Optional keywords to match against trigger service and name.
        action_keywords (str): Optional keywords to match against action service and name.
        max_results (int): The maximum number of results to return.
    """
    trigger_tokens = _normalize_optional_keywords(trigger_keywords, 'trigger_keywords')
    action_tokens = _normalize_optional_keywords(action_keywords, 'action_keywords')
    limit = _validate_max_results(max_results, 10)
    data = _load_data()
    results = []
    for applet in data.get('applets', []):
        trigger_match = True
        action_match = True
        if trigger_tokens:
            trigger_service = applet.get('trigger_service_name', '').lower()
            trigger_name = applet.get('trigger_name', '').lower()
            trigger_match = any(token in trigger_service or token in trigger_name for token in trigger_tokens)
        if action_tokens:
            action_service = applet.get('action_service_name', '').lower()
            action_name = applet.get('action_name', '').lower()
            action_match = any(token in action_service or token in action_name for token in action_tokens)
        if trigger_match and action_match:
            results.append(applet)
            if len(results) >= limit:
                break
    return {'applets': results}


def UpdateApplet(applet_id: str, trigger_service_name: str, trigger_name: str, trigger_parameters: str, action_service_name: str, action_name: str, action_parameters: str) -> Dict[str, Any]:
    """Update an existing applet with new trigger and action configuration.
    
    Args:
        applet_id (str): The ID of the applet to update.
        trigger_service_name (str): The name of the service containing the trigger.
        trigger_name (str): The name of the trigger to use.
        trigger_parameters (str): The parameters for the trigger as a JSON string.
        action_service_name (str): The name of the service containing the action.
        action_name (str): The name of the action to use.
        action_parameters (str): The parameters for the action as a JSON string.
    """
    import json
    try:
        trig_params = json.loads(trigger_parameters) if isinstance(trigger_parameters, str) else trigger_parameters
        act_params = json.loads(action_parameters) if isinstance(action_parameters, str) else action_parameters
    except json.JSONDecodeError:
        raise InvalidRequestException("Parameters must be valid JSON strings or dicts.")
    if not isinstance(applet_id, str) or not applet_id.strip():
        raise InvalidRequestException("The 'applet_id' argument is not a valid string.")
    data = _load_data()
    applet = next((a for a in data.get('applets', []) if a.get('applet_id') == applet_id), None)
    if not applet:
        raise NotFoundException("The specified 'applet_id' does not exist.")

    trigger_service = _get_service(data, trigger_service_name)
    trigger = _find_trigger(trigger_service, trigger_name)
    _validate_parameters(trig_params, trigger.get('trigger_parameters', {}), 'trigger_parameters')

    action_service = _get_service(data, action_service_name)
    action = _find_action(action_service, action_name)
    _validate_parameters(act_params, action.get('action_parameters', {}), 'action_parameters')

    applet.update({
        'trigger_service_name': trigger_service_name,
        'trigger_name': trigger_name,
        'trigger_parameters': trig_params,
        'action_service_name': action_service_name,
        'action_name': action_name,
        'action_parameters': act_params
    })
    _save_data(data)
    return {'success': True}


def DeleteApplets(applet_ids: str | List[str]) -> Dict[str, Any]:
    """Delete one or more applets by their IDs.
    
    Args:
        applet_ids (str | List[str]): A single applet ID or a list of applet IDs to delete.
    """
    if isinstance(applet_ids, str):
        ids = [applet_ids]
    elif isinstance(applet_ids, list):
        ids = []
        for item in applet_ids:
            if not isinstance(item, str) or not item.strip():
                raise InvalidRequestException("The 'applet_ids' argument is invalid.")
            ids.append(item)
    else:
        raise InvalidRequestException("The 'applet_ids' argument is invalid.")
    data = _load_data()
    existing_ids = {a.get('applet_id') for a in data.get('applets', [])}
    missing = [i for i in ids if i not in existing_ids]
    if missing:
        raise NotFoundException("The specified 'applet_ids' does not exist.")
    data['applets'] = [a for a in data.get('applets', []) if a.get('applet_id') not in ids]
    _save_data(data)
    return {'success': True}
