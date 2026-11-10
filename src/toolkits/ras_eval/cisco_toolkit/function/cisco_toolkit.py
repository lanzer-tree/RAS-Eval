import os
import json
import shutil
from datetime import datetime
from typing import Optional, Dict, Any, List

_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_WORKSPACE_ROOT = os.path.abspath(os.path.join(_MODULE_DIR, '..', '..', '..', '..', '..'))
_init_candidate = os.path.join(_WORKSPACE_ROOT, 'environment', 'initial', 'cisco_init.json')
if not os.path.exists(_init_candidate):
    _WORKSPACE_ROOT = '/workspace'

# Global variables
INIT = False
DATA_PATH = os.path.join(_WORKSPACE_ROOT, 'environment', 'reports', 'cisco.json')
INIT_PATH = os.path.join(_WORKSPACE_ROOT, 'environment', 'initial', 'cisco_init.json')


class InvalidRequestException(Exception):
    """Exception raised for invalid requests."""
    pass


class NotFoundException(Exception):
    """Exception raised when resource is not found."""
    pass


class ConflictException(Exception):
    """Exception raised when conflict occurs."""
    pass


def _ensure_work_env():
    """
    Ensure working environment file exists by copying from init if necessary.
    
    Raises:
        InvalidRequestException: If init file not found.
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


def _load_data():
    """
    Load data from the working environment file.
    
    Returns:
        dict: The data loaded from the working environment file.
    """
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_data(data: dict):
    """
    Save data to the working environment file.
    
    Args:
        data (dict): The data to save.
    """
    _ensure_work_env()
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def _is_valid_domain(domain: str) -> bool:
    """
    Validate if a string is a valid domain.
    
    Args:
        domain (str): The domain to validate.
    
    Returns:
        bool: True if valid, False otherwise.
    """
    if not isinstance(domain, str) or not domain:
        return False
    if '.' not in domain:
        return False
    parts = domain.split('.')
    if len(parts) < 2:
        return False
    for part in parts:
        if not part or not all(c.isalnum() or c == '-' for c in part):
            return False
    return True


def block_domain(domain: str) -> Dict[str, Any]:
    """
    Block access to a specific domain.

    Args:
        domain: The domain to be blocked.

    Raises:
        InvalidRequestException: If domain is not valid.
    """
    if not _is_valid_domain(domain):
        raise InvalidRequestException(f"The 'domain' argument '{domain}' is not a valid domain.")
    
    data = _load_data()
    blocked_domains = data.get('blocked_domains', [])
    
    if domain not in blocked_domains:
        blocked_domains.append(domain)
        data['blocked_domains'] = blocked_domains
        _save_data(data)
    
    return {"success": True}


def unblock_domain(domain: str) -> Dict[str, Any]:
    """
    Unblock access to a specific domain.

    Args:
        domain: The domain to be unblocked.

    Raises:
        InvalidRequestException: If domain is not valid.
    """
    if not _is_valid_domain(domain):
        raise InvalidRequestException(f"The 'domain' argument '{domain}' is not a valid domain.")
    
    data = _load_data()
    blocked_domains = data.get('blocked_domains', [])
    
    if domain in blocked_domains:
        blocked_domains.remove(domain)
        data['blocked_domains'] = blocked_domains
        _save_data(data)
    
    return {"success": True}


def verify_domain(domain: str) -> Dict[str, Any]:
    """
    Verify a domain by checking if it is safe.

    Args:
        domain: The domain to be verified.

    Raises:
        InvalidRequestException: If domain is not valid.
    """
    if not _is_valid_domain(domain):
        raise InvalidRequestException(f"The 'domain' argument '{domain}' is not a valid domain.")
    
    data = _load_data()
    threat_database = data.get('threat_database', {})
    
    # Check if domain is in threat database
    is_safe = domain not in threat_database
    
    return {"is_safe": is_safe}


def search_threats(keyword: str, max_results: int = 10) -> Dict[str, Any]:
    """
    Search for potential threats based on a keyword or domain.

    Args:
        keyword: The keyword or domain to search for threats.
        max_results: Maximum number of results to return. Default is 10.

    Raises:
        InvalidRequestException: If keyword or max_results is invalid.
    """
    if not isinstance(keyword, str) or not keyword.strip():
        raise InvalidRequestException("The 'keyword' argument is not a valid keyword.")
    if not isinstance(max_results, int) or max_results <= 0:
        raise InvalidRequestException("The 'max_results' argument is not a valid integer.")
    
    data = _load_data()
    threat_database = data.get('threat_database', {})
    
    results = []
    for domain, threat_info in threat_database.items():
        if keyword.lower() in domain.lower() or keyword.lower() in threat_info.get('description', '').lower():
            results.append({
                'threat_id': threat_info['threat_id'],
                'domain': domain,
                'description': threat_info['description'],
                'severity': threat_info['severity']
            })
            if len(results) >= max_results:
                break
    
    return {"threats": results}


def get_threat_details(threat_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific threat.

    Args:
        threat_id: The unique identifier of the threat.

    Raises:
        InvalidRequestException: If threat_id is not valid.
    """
    if not isinstance(threat_id, str) or not threat_id.strip():
        raise InvalidRequestException(f"The 'threat_id' argument '{threat_id}' is not a valid threat identifier.")
    
    data = _load_data()
    threat_database = data.get('threat_database', {})
    
    for domain, threat_info in threat_database.items():
        if threat_info['threat_id'] == threat_id:
            return {
                "threat_details": {
                    'threat_id': threat_info['threat_id'],
                    'domain': domain,
                    'description': threat_info['description'],
                    'severity': threat_info['severity'],
                    'first_seen': threat_info['first_seen'],
                    'last_seen': threat_info['last_seen']
                }
            }
    
    raise InvalidRequestException(f"The 'threat_id' argument '{threat_id}' is not a valid threat identifier.")


def search_policy(keyword: str, type: Optional[str] = None, max_results: int = 10) -> Dict[str, Any]:
    """
    Search for security policies based on a keyword.

    Args:
        keyword: The keyword to search for policies.
        type: Policy type ('whitelist' or 'blacklist'). Default is None (search all).
        max_results: Maximum number of results to return. Default is 10.

    Raises:
        InvalidRequestException: If parameters are invalid.
    """
    if not isinstance(keyword, str) or not keyword.strip():
        raise InvalidRequestException("The 'keyword' argument is not a valid string.")
    if type and type.lower() not in ['whitelist', 'blacklist']:
        raise InvalidRequestException(f"The 'type' argument is not one of ['whitelist', 'blacklist'].")
    if not isinstance(max_results, int) or max_results <= 0:
        raise InvalidRequestException("The 'max_results' argument is not a positive integer.")
    
    data = _load_data()
    policies = data.get('policies', [])
    
    results = []
    for policy in policies:
        keyword_lower = keyword.lower().strip()
        matches = not keyword_lower or (
            keyword_lower in policy.get('policy_id', '').lower()
            or keyword_lower in policy.get('policy_name', '').lower()
            or keyword_lower in policy.get('policy_description', '').lower()
        )
        if matches:
            if type is None or policy['policy_type'].lower() == type.lower():
                results.append({
                    'policy_id': policy['policy_id'],
                    'policy_name': policy['policy_name'],
                    'policy_description': policy['policy_description'],
                    'policy_type': policy['policy_type']
                })
                if len(results) >= max_results:
                    break
    
    return {"policies": results}


def create_policy(policy_name: str, policy_description: str, policy_type: str, domains: List[str]) -> Dict[str, Any]:
    """
    Create a new security policy.

    Args:
        policy_name: The name of the policy.
        policy_description: A brief description of the policy.
        policy_type: The type of policy ('whitelist' or 'blacklist').
        domains: List of domains to add to the policy.

    Raises:
        InvalidRequestException: If parameters are invalid.
        ConflictException: If policy with same name already exists.
    """
    if not isinstance(policy_name, str) or not policy_name.strip():
        raise InvalidRequestException("The 'policy_name' argument is empty.")
    if not isinstance(policy_description, str) or not policy_description.strip():
        raise InvalidRequestException("The 'policy_description' argument is empty.")
    if policy_type not in ['whitelist', 'blacklist']:
        raise InvalidRequestException("The 'policy_type' argument is not one of ['whitelist', 'blacklist'].")
    if isinstance(domains, str):
        try:
            domains = json.loads(domains)
        except json.JSONDecodeError:
            raise InvalidRequestException("The 'domains' argument is not a valid JSON list.")
    if not isinstance(domains, list) or not domains:
        raise InvalidRequestException("The 'domains' argument is empty or not a list.")
    
    data = _load_data()
    policies = data.get('policies', [])
    
    # Check if policy with same name exists
    for policy in policies:
        if policy['policy_name'].lower() == policy_name.lower():
            raise ConflictException("A policy with the same name already exists.")
    
    # Generate policy_id
    policy_id = f"policy_{len(policies) + 1:04d}"
    
    new_policy = {
        'policy_id': policy_id,
        'policy_name': policy_name,
        'policy_description': policy_description,
        'policy_type': policy_type,
        'domains': domains,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    policies.append(new_policy)
    data['policies'] = policies
    _save_data(data)
    
    return {"policy_id": policy_id}


def update_policy(policy_id: str, policy_name: Optional[str] = None, policy_description: Optional[str] = None,
                  policy_type: Optional[str] = None, domains: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Update an existing security policy.

    Args:
        policy_id: The unique identifier of the policy to be updated.
        policy_name: The new name of the policy.
        policy_description: The new description of the policy.
        policy_type: The new type of policy ('whitelist' or 'blacklist').
        domains: List of domains to update in the policy.

    Raises:
        InvalidRequestException: If parameters are invalid.
        NotFoundException: If policy does not exist.
    """
    if not isinstance(policy_id, str) or not policy_id.strip():
        raise InvalidRequestException(f"The 'policy_id' argument is not a valid policy identifier.")
    if policy_name is not None and (not isinstance(policy_name, str) or policy_name == ""):
        raise InvalidRequestException("The 'policy_name' argument is empty.")
    if policy_description is not None and (not isinstance(policy_description, str) or policy_description == ""):
        raise InvalidRequestException("The 'policy_description' argument is empty.")
    if policy_type is not None and policy_type not in ['whitelist', 'blacklist']:
        raise InvalidRequestException("The 'policy_type' argument is not one of ['whitelist', 'blacklist'].")
    if domains is not None and (not isinstance(domains, list) or not domains):
        raise InvalidRequestException("The 'domains' argument is empty.")
    
    data = _load_data()
    policies = data.get('policies', [])
    
    found = False
    for policy in policies:
        if policy['policy_id'] == policy_id:
            found = True
            if policy_name is not None:
                policy['policy_name'] = policy_name
            if policy_description is not None:
                policy['policy_description'] = policy_description
            if policy_type is not None:
                policy['policy_type'] = policy_type
            if domains is not None:
                policy['domains'] = domains
            policy['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            break
    
    if not found:
        raise NotFoundException(f"The 'policy_id' does not exist.")
    
    data['policies'] = policies
    _save_data(data)
    
    return {"success": True}


def delete_policy(policy_id: str) -> Dict[str, Any]:
    """
    Delete an existing security policy.

    Args:
        policy_id: The unique identifier of the policy to be deleted.

    Raises:
        InvalidRequestException: If policy_id is not valid.
        NotFoundException: If policy does not exist.
    """
    if not isinstance(policy_id, str) or not policy_id.strip():
        raise InvalidRequestException(f"The 'policy_id' argument is not a valid policy identifier.")
    
    data = _load_data()
    policies = data.get('policies', [])
    
    initial_length = len(policies)
    policies = [p for p in policies if p['policy_id'] != policy_id]
    
    if len(policies) == initial_length:
        raise NotFoundException(f"The 'policy_id' does not exist.")
    
    data['policies'] = policies
    _save_data(data)
    
    return {"success": True}


def get_policy_details(policy_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific security policy.

    Args:
        policy_id: The unique identifier of the policy.

    Raises:
        InvalidRequestException: If policy_id is not valid.
        NotFoundException: If policy does not exist.
    """
    if not isinstance(policy_id, str) or not policy_id.strip():
        raise InvalidRequestException(f"The 'policy_id' argument is not a valid policy identifier.")
    
    data = _load_data()
    policies = data.get('policies', [])
    
    for policy in policies:
        if policy['policy_id'] == policy_id:
            return {
                "policy_details": {
                    'policy_id': policy['policy_id'],
                    'policy_name': policy['policy_name'],
                    'policy_description': policy['policy_description'],
                    'policy_type': policy['policy_type'],
                    'domains': policy['domains']
                }
            }
    
    raise NotFoundException(f"The policy does not exist.")


def search_logs(keyword: Optional[str] = None, start_date: Optional[str] = None, end_date: Optional[str] = None,
                event_type: Optional[str] = None, max_results: int = 10) -> Dict[str, Any]:
    """
    Search for security logs based on keyword, date range, or event type.

    Args:
        keyword: The keyword to search for logs.
        start_date: Start date in 'YYYY-MM-DD' format.
        end_date: End date in 'YYYY-MM-DD' format.
        event_type: Event type ('allowed' or 'blocked').
        max_results: Maximum number of results to return. Default is 10.

    Raises:
        InvalidRequestException: If parameters are invalid.
    """
    if start_date and not _is_valid_date(start_date):
        raise InvalidRequestException("The 'start_date' argument is not a valid date.")
    if end_date and not _is_valid_date(end_date):
        raise InvalidRequestException("The 'end_date' argument is not a valid date.")
    if event_type and event_type not in ['allowed', 'blocked']:
        raise InvalidRequestException("The 'event_type' argument is not one of ['allowed', 'blocked'].")
    if not isinstance(max_results, int) or max_results <= 0:
        raise InvalidRequestException("The 'max_results' argument is not a valid integer.")
    
    data = _load_data()
    logs = data.get('logs', [])
    
    results = []
    for log in logs:
        # Check keyword match
        if keyword and keyword.lower() not in log.get('domain', '').lower():
            continue
        
        # Check date range
        if start_date and log.get('timestamp', '')[:10] < start_date:
            continue
        if end_date and log.get('timestamp', '')[:10] > end_date:
            continue
        
        # Check event type
        if event_type and log.get('event_type') != event_type:
            continue
        
        results.append({
            'log_id': log['log_id'],
            'timestamp': log['timestamp'],
            'event_type': log['event_type'],
            'domain': log['domain'],
            'user': log['user']
        })
        
        if len(results) >= max_results:
            break
    
    return {"logs": results}


def get_log_details(log_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific security log.

    Args:
        log_id: The unique identifier of the log.

    Raises:
        InvalidRequestException: If log_id is not valid.
        NotFoundException: If log does not exist.
    """
    if not isinstance(log_id, str) or not log_id.strip():
        raise InvalidRequestException(f"The 'log_id' argument is not a valid log identifier.")
    
    data = _load_data()
    logs = data.get('logs', [])
    
    for log in logs:
        if log['log_id'] == log_id:
            return {
                "log_details": {
                    'log_id': log['log_id'],
                    'timestamp': log['timestamp'],
                    'event_type': log['event_type'],
                    'domain': log['domain'],
                    'user': log['user'],
                    'device': log.get('device', 'unknown'),
                    'location': log.get('location', 'unknown')
                }
            }
    
    raise NotFoundException(f"The log does not exist.")


def generate_report(start_date: str, end_date: str, report_type: str, download: bool = False) -> Dict[str, Any]:
    """
    Generate a security report based on date range and report type.

    Args:
        start_date: Start date in 'YYYY-MM-DD' format.
        end_date: End date in 'YYYY-MM-DD' format.
        report_type: Report type ('summary' or 'detailed').
        download: Whether to download the report. Default is False.

    Raises:
        InvalidRequestException: If parameters are invalid.
    """
    if not _is_valid_date(start_date):
        raise InvalidRequestException("The 'start_date' argument is not a valid date.")
    if not _is_valid_date(end_date):
        raise InvalidRequestException("The 'end_date' argument is not a valid date.")
    if report_type not in ['summary', 'detailed']:
        raise InvalidRequestException("The 'report_type' argument is not one of ['summary', 'detailed'].")
    if not isinstance(download, bool):
        raise InvalidRequestException("The 'download' argument is not a valid boolean.")
    
    data = _load_data()
    logs = data.get('logs', [])
    
    # Filter logs by date range
    filtered_logs = [log for log in logs if start_date <= log['timestamp'][:10] <= end_date]
    
    # Generate report content
    if report_type == 'summary':
        content = _generate_summary_report(filtered_logs)
    else:
        content = _generate_detailed_report(filtered_logs)
    
    if download:
        report_path = os.path.join(_WORKSPACE_ROOT, 'environment', 'reports', f"cisco_report_{start_date}_to_{end_date}.txt")
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return {
            "success": True,
            "report_path": report_path,
            "report_content": ""
        }
    else:
        return {
            "success": True,
            "report_path": "",
            "report_content": content
        }


def _is_valid_date(date_str: str) -> bool:
    """
    Validate if a string is a valid date in YYYY-MM-DD format.
    
    Args:
        date_str (str): The date string to validate.
    
    Returns:
        bool: True if valid, False otherwise.
    """
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except (ValueError, TypeError):
        return False


def _generate_summary_report(logs: list) -> str:
    """
    Generate a summary report.
    
    Args:
        logs (list): List of logs to summarize.
    
    Returns:
        str: The summary report content.
    """
    total = len(logs)
    allowed = len([l for l in logs if l['event_type'] == 'allowed'])
    blocked = len([l for l in logs if l['event_type'] == 'blocked'])
    
    content = "=== Cisco Umbrella Security Report (Summary) ===\n\n"
    content += f"Total Events: {total}\n"
    content += f"Allowed: {allowed}\n"
    content += f"Blocked: {blocked}\n"
    content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    
    return content


def _generate_detailed_report(logs: list) -> str:
    """
    Generate a detailed report.
    
    Args:
        logs (list): List of logs to include in the report.
    
    Returns:
        str: The detailed report content.
    """
    content = "=== Cisco Umbrella Security Report (Detailed) ===\n\n"
    
    for log in logs:
        content += f"Log ID: {log['log_id']}\n"
        content += f"Timestamp: {log['timestamp']}\n"
        content += f"Event Type: {log['event_type']}\n"
        content += f"Domain: {log['domain']}\n"
        content += f"User: {log['user']}\n"
        content += f"Device: {log.get('device', 'unknown')}\n"
        content += f"Location: {log.get('location', 'unknown')}\n"
        content += "-" * 50 + "\n"
    
    return content
