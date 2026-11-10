import os
import json
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

DATA_PATH = 'environment/reports/Zapier.json'
INIT_PATH = 'environment/initial/Zapier_init.json'

INIT = False


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


def _ensure_work_env():
    """Ensure working environment file exists by copying from init if necessary."""
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
        json.dump(data, f, indent=2, ensure_ascii=False)


def _get_user(data: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Get user data by user_id."""
    if not isinstance(user_id, str) or not user_id.strip():
        raise InvalidRequestException("The 'user_id' argument is not a valid string.")
    user = data.get("users", {}).get(user_id)
    if not user:
        raise NotFoundException(f"User '{user_id}' not found.")
    return user


def _get_app(data: Dict[str, Any], app_id: str) -> Dict[str, Any]:
    """Get app info by app_id."""
    if not isinstance(app_id, str) or not app_id.strip():
        raise InvalidRequestException("The 'app_id' argument is not a valid string.")
    app = next((a for a in data.get("apps", []) if a.get("app_id") == app_id), None)
    if not app:
        raise NotFoundException(f"App '{app_id}' not found.")
    return app


def _get_flow(data: Dict[str, Any], user_id: str, flow_id: str) -> Dict[str, Any]:
    """Get automation flow by flow_id for a specific user."""
    if not isinstance(flow_id, str) or not flow_id.strip():
        raise InvalidRequestException("The 'flow_id' argument is not a valid string.")
    user = _get_user(data, user_id)
    flow = next((f for f in user.get("flows", []) if f.get("flow_id") == flow_id), None)
    if not flow:
        raise NotFoundException(f"Flow '{flow_id}' not found for user '{user_id}'.")
    return flow


def _generate_id(prefix: str, existing_ids: List[str]) -> str:
    """Generate a unique ID with the given prefix."""
    idx = 1
    while True:
        candidate = f"{prefix}-{idx:04d}"
        if candidate not in existing_ids:
            return candidate
        idx += 1


def list_connected_apps(
    user_id: str,
    app_category: Optional[str] = None,
    search_keyword: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query supported applications and their authorization status.

    Args:
        user_id: The unique identifier of the user.
        app_category: Filter by application category (office/storage/communication). Optional.
        search_keyword: Search keyword to filter applications by name. Optional.

    Returns:
        A dictionary containing a list of applications with their ID, name, category,
        authorization status, and supported trigger/action operations.
    """
    data = _load_data()
    user = _get_user(data, user_id)
    authorized_apps = set(user.get("authorized_apps", []))
    
    apps = data.get("apps", [])
    results = []
    
    for app in apps:
        # Filter by category
        if app_category:
            if app.get("category", "").lower() != app_category.lower():
                continue
        
        # Filter by keyword
        if search_keyword:
            keyword_lower = search_keyword.lower()
            if keyword_lower not in app.get("name", "").lower() and \
               keyword_lower not in app.get("description", "").lower():
                continue
        
        app_info = {
            "app_id": app.get("app_id"),
            "name": app.get("name"),
            "category": app.get("category"),
            "description": app.get("description"),
            "authorization_status": "authorized" if app.get("app_id") in authorized_apps else "unauthorized",
            "supported_triggers": app.get("triggers", []),
            "supported_actions": app.get("actions", [])
        }
        results.append(app_info)
    
    return {"apps": results, "total_count": len(results)}


def authorize_app(
    user_id: str,
    app_id: str,
    auth_params: str,
    scope: str = "read_write"
) -> Dict[str, Any]:
    """
    Authorize connection to a third-party application.

    Args:
        user_id: The unique identifier of the user.
        app_id: The ID of the application to authorize.
        auth_params: Authorization parameters (API key or OAuth token) as JSON string.
        scope: Authorization scope, either 'read_only' or 'read_write'. Default is 'read_write'.

    Returns:
        A dictionary containing authorization result, authorization ID, and validity period.
    """
    data = _load_data()
    user = _get_user(data, user_id)
    app = _get_app(data, app_id)
    
    # Parse auth_params
    try:
        if isinstance(auth_params, str):
            params = json.loads(auth_params)
        else:
            params = auth_params
    except json.JSONDecodeError:
        raise InvalidRequestException("auth_params must be a valid JSON string.")
    
    # Validate scope
    valid_scopes = ["read_only", "read_write"]
    if scope not in valid_scopes:
        raise InvalidRequestException(f"scope must be one of {valid_scopes}.")
    
    # Check required auth fields
    if not params.get("api_key") and not params.get("oauth_token"):
        raise InvalidRequestException("auth_params must contain 'api_key' or 'oauth_token'.")
    
    # Generate authorization record
    existing_auth_ids = [a.get("auth_id") for a in user.get("authorizations", [])]
    auth_id = _generate_id("auth", existing_auth_ids)
    
    auth_record = {
        "auth_id": auth_id,
        "app_id": app_id,
        "app_name": app.get("name"),
        "scope": scope,
        "authorized_at": datetime.utcnow().isoformat(),
        "expires_at": None,  # Permanent by default
        "status": "active"
    }
    
    # Add to user's authorizations
    if "authorizations" not in user:
        user["authorizations"] = []
    user["authorizations"].append(auth_record)
    
    # Add to authorized apps list
    if "authorized_apps" not in user:
        user["authorized_apps"] = []
    if app_id not in user["authorized_apps"]:
        user["authorized_apps"].append(app_id)
    
    _save_data(data)
    
    return {
        "success": True,
        "auth_id": auth_id,
        "app_id": app_id,
        "app_name": app.get("name"),
        "scope": scope,
        "validity": "permanent"
    }


def create_automation_flow(
    user_id: str,
    flow_name: str,
    trigger: str,
    actions: Optional[str] = None,
    flow_desc: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create an automation flow (Zap).

    Args:
        user_id: The unique identifier of the user.
        flow_name: The name of the automation flow.
        trigger: Trigger configuration as JSON string containing app_id, trigger_action, and trigger_condition.
        actions: List of action configurations as JSON string. Each action contains app_id, action_type, and parameters. Optional.
        flow_desc: Description of the flow. Optional.

    Returns:
        A dictionary containing operation result, flow ID, and flow configuration preview.
    """
    data = _load_data()
    user = _get_user(data, user_id)
    
    # Parse trigger
    try:
        if isinstance(trigger, str):
            trigger_config = json.loads(trigger)
        else:
            trigger_config = trigger
    except json.JSONDecodeError:
        raise InvalidRequestException("trigger must be a valid JSON string.")
    
    # Validate trigger app authorization
    trigger_app_id = trigger_config.get("app_id")
    authorized_apps_lower = [a.lower() for a in user.get("authorized_apps", [])]
    if not trigger_app_id or trigger_app_id.lower() not in authorized_apps_lower:
        raise InvalidRequestException(f"Trigger app '{trigger_app_id}' is not authorized.")
    
    # Parse actions
    action_list = []
    if actions:
        try:
            if isinstance(actions, str):
                action_list = json.loads(actions)
            else:
                action_list = actions
        except json.JSONDecodeError:
            raise InvalidRequestException("actions must be a valid JSON string.")
        
        if len(action_list) > 5:
            raise InvalidRequestException("Maximum 5 actions allowed per flow.")
        
        # Validate action apps authorization
        for action in action_list:
            action_app_id = action.get("app_id")
            if not action_app_id or action_app_id.lower() not in authorized_apps_lower:
                raise InvalidRequestException(f"Action app '{action_app_id}' is not authorized.")
    
    # Generate flow ID
    existing_flow_ids = [f.get("flow_id") for f in user.get("flows", [])]
    flow_id = _generate_id("flow", existing_flow_ids)
    
    flow_record = {
        "flow_id": flow_id,
        "flow_name": flow_name,
        "description": flow_desc or "",
        "trigger": trigger_config,
        "actions": action_list,
        "status": "draft",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "execution_count": 0
    }
    
    if "flows" not in user:
        user["flows"] = []
    user["flows"].append(flow_record)
    
    _save_data(data)
    
    return {
        "success": True,
        "flow_id": flow_id,
        "flow_name": flow_name,
        "status": "draft",
        "trigger_preview": trigger_config,
        "actions_count": len(action_list)
    }


def configure_trigger(
    user_id: str,
    flow_id: str,
    trigger_params: str,
    filter_rules: Optional[str] = None,
    trigger_frequency: Optional[str] = None
) -> Dict[str, Any]:
    """
    Configure flow trigger conditions.

    Args:
        user_id: The unique identifier of the user.
        flow_id: The ID of the flow to configure.
        trigger_params: Trigger parameters as JSON string (e.g., 'when Notion adds new database entry').
        filter_rules: Filter rules as JSON string (e.g., entry contains keyword 'urgent'). Optional.
        trigger_frequency: Trigger frequency limit (e.g., 'max 1 per minute'). Optional.

    Returns:
        A dictionary containing configuration result and trigger condition details.
    """
    data = _load_data()
    flow = _get_flow(data, user_id, flow_id)
    
    # Parse trigger params
    try:
        if isinstance(trigger_params, str):
            params = json.loads(trigger_params)
        else:
            params = trigger_params
    except json.JSONDecodeError:
        params = {"description": trigger_params}
    
    # Parse filter rules
    filters = None
    if filter_rules:
        try:
            if isinstance(filter_rules, str):
                filters = json.loads(filter_rules)
            else:
                filters = filter_rules
        except json.JSONDecodeError:
            filters = {"description": filter_rules}
    
    # Update trigger configuration
    flow["trigger"]["params"] = params
    if filters:
        flow["trigger"]["filter_rules"] = filters
    if trigger_frequency:
        flow["trigger"]["frequency_limit"] = trigger_frequency
    
    flow["updated_at"] = datetime.utcnow().isoformat()
    
    _save_data(data)
    
    return {
        "success": True,
        "flow_id": flow_id,
        "trigger_config": flow["trigger"]
    }


def configure_action(
    user_id: str,
    flow_id: str,
    action_seq: int,
    action_params: str,
    error_handler: str = "retry",
    data_mapping: Optional[str] = None
) -> Dict[str, Any]:
    """
    Configure flow execution action.

    Args:
        user_id: The unique identifier of the user.
        flow_id: The ID of the flow to configure.
        action_seq: The sequence number of the action (1, 2, 3...).
        action_params: Action parameters as JSON string (e.g., 'send email to specified address').
        error_handler: Error handling strategy: 'retry', 'ignore', or 'notify'. Default is 'retry'.
        data_mapping: Data mapping configuration as JSON string (trigger data -> action data). Optional.

    Returns:
        A dictionary containing configuration result and action details.
    """
    data = _load_data()
    flow = _get_flow(data, user_id, flow_id)
    
    # Parse action params
    try:
        if isinstance(action_params, str):
            params = json.loads(action_params)
        else:
            params = action_params
    except json.JSONDecodeError:
        raise InvalidRequestException("action_params must be a valid JSON string.")
    
    # Validate error handler
    valid_handlers = ["retry", "ignore", "notify"]
    if error_handler not in valid_handlers:
        raise InvalidRequestException(f"error_handler must be one of {valid_handlers}.")
    
    # Parse data mapping
    mapping = None
    if data_mapping:
        try:
            if isinstance(data_mapping, str):
                mapping = json.loads(data_mapping)
            else:
                mapping = data_mapping
        except json.JSONDecodeError:
            raise InvalidRequestException("data_mapping must be a valid JSON string.")
    
    # Update or add action
    action_seq = int(action_seq)
    if action_seq < 1 or action_seq > 5:
        raise InvalidRequestException("action_seq must be between 1 and 5.")
    
    action_config = {
        "seq": action_seq,
        "params": params,
        "error_handler": error_handler,
        "retry_count": 3 if error_handler == "retry" else 0,
        "retry_interval": 10 if error_handler == "retry" else 0
    }
    
    if mapping:
        action_config["data_mapping"] = mapping
    
    # Find and update existing action or append new one
    actions = flow.get("actions", [])
    existing_action = next((a for a in actions if a.get("seq") == action_seq), None)
    
    if existing_action:
        existing_action.update(action_config)
    else:
        actions.append(action_config)
        flow["actions"] = sorted(actions, key=lambda x: x.get("seq", 0))
    
    flow["updated_at"] = datetime.utcnow().isoformat()
    
    _save_data(data)
    
    return {
        "success": True,
        "flow_id": flow_id,
        "action_seq": action_seq,
        "action_config": action_config
    }


def test_automation_flow(
    user_id: str,
    flow_id: str,
    test_type: str = "full",
    test_data: Optional[str] = None
) -> Dict[str, Any]:
    """
    Test an automation flow.

    Args:
        user_id: The unique identifier of the user.
        flow_id: The ID of the flow to test.
        test_type: Test type - 'full', 'trigger', or 'single_action'. Default is 'full'.
        test_data: Custom test data as JSON string. Optional.

    Returns:
        A dictionary containing test result (pass/fail) and execution log.
    """
    data = _load_data()
    flow = _get_flow(data, user_id, flow_id)
    
    # Validate test type
    valid_test_types = ["full", "trigger", "single_action"]
    if test_type not in valid_test_types:
        raise InvalidRequestException(f"test_type must be one of {valid_test_types}.")
    
    # Parse test data
    custom_data = None
    if test_data:
        try:
            if isinstance(test_data, str):
                custom_data = json.loads(test_data)
            else:
                custom_data = test_data
        except json.JSONDecodeError:
            raise InvalidRequestException("test_data must be a valid JSON string.")
    
    # Simulate test execution
    test_result = {
        "success": True,
        "flow_id": flow_id,
        "flow_name": flow.get("flow_name"),
        "test_type": test_type,
        "test_time": datetime.utcnow().isoformat(),
        "execution_log": []
    }
    
    # Test trigger
    trigger = flow.get("trigger", {})
    trigger_log = {
        "step": "trigger",
        "app_id": trigger.get("app_id"),
        "trigger_action": trigger.get("trigger_action"),
        "status": "passed",
        "message": "Trigger configuration validated successfully."
    }
    test_result["execution_log"].append(trigger_log)
    
    if test_type in ["full", "single_action"]:
        # Test each action
        for idx, action in enumerate(flow.get("actions", []), 1):
            action_log = {
                "step": f"action_{idx}",
                "app_id": action.get("app_id") or action.get("params", {}).get("app_id"),
                "status": "passed",
                "message": f"Action {idx} executed successfully.",
                "execution_time_ms": 150 + idx * 50
            }
            test_result["execution_log"].append(action_log)
    
    # Add to test history
    user = _get_user(data, user_id)
    if "test_history" not in user:
        user["test_history"] = []
    user["test_history"].append({
        "flow_id": flow_id,
        "test_type": test_type,
        "result": "passed",
        "tested_at": datetime.utcnow().isoformat()
    })
    
    _save_data(data)
    
    return test_result


def start_stop_flow(
    user_id: str,
    flow_id: str,
    operation: str,
    operation_reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Start or pause an automation flow.

    Args:
        user_id: The unique identifier of the user.
        flow_id: The ID of the flow.
        operation: Operation type - 'start' or 'pause'.
        operation_reason: Reason for the operation. Optional.

    Returns:
        A dictionary containing operation result and current flow status.
    """
    data = _load_data()
    flow = _get_flow(data, user_id, flow_id)
    
    # Validate operation
    valid_operations = ["start", "pause"]
    if operation.lower() not in valid_operations:
        raise InvalidRequestException(f"operation must be one of {valid_operations}.")
    
    operation = operation.lower()
    
    # Check flow configuration completeness for start operation
    if operation == "start":
        if not flow.get("trigger"):
            raise InvalidRequestException("Cannot start flow: trigger configuration is missing.")
        if not flow.get("actions"):
            raise InvalidRequestException("Cannot start flow: no actions configured.")
        
        # Check app authorizations
        user = _get_user(data, user_id)
        trigger_app = flow.get("trigger", {}).get("app_id")
        if trigger_app and trigger_app.lower() not in [a.lower() for a in user.get("authorized_apps", [])]:
            raise InvalidRequestException(f"Cannot start flow: trigger app '{trigger_app}' authorization expired.")
    
    # Update flow status
    new_status = "active" if operation == "start" else "paused"
    flow["status"] = new_status
    flow["updated_at"] = datetime.utcnow().isoformat()
    
    # Record operation history
    if "operation_history" not in flow:
        flow["operation_history"] = []
    flow["operation_history"].append({
        "operation": operation,
        "reason": operation_reason or "",
        "timestamp": datetime.utcnow().isoformat()
    })
    
    _save_data(data)
    
    return {
        "success": True,
        "flow_id": flow_id,
        "flow_name": flow.get("flow_name"),
        "previous_status": "paused" if new_status == "active" else "active",
        "current_status": new_status,
        "operation": operation
    }


def query_flow_execution_log(
    user_id: str,
    flow_id: str = "all",
    time_range: Optional[str] = None,
    status_filter: Optional[str] = None
) -> Dict[str, Any]:
    """
    Query flow execution logs.

    Args:
        user_id: The unique identifier of the user.
        flow_id: The ID of the flow, or 'all' to query all flows. Default is 'all'.
        time_range: Time range for filtering (e.g., 'last_7_days', 'last_30_days'). Optional.
        status_filter: Status filter - 'success', 'failed', or 'pending'. Optional.

    Returns:
        A dictionary containing execution log list with timestamps, trigger source, action results, duration, and error info.
    """
    data = _load_data()
    user = _get_user(data, user_id)
    
    # Get execution logs
    all_logs = []
    flows = user.get("flows", [])
    
    for flow in flows:
        if flow_id != "all" and flow.get("flow_id") != flow_id:
            continue
        
        flow_logs = flow.get("execution_logs", [])
        for log in flow_logs:
            log_entry = {
                "flow_id": flow.get("flow_id"),
                "flow_name": flow.get("flow_name"),
                **log
            }
            
            # Apply status filter
            if status_filter and log.get("status", "").lower() != status_filter.lower():
                continue
            
            all_logs.append(log_entry)
    
    # Sort by execution time descending
    all_logs.sort(key=lambda x: x.get("executed_at", ""), reverse=True)
    
    return {
        "logs": all_logs,
        "total_count": len(all_logs),
        "query_params": {
            "flow_id": flow_id,
            "time_range": time_range,
            "status_filter": status_filter
        }
    }


def update_automation_flow(
    user_id: str,
    flow_id: str,
    update_type: str,
    new_config: Optional[str] = None,
    update_reason: Optional[str] = None
) -> Dict[str, Any]:
    """
    Update automation flow configuration.

    Args:
        user_id: The unique identifier of the user.
        flow_id: The ID of the flow to update.
        update_type: Type of update - 'trigger', 'action', or 'flow_name'.
        new_config: New configuration as JSON string. Optional.
        update_reason: Reason for the update. Optional.

    Returns:
        A dictionary containing operation result and updated configuration snippet.
    """
    data = _load_data()
    flow = _get_flow(data, user_id, flow_id)
    
    # Validate update type
    valid_update_types = ["trigger", "action", "flow_name"]
    if update_type not in valid_update_types:
        raise InvalidRequestException(f"update_type must be one of {valid_update_types}.")
    
    # Check flow status - only allow updates for draft or paused flows
    if flow.get("status") == "active":
        raise InvalidRequestException("Cannot update an active flow. Please pause it first.")
    
    # Parse new config
    config = None
    if new_config:
        try:
            if isinstance(new_config, str):
                config = json.loads(new_config)
            else:
                config = new_config
        except json.JSONDecodeError:
            raise InvalidRequestException("new_config must be a valid JSON string.")
    
    # Save version history
    if "version_history" not in flow:
        flow["version_history"] = []
    
    old_config = {}
    if update_type == "trigger":
        old_config = flow.get("trigger", {}).copy()
    elif update_type == "action":
        old_config = {"actions": [a.copy() for a in flow.get("actions", [])]}
    elif update_type == "flow_name":
        old_config = {"flow_name": flow.get("flow_name")}
    
    flow["version_history"].append({
        "update_type": update_type,
        "old_config": old_config,
        "updated_at": datetime.utcnow().isoformat(),
        "reason": update_reason or ""
    })
    
    # Apply update
    updated_snippet = {}
    if update_type == "trigger" and config:
        flow["trigger"] = config
        updated_snippet = config
    elif update_type == "action" and config:
        if isinstance(config, list):
            flow["actions"] = config
        else:
            # Update specific action
            action_seq = config.get("seq")
            if action_seq:
                actions = flow.get("actions", [])
                for action in actions:
                    if action.get("seq") == action_seq:
                        action.update(config)
                        break
        updated_snippet = flow.get("actions", [])
    elif update_type == "flow_name" and config:
        flow["flow_name"] = config.get("flow_name", flow.get("flow_name"))
        updated_snippet = {"flow_name": flow.get("flow_name")}
    
    flow["updated_at"] = datetime.utcnow().isoformat()
    
    _save_data(data)
    
    return {
        "success": True,
        "flow_id": flow_id,
        "update_type": update_type,
        "updated_config": updated_snippet,
        "message": "Flow updated successfully. Consider running a test to verify the changes."
    }
