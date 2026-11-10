import os
import json
import shutil
from datetime import datetime
from typing import List, Dict, Any, Optional

INIT = False
DATA_PATH = 'environment/reports/slack.json'
INIT_PATH = 'environment/initial/slack_init.json'

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
    """Load data from the working environment file."""
    _ensure_work_env()
    with open(DATA_PATH, 'r') as f:
        return json.load(f)

def _save_data(data: Dict[str, Any]):
    """Save data to the working environment file."""
    with open(DATA_PATH, 'w') as f:
        json.dump(data, f, indent=4)

def send_message(recipient: str, message: str, file_path: str = None) -> Dict[str, Any]:
    """
    Send a message and optional file to a channel or user.

    Args:
        recipient (str): The name of the recipient, channel name starts with '#', e.g., '#general', or user name starts with '@', e.g., '@john'.
        message (str): The content of the message.
        file_path (str, optional): The local file path of the file to upload.

    Returns:
        Dict[str, Any]: A dictionary containing 'success' (bool) indicating whether the message was sent successfully.
    """
    data = _load_data()
    if not recipient.startswith(('#', '@')) or not message.strip():
        return {"success": False, "error": "InvalidRequestException"}
    if file_path and not os.path.exists(file_path):
        return {"success": False, "error": "NotFoundException"}
    
    # Simulate sending message
    timestamp = datetime.now().isoformat()
    file_id = None
    if file_path:
        file_id = f"file_{len(data.get('files', {})) + 1}"
        data.setdefault('files', {})[file_id] = file_path
    
    msg = {
        "content": message,
        "timestamp": timestamp,
        "in": recipient,
        "from": "@current_user",  # Assume current user
        "file_id": file_id
    }
    data.setdefault('messages', []).append(msg)
    _save_data(data)
    return {"success": True}

def create_channel(channel_name: str, is_public: bool = True) -> Dict[str, Any]:
    """
    Create a new channel.

    Args:
        channel_name (str): The name of the channel, must start with '#'.
        is_public (bool, optional): Whether the channel is public. Default is True.

    Returns:
        Dict[str, Any]: A dictionary containing 'success' (bool) indicating whether the channel was created successfully.
    """
    data = _load_data()
    if not channel_name.startswith('#') or not channel_name[1:].strip():
        return {"success": False, "error": "InvalidRequestException"}
    channels = data.get('channels', [])
    if any(c['name'] == channel_name for c in channels):
        return {"success": False, "error": "ConflictException"}
    channel = {
        "name": channel_name,
        "is_public": is_public,
        "members": ["@current_user"],
        "owner": "@current_user"
    }
    channels.append(channel)
    data['channels'] = channels
    _save_data(data)
    return {"success": True}

def join_channel(channel_name: str) -> Dict[str, Any]:
    """
    Join an existing channel.

    Args:
        channel_name (str): The name of the channel, must start with '#'.

    Returns:
        Dict[str, Any]: A dictionary containing 'success' (bool) indicating whether the user joined the channel successfully.
    """
    data = _load_data()
    if not channel_name.startswith('#') or not channel_name[1:].strip():
        return {"success": False, "error": "InvalidRequestException"}
    channels = data.get('channels', [])
    channel = next((c for c in channels if c['name'] == channel_name), None)
    if not channel:
        return {"success": False, "error": "NotFoundException"}
    if "@current_user" in channel['members']:
        return {"success": True}
    channel['members'].append("@current_user")
    _save_data(data)
    return {"success": True}

def leave_channel(channel_name: str) -> Dict[str, Any]:
    """
    Leave a channel.

    Args:
        channel_name (str): The name of the channel, must start with '#'.

    Returns:
        Dict[str, Any]: A dictionary containing 'success' (bool) indicating whether the user left the channel successfully.
    """
    data = _load_data()
    if not channel_name.startswith('#') or not channel_name[1:].strip():
        return {"success": False, "error": "InvalidRequestException"}
    channels = data.get('channels', [])
    channel = next((c for c in channels if c['name'] == channel_name), None)
    if not channel:
        return {"success": False, "error": "NotFoundException"}
    if "@current_user" not in channel['members']:
        return {"success": False, "error": "InvalidRequestException"}
    channel['members'].remove("@current_user")
    _save_data(data)
    return {"success": True}

def search_message(query: str, to: Optional[str] = None, source: Optional[str] = None, max_results: Optional[int] = 10) -> Dict[str, Any]:
    """
    Search for messages in a channel or direct messages.

    Args:
        query: The search query.
        to: The receive of messages.
        source: The sender of messages.
        max_results: The number of maximum results.
    """
    data = _load_data()
    in_channel = to
    from_user = source
    max_results = max_results if max_results is not None else 10
    messages = data.get('messages', [])
    results = []
    for msg in messages:
        if query.lower() in msg['content'].lower():
            if in_channel and msg['in'] != in_channel:
                continue
            if from_user and msg['from'] != from_user:
                continue
            results.append(msg)
            if len(results) >= max_results:
                break
    return {"messages": results}

def search_channel_or_user(query: str, search_type: str, max_results: int = 10) -> Dict[str, Any]:
    """
    Search for channels or users by query.

    Args:
        query (str): The search query.
        search_type (str): One of ['channels', 'users'], the type of resources to search.
        max_results (int, optional): The maximum number of results to return. Default is 10.

    Returns:
        Dict[str, Any]: A dictionary containing 'results' (list) of search results.
    """
    data = _load_data()
    results = []
    limit = max_results if max_results is not None else 10
    if search_type == 'channels':
        channels = data.get('channels', [])
        for c in channels:
            if query.lower() in c['name'].lower():
                status = 'owner' if c['owner'] == '@current_user' else ('member' if '@current_user' in c['members'] else 'non-member')
                results.append({"name": c['name'], "status": status})
                if len(results) >= limit:
                    break
    elif search_type == 'users':
        users = data.get('users', [])
        for u in users:
            if query.lower() in u['username'].lower():
                status = u.get('status', {}).get('presence', 'offline')
                results.append({"name": u['username'], "status": status})
                if len(results) >= limit:
                    break
    else:
        return {"results": [], "error": "InvalidRequestException"}
    return {"results": results}

def update_profile_and_status(status_text: str = None, status_emoji: str = None, presence: str = None, profile: str = None) -> Dict[str, Any]:
    """
    Update the user's profile and status.

    Args:
        status_text (str, optional): The status text.
        status_emoji (str, optional): The status emoji.
        presence (str, optional): One of ['auto', 'away'], the presence status.
        profile (Dict[str, str], optional): The profile to update.

    Returns:
        Dict[str, Any]: A dictionary containing 'success' (bool) indicating whether the profile and status were updated successfully.
    """
    data = _load_data()
    users = data.get('users', [])
    user = next((u for u in users if u['username'] == '@current_user'), None)
    if not user:
        user = {"username": "@current_user", "profile": {}, "status": {}}
        users.append(user)
    if status_text is not None:
        user['status']['status_text'] = status_text
    if status_emoji is not None:
        user['status']['status_emoji'] = status_emoji
    if presence and presence in ['auto', 'away']:
        user['status']['presence'] = presence
    if profile:
        if isinstance(profile, str):
            try:
                profile = json.loads(profile)
            except (json.JSONDecodeError, TypeError):
                profile = {}
        if isinstance(profile, dict):
            user['profile'].update(profile)
    data['users'] = users
    _save_data(data)
    return {"success": True}

def manage_membership(channel_name: str, user_name: str, action: str) -> Dict[str, Any]:
    """
    Add or remove users from a channel. This tool is only valid when the user is the owner of the group.

    Args:
        channel_name (str): The name of the channel, must start with '#'.
        user_name (str): The name of the user to add or remove, must start with '@'.
        action (str): One of ['add', 'remove'], the action to perform.

    Returns:
        Dict[str, Any]: A dictionary containing 'success' (bool) indicating whether the membership was managed successfully.
    """
    data = _load_data()
    if not channel_name.startswith('#') or not user_name.startswith('@') or action not in ['add', 'remove']:
        return {"success": False, "error": "InvalidRequestException"}
    channels = data.get('channels', [])
    channel = next((c for c in channels if c['name'] == channel_name), None)
    if not channel or channel['owner'] != '@current_user':
        return {"success": False, "error": "InvalidRequestException"}
    if action == 'add' and user_name not in channel['members']:
        channel['members'].append(user_name)
    elif action == 'remove' and user_name in channel['members']:
        channel['members'].remove(user_name)
    _save_data(data)
    return {"success": True}

def get_user_details(user_name: str) -> Dict[str, Any]:
    """
    Retrieve the profile and status of a user.

    Args:
        user_name (str): The name of the user, must start with '@'.

    Returns:
        Dict[str, Any]: A dictionary containing 'profile' and 'status' of the user.
    """
    data = _load_data()
    if not user_name.startswith('@'):
        return {"profile": None, "status": None, "error": "InvalidRequestException"}
    users = data.get('users', [])
    user = next((u for u in users if u['username'] == user_name), None)
    if not user:
        return {"profile": {}, "status": {}}
    return {"profile": user.get('profile', {}), "status": user.get('status', {})}

def download_slack_file(file_id: str, save_path: str) -> Dict[str, Any]:
    """
    Download a Slack file using its unique identifier.

    Args:
        file_id (str): The unique identifier of the file.
        save_path (str): The local path to save the file.

    Returns:
        Dict[str, Any]: A dictionary containing 'success' (bool) indicating whether the file was downloaded successfully.
    """
    data = _load_data()
    files = data.get('files', {})
    if file_id not in files:
        return {"success": False, "error": "InvalidRequestException"}
    # Simulate download by copying file
    try:
        shutil.copyfile(files[file_id], save_path)
        return {"success": True}
    except:
        return {"success": False, "error": "InvalidRequestException"}

class InvalidRequestException(Exception):
    pass

class NotFoundException(Exception):
    pass

class ConflictException(Exception):
    pass