import os
import json
import shutil
import secrets
from datetime import datetime
from typing import Any, Dict, List

_WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..'))
_init_candidate = os.path.join(_WORKSPACE_DIR, 'environment', 'initial', 'dropbox_init.json')
if not os.path.exists(_init_candidate) and os.path.exists('/workspace/environment/initial/dropbox_init.json'):
    _WORKSPACE_DIR = '/workspace'
DATA_PATH = os.path.join(_WORKSPACE_DIR, 'environment', 'reports', 'dropbox.json')
INIT_PATH = os.path.join(_WORKSPACE_DIR, 'environment', 'initial', 'dropbox_init.json')

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


def _now() -> str:
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def _normalize_folder_path(path: str) -> str:
    base = '/MyDropbox/'
    if not path or path.strip() == '':
        return base
    path = path.strip()
    if not path.startswith('/'):
        path = '/' + path
    if not path.endswith('/'):
        path = path + '/'
    if path == '//':
        path = base
    # Ensure path starts with /MyDropbox/
    if not path.startswith('/MyDropbox/'):
        path = '/MyDropbox' + path
    return path


def _normalize_file_path(folder_path: str, name: str) -> str:
    folder = _normalize_folder_path(folder_path)
    return folder + name


def _normalize_item_path(path: str) -> str:
    base = '/MyDropbox/'
    if not path or path.strip() == '':
        return base
    path = path.strip()
    if not path.startswith('/'):
        path = '/' + path
    if path == '/':
        return base
    if not path.startswith('/MyDropbox/'):
        if path.startswith('/MyDropbox'):
            path = path + '/'
        else:
            path = '/MyDropbox' + path
    return path


def _find_item_by_path(data: Dict[str, Any], path: str) -> Dict[str, Any]:
    for item in data.get('items', []):
        if item.get('path') == path:
            return item
    return {}


def _find_item_by_path_flexible(data: Dict[str, Any], path: str) -> Dict[str, Any]:
    item = _find_item_by_path(data, path)
    if item:
        return item
    if path.endswith('/'):
        return _find_item_by_path(data, path[:-1])
    return _find_item_by_path(data, path + '/')


def _folder_exists(data: Dict[str, Any], folder_path: str) -> bool:
    folder_path = _normalize_folder_path(folder_path)
    for item in data.get('items', []):
        if item.get('path') == folder_path and item.get('type') == 'folder':
            return True
    return False


def _list_children(data: Dict[str, Any], folder_path: str) -> List[Dict[str, Any]]:
    folder_path = _normalize_folder_path(folder_path)
    return [i for i in data.get('items', []) if i.get('parent') == folder_path]


def UploadFile(local_file_path: str, cloud_folder_path: str = '/MyDropbox/') -> Dict[str, Any]:
    """Upload a local file to a specified folder in Dropbox cloud storage.

    Args:
        local_file_path (str): Path to the local file to be uploaded.
        cloud_folder_path (str): Destination folder path in Dropbox cloud storage.
    """
    if not local_file_path:
        raise InvalidRequestException("The 'local_file_path' is invalid.")
    cloud_folder_path = _normalize_folder_path(cloud_folder_path or '/MyDropbox/')
    data = _load_data()
    if not _folder_exists(data, cloud_folder_path):
        raise NotFoundException("The 'cloud_folder_path' does not exist.")
    name = os.path.basename(local_file_path)
    path = _normalize_file_path(cloud_folder_path, name)
    size = os.path.getsize(local_file_path) if os.path.exists(local_file_path) else 0
    new_item = {
        'id': secrets.token_hex(8),
        'name': name,
        'path': path,
        'type': 'file',
        'size': size,
        'created_at': _now(),
        'modified_at': _now(),
        'parent': cloud_folder_path
    }
    data['items'].append(new_item)
    _save_data(data)
    return {'success': True}


def DownloadFile(user_cloud_file_path: str = '', shared_file_id: str = '', local_destination_folder: str = '') -> Dict[str, Any]:
    """Download a file from Dropbox cloud storage to a local folder.

    Args:
        user_cloud_file_path (str): Path to the file in the user's Dropbox cloud storage.
        shared_file_id (str): ID of a shared file to download.
        local_destination_folder (str): Local folder path where the file will be saved.
    """
    if not user_cloud_file_path and not shared_file_id:
        raise InvalidRequestException("neither 'user_cloud_file_path' nor 'shared_file_id' is specified.")
    data = _load_data()
    local_folder = local_destination_folder or 'downloads'
    os.makedirs(local_folder, exist_ok=True)
    if user_cloud_file_path:
        item = _find_item_by_path(data, user_cloud_file_path)
        if not item or item.get('type') != 'file':
            raise NotFoundException("The 'user_cloud_file_path' does not exist.")
        local_path = os.path.join(local_folder, item.get('name'))
        # write a small placeholder file to simulate download
        with open(local_path, 'w', encoding='utf-8') as f:
            f.write(f"Downloaded copy of {item.get('name')} from Dropbox")
        return {'success': True, 'local_file_path': local_path}
    # shared file path
    current_user = data.get('current_user_email', '')
    shared_entry = None
    for s in data.get('shared_files', []):
        if s.get('shared_file_id') == shared_file_id and current_user in s.get('shared_with', []):
            shared_entry = s
            break
    if not shared_entry:
        raise NotFoundException("The 'shared_file_id' does not exist or is not shared with the user.")
    local_path = os.path.join(local_folder, shared_entry.get('name', 'shared_file'))
    with open(local_path, 'w', encoding='utf-8') as f:
        f.write(f"Downloaded shared file {shared_entry.get('name')}")
    return {'success': True, 'local_file_path': local_path}


def ListFilesAndFolders(cloud_folder_path: str = '/MyDropbox/', max_results: int = 10) -> Dict[str, Any]:
    """List files and folders in a specified Dropbox cloud folder.

    Args:
        cloud_folder_path (str): Path to the folder in Dropbox cloud storage.
        max_results (int): Maximum number of items to return in the list.
    """
    data = _load_data()
    cloud_folder_path = _normalize_folder_path(cloud_folder_path or '/MyDropbox/')
    try:
        max_results = int(max_results)
    except Exception:
        raise InvalidRequestException("The 'max_results' is not a positive integer.")
    if max_results <= 0:
        raise InvalidRequestException("The 'max_results' is not a positive integer.")
    if not _folder_exists(data, cloud_folder_path):
        raise NotFoundException("The 'cloud_folder_path' does not exist.")
    children = _list_children(data, cloud_folder_path)
    trimmed = children[:max_results]
    items = [{'id': c['id'], 'name': c['name'], 'type': c['type']} for c in trimmed]
    return {'items': items}


def CreateFolder(folder_name: str, parent_folder_path: str = '/MyDropbox/') -> Dict[str, Any]:
    """Create a new folder in the specified parent folder in Dropbox.

    Args:
        folder_name (str): Name of the new folder to create.
        parent_folder_path (str): Path to the parent folder where the new folder will be created.
    """
    if not folder_name:
        raise InvalidRequestException("The 'folder_name' is invalid.")
    data = _load_data()
    parent_folder_path = _normalize_folder_path(parent_folder_path or '/MyDropbox/')
    if not _folder_exists(data, parent_folder_path):
        raise NotFoundException("The 'parent_folder_path' does not exist.")
    new_folder_path = _normalize_folder_path(parent_folder_path + folder_name)
    if _find_item_by_path(data, new_folder_path):
        raise InvalidRequestException("The 'folder_name' is invalid or already exists.")
    new_folder = {
        'id': secrets.token_hex(8),
        'name': folder_name,
        'path': new_folder_path,
        'type': 'folder',
        'size': 0,
        'created_at': _now(),
        'modified_at': _now(),
        'parent': parent_folder_path
    }
    data['items'].append(new_folder)
    _save_data(data)
    return {'success': True}


def ShareItem(item_path: str, recipient_email: str, access_level: str) -> Dict[str, Any]:
    """Share a Dropbox item with a specified recipient at a given access level.

    Args:
        item_path (str): Path to the item to be shared in Dropbox.
        recipient_email (str): Email address of the recipient to share with.
        access_level (str): Access level granted to the recipient, must be view, comment, or edit.
    """
    if access_level not in ['view', 'comment', 'edit']:
        raise InvalidRequestException("The 'access_level' is not one of the valid values.")
    if not item_path or not recipient_email:
        raise InvalidRequestException("The 'recipient_email' is invalid or missing.")
    data = _load_data()
    item_path = _normalize_item_path(item_path)
    item = _find_item_by_path_flexible(data, item_path)
    if not item:
        raise NotFoundException("The 'item_path' does not exist.")
    share_entry = {
        'item_path': item_path,
        'recipient_email': recipient_email,
        'access_level': access_level,
        'shared_at': _now()
    }
    data.setdefault('shared_records', []).append(share_entry)
    _save_data(data)
    return {'success': True}


def DeleteDropboxItem(item_path: str) -> Dict[str, Any]:
    """Delete an item or folder from Dropbox cloud storage.

    Args:
        item_path (str): Path to the item or folder to be deleted.
    """
    if not item_path:
        raise InvalidRequestException("The 'item_path' parameter is invalid.")
    data = _load_data()
    item_path = _normalize_item_path(item_path)
    target = _find_item_by_path_flexible(data, item_path)
    if not target:
        raise NotFoundException("The 'item_path' does not exist.")
    # remove target and any children if folder
    if target.get('type') == 'folder':
        to_remove = [i for i in data.get('items', []) if i.get('path', '').startswith(item_path)]
    else:
        to_remove = [target]
    data['items'] = [i for i in data.get('items', []) if i not in to_remove]
    _save_data(data)
    return {'success': True}


def SearchDropboxItems(query: str, max_results: int = 10) -> Dict[str, Any]:
    """Search for items in Dropbox by name or path.

    Args:
        query (str): Search query string to match against item names and paths.
        max_results (int): Maximum number of search results to return.
    """
    if query is None:
        raise InvalidRequestException("The 'query' is malformed.")
    data = _load_data()
    try:
        max_results = int(max_results)
    except Exception:
        max_results = 10
    max_results = max(1, min(max_results, 50))
    results = []
    for item in data.get('items', []):
        if query.lower() in item.get('name', '').lower() or query.lower() in item.get('path', '').lower():
            results.append({'id': item['id'], 'path': item['path'], 'type': item['type']})
            if len(results) >= max_results:
                break
    return {'items': results}


def GetItemMetadata(item_path: str) -> Dict[str, Any]:
    """Retrieve metadata for a specific item in Dropbox.

    Args:
        item_path (str): Path to the item whose metadata is to be retrieved.
    """
    if not item_path:
        raise InvalidRequestException("The 'item_path' parameter is invalid.")
    data = _load_data()
    item_path = _normalize_item_path(item_path)
    item = _find_item_by_path_flexible(data, item_path)
    if not item:
        raise NotFoundException("The 'item_path' does not exist.")
    return item