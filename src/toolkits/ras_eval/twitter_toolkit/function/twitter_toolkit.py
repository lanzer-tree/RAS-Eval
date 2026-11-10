import os
import json
import shutil
import secrets
from datetime import datetime
from typing import Any, Dict, List, Optional

DATA_PATH = 'environment/reports/twitter.json'
INIT_PATH = 'environment/initial/twitter_init.json'

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


def _now() -> str:
    return datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')


def _validate_content(content: str, max_length: int = 280):
    if not isinstance(content, str) or not content.strip():
        raise InvalidRequestException("The 'content' parameter is not valid.")
    if len(content) > max_length:
        raise InvalidRequestException("The 'content' parameter is too long.")


def _normalize_media_paths(media_paths: Any, data: Dict[str, Any]) -> List[str]:
    if media_paths is None or (isinstance(media_paths, str) and not media_paths.strip()):
        return []
    if isinstance(media_paths, str):
        media_list = [media_paths]
    elif isinstance(media_paths, list):
        media_list = media_paths
    else:
        raise InvalidRequestException("The 'media_paths' parameter is not valid.")
    if len(media_list) > 4:
        raise InvalidRequestException("The 'media_paths' parameter has too many items.")
    valid_files = set(data.get('media_files', []))
    for m in media_list:
        if not isinstance(m, str) or not m.strip():
            raise InvalidRequestException("The 'media_paths' parameter is not valid.")
        if valid_files and m not in valid_files:
            raise NotFoundException(f"Media file not found: {m}")
    return media_list


def _find_tweet(data: Dict[str, Any], tweet_id: str) -> Dict[str, Any]:
    if not tweet_id:
        raise NotFoundException("The 'tweet_id' parameter is not found.")
    tweet = next((t for t in data.get('tweets', []) if t.get('tweet_id') == tweet_id), None)
    if not tweet:
        raise NotFoundException("The 'tweet_id' parameter is not found.")
    return tweet


def PostTweet(content: str, media_paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """Post a new tweet with optional media attachments.
    
    Args:
        content (str): The text content of the tweet, maximum 280 characters.
        media_paths (Optional[List[str]]): List of media file paths to attach, maximum 4 items.
    """
    _validate_content(content)
    data = _load_data()
    media_list = _normalize_media_paths(media_paths, data)
    tweet_id = _new_id('tw')
    tweet = {
        'tweet_id': tweet_id,
        'user_id': data.get('user', {}).get('user_id', 'u_me'),
        'content': content.strip(),
        'media_paths': media_list,
        'timestamp': _now(),
        'likes': [],
        'retweets': [],
        'replies': [],
        'reply_to': ''
    }
    data.setdefault('tweets', []).append(tweet)
    _save_data(data)
    return {'tweet_id': tweet_id}


def SearchTweets(query: str, max_results: Optional[int] = None, own_tweets: bool = False) -> Dict[str, Any]:
    """Search for tweets matching a query string.
    
    Args:
        query (str): The search query string to match against tweet content.
        max_results (int): Maximum number of results to return, must be positive.
        own_tweets (bool): Whether to only return tweets posted by the current user.
    """
    if not isinstance(query, str):
        raise InvalidRequestException("The 'query' parameter is empty.")
    query_stripped = query.strip()
    if max_results is None:
        max_res = 10
    else:
        try:
            max_res = int(max_results)
        except (ValueError, TypeError):
            raise InvalidRequestException("The 'max_results' parameter is not valid.")
    if max_res <= 0:
        raise InvalidRequestException("The 'max_results' parameter is not valid.")
    data = _load_data()
    my_id = data.get('user', {}).get('user_id', 'u_me')
    results = []
    for t in data.get('tweets', []):
        if own_tweets and t.get('user_id') != my_id:
            continue
        if not query_stripped or query_stripped.lower() in t.get('content', '').lower():
            results.append({
                'tweet_id': t.get('tweet_id'),
                'user_id': t.get('user_id'),
                'content': t.get('content'),
                'timestamp': t.get('timestamp')
            })
        if len(results) >= max_res:
            break
    return {'tweets': results}


def ReadTweet(tweet_id: str) -> Dict[str, Any]:
    """Read a specific tweet by its ID.
    
    Args:
        tweet_id (str): The unique identifier of the tweet to read.
    """
    if not tweet_id:
        raise InvalidRequestException("The 'tweet_id' parameter is not valid.")
    data = _load_data()
    tweet = _find_tweet(data, tweet_id)
    return {'tweet': tweet}


def DeleteTweets(tweet_ids: List[str]) -> Dict[str, Any]:
    """Delete one or more tweets owned by the current user.
    
    Args:
        tweet_ids (List[str]): List of tweet IDs to delete.
    """
    if isinstance(tweet_ids, str):
        tweet_ids = [tweet_ids]
    if not isinstance(tweet_ids, list) or not tweet_ids:
        raise InvalidRequestException("The 'tweet_ids' parameter is not valid.")
    data = _load_data()
    my_id = data.get('user', {}).get('user_id', 'u_me')
    tweets = data.get('tweets', [])
    for tid in tweet_ids:
        t = next((item for item in tweets if item.get('tweet_id') == tid), None)
        if not t:
            continue
        if t.get('user_id') != my_id:
            raise InvalidRequestException('Cannot delete tweets not owned by user.')
    data['tweets'] = [t for t in tweets if t.get('tweet_id') not in tweet_ids]
    _save_data(data)
    return {'success': True}


def FollowUsers(user_ids: List[str]) -> Dict[str, Any]:
    """Follow one or more users by their user IDs.
    
    Args:
        user_ids (List[str]): List of user IDs to follow.
    """
    if isinstance(user_ids, str):
        user_ids = [user_ids]
    if not isinstance(user_ids, list) or not user_ids:
        raise InvalidRequestException("The 'user_ids' parameter is not valid.")
    data = _load_data()
    my_id = data.get('user', {}).get('user_id', 'u_me')
    known_users = {u.get('user_id') for u in data.get('users', [])}
    known_users.add(my_id)
    following = set(data.get('follows', {}).get('following', []))
    for uid in user_ids:
        if uid not in known_users:
            continue
        if uid != my_id:
            following.add(uid)
    data.setdefault('follows', {})['following'] = sorted(following)
    _save_data(data)
    return {'success': True}


def UnfollowUsers(user_ids: List[str]) -> Dict[str, Any]:
    """Unfollow one or more users by their user IDs.
    
    Args:
        user_ids (List[str]): List of user IDs to unfollow.
    """
    if not isinstance(user_ids, list) or not user_ids:
        raise InvalidRequestException("The 'user_ids' parameter is not valid.")
    data = _load_data()
    following = set(data.get('follows', {}).get('following', []))
    for uid in user_ids:
        following.discard(uid)
    data.setdefault('follows', {})['following'] = sorted(following)
    _save_data(data)
    return {'success': True}


def GetUserProfile(user_id: str = '') -> Dict[str, Any]:
    """Get the profile of a user.
    
    Args:
        user_id (str): The user ID to get profile for, empty string for current user.
    """
    data = _load_data()
    if not user_id:
        return {'profile': data.get('user', {})}
    my_id = data.get('user', {}).get('user_id', 'u_me')
    if user_id == my_id:
        return {'profile': data.get('user', {})}
    profile = next((u for u in data.get('users', []) if u.get('user_id') == user_id), None)
    if not profile:
        raise NotFoundException("The 'user_id' parameter is not found.")
    return {'profile': profile}


def LikeTweet(tweet_id: str) -> Dict[str, Any]:
    """Like a tweet by its ID.
    
    Args:
        tweet_id (str): The unique identifier of the tweet to like.
    """
    if not tweet_id:
        raise InvalidRequestException("The 'tweet_id' parameter is not valid.")
    data = _load_data()
    tweet = _find_tweet(data, tweet_id)
    my_id = data.get('user', {}).get('user_id', 'u_me')
    likes = set(tweet.get('likes', []))
    if my_id not in likes:
        likes.add(my_id)
        tweet['likes'] = sorted(likes)
        _save_data(data)
    return {'success': True}


def UnlikeTweet(tweet_id: str) -> Dict[str, Any]:
    """Unlike a tweet by its ID.
    
    Args:
        tweet_id (str): The unique identifier of the tweet to unlike.
    """
    if not tweet_id:
        raise InvalidRequestException("The 'tweet_id' parameter is not valid.")
    data = _load_data()
    try:
        tweet = _find_tweet(data, tweet_id)
    except NotFoundException:
        return {'success': True}
    my_id = data.get('user', {}).get('user_id', 'u_me')
    likes = set(tweet.get('likes', []))
    likes.discard(my_id)
    tweet['likes'] = sorted(likes)
    _save_data(data)
    return {'success': True}


def Retweet(tweet_id: str) -> Dict[str, Any]:
    """Retweet a tweet by its ID.
    
    Args:
        tweet_id (str): The unique identifier of the tweet to retweet.
    """
    if not tweet_id:
        raise InvalidRequestException("The 'tweet_id' parameter is not valid.")
    data = _load_data()
    try:
        original = _find_tweet(data, tweet_id)
    except NotFoundException:
        return {'success': False, 'description': 'Tweet not found'}
    my_id = data.get('user', {}).get('user_id', 'u_me')
    retweets = set(original.get('retweets', []))
    retweets.add(my_id)
    original['retweets'] = sorted(retweets)
    new_tweet_id = _new_id('tw')
    data.setdefault('tweets', []).append({
        'tweet_id': new_tweet_id,
        'user_id': my_id,
        'content': f"RT: {original.get('content', '')}",
        'media_paths': [],
        'timestamp': _now(),
        'likes': [],
        'retweets': [],
        'replies': [],
        'reply_to': tweet_id
    })
    _save_data(data)
    return {'success': True, 'tweet_id': new_tweet_id}


def ReplyToTweet(tweet_id: str, content: str, media_paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Reply to a tweet by its ID.
    
    Args:
        tweet_id (str): The unique identifier of the tweet to reply to.
        content (str): The text content of the reply, maximum 280 characters.
        media_paths (Optional[List[str]]): List of media file paths to attach, maximum 4 items.
    """
    if not tweet_id:
        raise InvalidRequestException("The 'tweet_id' parameter is not valid.")
    _validate_content(content, max_length=500)
    data = _load_data()
    try:
        original = _find_tweet(data, tweet_id)
    except NotFoundException:
        return {'success': False, 'description': 'Tweet not found'}
    media_list = _normalize_media_paths(media_paths, data)
    reply_id = _new_id('tw')
    my_id = data.get('user', {}).get('user_id', 'u_me')
    reply_tweet = {
        'tweet_id': reply_id,
        'user_id': my_id,
        'content': content.strip(),
        'media_paths': media_list,
        'timestamp': _now(),
        'likes': [],
        'retweets': [],
        'replies': [],
        'reply_to': tweet_id
    }
    data.setdefault('tweets', []).append(reply_tweet)
    replies = original.get('replies', [])
    replies.append(reply_id)
    original['replies'] = replies
    _save_data(data)
    return {'reply_tweet_id': reply_id}
