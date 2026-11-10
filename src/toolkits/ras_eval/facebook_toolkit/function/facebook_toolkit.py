import os
import json
import shutil
import secrets
from datetime import datetime
from typing import Any, Dict, List

DATA_PATH = 'environment/reports/facebook.json'
INIT_PATH = 'environment/initial/facebook_init.json'

INIT = False
VALID_PRIVACY = {'public', 'friends', 'only me'}


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


def _new_id(prefix: str) -> str:
    return f"{prefix}_{secrets.token_hex(4)}"


def GetFacebookUserProfile() -> Dict[str, Any]:
    """Get the current user's profile information."""
    data = _load_data()
    return {'profile': data.get('user', {})}


def UpdateUserProfile(updates: Dict[str, Any]) -> Dict[str, Any]:
    """Update the current user's profile information.
    
    Args:
        updates (Dict[str, Any]): Dictionary of profile fields to update (name, email, birthday, location, bio).
    """
    if isinstance(updates, str):
        try:
            updates = json.loads(updates)
        except json.JSONDecodeError:
            raise InvalidRequestException("The 'updates' parameter contains invalid fields or values.")
    if not isinstance(updates, dict) or not updates:
        raise InvalidRequestException("The 'updates' parameter contains invalid fields or values.")
    data = _load_data()
    allowed = {'name', 'email', 'birthday', 'location', 'bio'}
    for k in updates.keys():
        if k not in allowed:
            raise InvalidRequestException("The 'updates' parameter contains invalid fields or values.")
    data.setdefault('user', {}).update(updates)
    _save_data(data)
    return {'success': True}


def SearchFriends(keyword: str, max_results: int = 10) -> Dict[str, Any]:
    """Search for friends based on a keyword.
    
    Args:
        keyword (str): Search keyword to match friend names, emails, or locations.
        max_results (int): Maximum number of results to return.
    """
    if not isinstance(keyword, str) or not keyword.strip():
        raise InvalidRequestException("The 'keyword' parameter is empty.")
    try:
        max_res = int(max_results) if max_results is not None else 10
    except (ValueError, TypeError):
        raise InvalidRequestException("The 'max_results' parameter is not valid.")
    if max_res <= 0:
        raise InvalidRequestException("The 'max_results' parameter is not valid.")
    data = _load_data()
    results = []
    for f in data.get('friends', []):
        text = f"{f.get('name','')} {f.get('email','')} {f.get('location','')} {f.get('profile','')}".lower()
        if keyword.lower() in text:
            results.append(f)
        if len(results) >= max_res:
            break
    return {'friends_info': results}


def CreatePost(content: str, media_path: str = '', privacy_setting: str = 'friends') -> Dict[str, Any]:
    """Create a new post with optional media and privacy settings.
    
    Args:
        content (str): The text content of the post.
        media_path (str): Path to media file to attach, optional.
        privacy_setting (str): Privacy setting (public, friends, only me).
    """
    if not isinstance(content, str) or not content.strip():
        raise InvalidRequestException("The 'content' parameter is empty.")
    if privacy_setting and privacy_setting not in VALID_PRIVACY:
        raise InvalidRequestException("The 'privacy_setting' parameter is not valid.")
    data = _load_data()
    if media_path:
        media_files = set(data.get('media_files', []))
        if media_files and media_path not in media_files:
            raise NotFoundException("Media file not found.")
    post_id = _new_id('post')
    post = {
        'post_id': post_id,
        'user_id': data.get('user', {}).get('user_id', 'u_me'),
        'content': content.strip(),
        'media_path': media_path,
        'privacy_setting': privacy_setting or 'friends',
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    data.setdefault('posts', []).append(post)
    _save_data(data)
    return {'post_id': post_id}


def SearchPosts(user_id: str, keyword: str, max_results: int = 10) -> Dict[str, Any]:
    """Search for posts by a specific user.
    
    Args:
        user_id (str): The ID of the user whose posts to search.
        keyword (str): Search keyword to match post content.
        max_results (int): Maximum number of results to return.
    """
    if not user_id:
        raise InvalidRequestException("The 'user_id' parameter is not valid.")
    if not isinstance(keyword, str) or not keyword.strip():
        raise InvalidRequestException("The 'keyword' parameter is empty.")
    try:
        max_res = int(max_results) if max_results is not None else 10
    except (ValueError, TypeError):
        raise InvalidRequestException("The 'max_results' parameter is not valid.")
    if max_res <= 0:
        raise InvalidRequestException("The 'max_results' parameter is not valid.")
    data = _load_data()
    user_exists = any(u.get('user_id') == user_id for u in data.get('users', []) + data.get('friends', []) + [data.get('user', {})])
    if not user_exists:
        raise NotFoundException("The 'user_id' parameter is not found.")
    results = []
    for p in data.get('posts', []):
        if p.get('user_id') != user_id:
            continue
        if keyword.lower() in p.get('content', '').lower():
            results.append({'post_id': p.get('post_id'), 'content': p.get('content')})
        if len(results) >= max_res:
            break
    return {'posts': results}


def SearchMyPosts(keyword: str, max_results: int = 10) -> Dict[str, Any]:
    """Search for the current user's own posts.
    
    Args:
        keyword (str): Search keyword to match post content. If empty, returns all posts.
        max_results (int): Maximum number of results to return.
    """
    if not isinstance(keyword, str):
        raise InvalidRequestException("The 'keyword' parameter is empty.")
    try:
        max_res = int(max_results) if max_results is not None else 10
    except (ValueError, TypeError):
        raise InvalidRequestException("The 'max_results' parameter is not valid.")
    if max_res <= 0:
        raise InvalidRequestException("The 'max_results' parameter is not valid.")
    data = _load_data()
    user_id = data.get('user', {}).get('user_id')
    results = []
    for p in data.get('posts', []):
        if p.get('user_id') != user_id:
            continue
        if not keyword.strip() or keyword.lower() in p.get('content', '').lower():
            results.append({'post_id': p.get('post_id'), 'content': p.get('content')})
        if len(results) >= max_res:
            break
    return {'posts': results}


def GetPost(post_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific post.
    
    Args:
        post_id (str): The ID of the post to retrieve.
    """
    if not post_id:
        raise InvalidRequestException("The 'post_id' parameter is not valid.")
    data = _load_data()
    post = next((p for p in data.get('posts', []) if p.get('post_id') == post_id), None)
    if not post:
        raise NotFoundException("The 'post_id' parameter is not found.")
    return {'post': post}


def UpdatePost(post_id: str, new_content: str = '', new_privacy_setting: str = '') -> Dict[str, Any]:
    """Update an existing post's content or privacy settings.
    
    Args:
        post_id (str): The ID of the post to update.
        new_content (str): New content for the post, optional.
        new_privacy_setting (str): New privacy setting (public, friends, only me), optional.
    """
    if not post_id:
        raise InvalidRequestException("The 'post_id' parameter is not valid.")
    data = _load_data()
    post = next((p for p in data.get('posts', []) if p.get('post_id') == post_id), None)
    if not post:
        raise NotFoundException("The 'post_id' parameter is not found.")
    if new_content is not None:
        if isinstance(new_content, str) and new_content.strip():
            post['content'] = new_content.strip()
        elif new_content:
            raise InvalidRequestException("The 'new_content' parameter is empty.")
    if new_privacy_setting:
        if new_privacy_setting not in VALID_PRIVACY:
            raise InvalidRequestException("The 'new_privacy_setting' parameter is not valid.")
        post['privacy_setting'] = new_privacy_setting
    _save_data(data)
    return {'success': True}


def DeletePost(post_id: str) -> Dict[str, Any]:
    """Delete a specific post.
    
    Args:
        post_id (str): The ID of the post to delete.
    """
    if not post_id:
        raise InvalidRequestException("The 'post_id' parameter is not valid.")
    data = _load_data()
    posts = data.get('posts', [])
    exists = any(p.get('post_id') == post_id for p in posts)
    if not exists:
        raise NotFoundException("The 'post_id' parameter is not found.")
    data['posts'] = [p for p in posts if p.get('post_id') != post_id]
    _save_data(data)
    return {'success': True}


def CreateComment(post_id: str, content: str) -> Dict[str, Any]:
    """Create a comment on a specific post.
    
    Args:
        post_id (str): The ID of the post to comment on.
        content (str): The text content of the comment.
    """
    if not post_id:
        raise InvalidRequestException("The 'post_id' parameter is not valid.")
    if not isinstance(content, str) or not content.strip():
        raise InvalidRequestException("The 'content' parameter is empty.")
    data = _load_data()
    post = next((p for p in data.get('posts', []) if p.get('post_id') == post_id), None)
    if not post:
        raise NotFoundException("The 'post_id' parameter is not found.")
    comment_id = _new_id('cmt')
    comment = {
        'comment_id': comment_id,
        'post_id': post_id,
        'user_id': data.get('user', {}).get('user_id', 'u_me'),
        'content': content.strip(),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    data.setdefault('comments', []).append(comment)
    _save_data(data)
    return {'success': True}


def GetMessages(friend_id: str, max_results: int = 10) -> Dict[str, Any]:
    """Get message history with a specific friend.
    
    Args:
        friend_id (str): The ID of the friend whose messages to retrieve.
        max_results (int): Maximum number of messages to return.
    """
    if not friend_id:
        raise InvalidRequestException("The 'friend_id' parameter is not valid.")
    try:
        max_res = int(max_results) if max_results is not None else 10
    except (ValueError, TypeError):
        raise InvalidRequestException("The 'max_results' parameter is not valid.")
    if max_res <= 0:
        raise InvalidRequestException("The 'max_results' parameter is not valid.")
    data = _load_data()
    friend_exists = any(f.get('user_id') == friend_id for f in data.get('friends', []))
    if not friend_exists:
        raise NotFoundException("The 'friend_id' parameter is not found.")
    msgs = [m for m in data.get('messages', []) if m.get('friend_id') == friend_id]
    return {'messages': msgs[:max_res]}


def SendFacebookMessage(recipient_id: str, content: str) -> Dict[str, Any]:
    """Send a message to a specific recipient.
    
    Args:
        recipient_id (str): The ID of the message recipient.
        content (str): The text content of the message.
    """
    if not recipient_id:
        raise InvalidRequestException("The 'recipient_id' parameter is not valid.")
    if not isinstance(content, str) or not content.strip():
        raise InvalidRequestException("The 'content' parameter is empty.")
    data = _load_data()
    known = any(u.get('user_id') == recipient_id for u in data.get('friends', []) + [data.get('user', {})])
    if not known:
        raise NotFoundException("The 'recipient_id' parameter is not found.")
    msg = {
        'friend_id': recipient_id,
        'direction': 'outgoing',
        'content': content.strip(),
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    }
    data.setdefault('messages', []).append(msg)
    _save_data(data)
    return {'success': True}
