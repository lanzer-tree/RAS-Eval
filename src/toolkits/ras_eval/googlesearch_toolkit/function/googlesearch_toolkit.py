import os
import json
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional

DATA_PATH = 'environment/reports/googlesearch.json'
INIT_PATH = 'environment/initial/googlesearch_init.json'

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
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4)


def web_search(keyword: str, num_results: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Perform a web search on Google with a given keyword or phrase and return the search results.

    Args:
        keyword (str): The keyword or phrase to search.
        num_results (int): The maximum number of results to return. Default is 10.
        filters (Optional[Dict[str, Any]]): The filters to apply, includes 'time_range' (string, in the format of 'YYYY-MM-DD..YYYY-MM-DD'), 'language' (string, in the format of ISO 639-1 language code), and 'region' (string, in the format of ISO 3166-1 alpha-2 country code).
    """
    if not keyword or not isinstance(num_results, (int, str)) or int(num_results) <= 0:
        return {"error": "InvalidRequestException", "message": "The 'keyword' is empty or the 'num_results' is not a positive integer."}
    
    num_results = int(num_results)
    
    # Simulate search results
    results = [
        {"title": f"Result 1 for {keyword}", "snippet": f"Snippet for {keyword} result 1", "url": f"https://example.com/1"},
        {"title": f"Result 2 for {keyword}", "snippet": f"Snippet for {keyword} result 2", "url": f"https://example.com/2"},
    ]
    if num_results < len(results):
        results = results[:num_results]
    
    # Add to history
    try:
        data = _load_data()
        history = data.get("search_history", [])
        history.append({
            "keyword": keyword,
            "time": datetime.now().strftime("%Y-%m-%d:%H:%M:%S"),
            "type": "web"
        })
        data["search_history"] = history
        _save_data(data)
    except Exception as e:
        # If data operation fails, still return results
        pass
    
    if not results:
        return {"error": "NotFoundException", "message": "No search results are found."}
    
    return {"results": results}


def image_search(keyword: str, num_results: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Perform an image search on Google with a given keyword or phrase and return the search results.

    Args:
        keyword (str): The keyword or phrase to search.
        num_results (int): The maximum number of results to return. Default is 10.
        filters (Optional[Dict[str, Any]]): The filters to apply, includes 'time_range' (string, in the format of 'YYYY-MM-DD..YYYY-MM-DD'), 'language' (string, in the format of ISO 639-1 language code), and 'region' (string, in the format of ISO 3166-1 alpha-2 country code).
    """
    if not keyword or not isinstance(num_results, (int, str)) or int(num_results) <= 0:
        return {"error": "InvalidRequestException", "message": "The 'keyword' is empty or the 'num_results' is not a positive integer."}
    
    num_results = int(num_results)
    
    # Simulate image search results
    results = [
        {"title": f"Image 1 for {keyword}", "url": f"https://example.com/image1.jpg", "size": "1024x768", "format": "jpg", "source": "example.com"},
        {"title": f"Image 2 for {keyword}", "url": f"https://example.com/image2.png", "size": "800x600", "format": "png", "source": "example.com"},
    ]
    if num_results < len(results):
        results = results[:num_results]
    
    # Add to history
    try:
        data = _load_data()
        history = data.get("search_history", [])
        history.append({
            "keyword": keyword,
            "time": datetime.now().strftime("%Y-%m-%d:%H:%M:%S"),
            "type": "image"
        })
        data["search_history"] = history
        _save_data(data)
    except Exception as e:
        # If data operation fails, still return results
        pass
    
    if not results:
        return {"error": "NotFoundException", "message": "No search results are found."}
    
    return {"results": results}


def video_search(keyword: str, num_results: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Perform a video search on Google with a given keyword or phrase and return the search results.

    Args:
        keyword (str): The keyword or phrase to search.
        num_results (int): The maximum number of results to return. Default is 10.
        filters (Optional[Dict[str, Any]]): The filters to apply, includes 'time_range' (string, in the format of 'YYYY-MM-DD..YYYY-MM-DD'), 'language' (string, in the format of ISO 639-1 language code), and 'region' (string, in the format of ISO 3166-1 alpha-2 country code).
    """
    if not keyword or not isinstance(num_results, (int, str)) or int(num_results) <= 0:
        return {"error": "InvalidRequestException", "message": "The 'keyword' is empty or the 'num_results' is not a positive integer."}
    
    num_results = int(num_results)
    
    # Simulate video search results
    results = [
        {"title": f"Video 1 for {keyword}", "url": f"https://example.com/video1.mp4", "duration": "5:30", "format": "mp4"},
        {"title": f"Video 2 for {keyword}", "url": f"https://example.com/video2.avi", "duration": "3:45", "format": "avi"},
    ]
    if num_results < len(results):
        results = results[:num_results]
    
    # Add to history
    try:
        data = _load_data()
        history = data.get("search_history", [])
        history.append({
            "keyword": keyword,
            "time": datetime.now().strftime("%Y-%m-%d:%H:%M:%S"),
            "type": "video"
        })
        data["search_history"] = history
        _save_data(data)
    except Exception as e:
        # If data operation fails, still return results
        pass
    
    if not results:
        return {"error": "NotFoundException", "message": "No search results are found."}
    
    return {"results": results}


def news_search(keyword: str, num_results: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Perform a news search on Google with a given keyword or phrase and return the search results.

    Args:
        keyword (str): The keyword or phrase to search.
        num_results (int): The maximum number of results to return. Default is 10.
        filters (Optional[Dict[str, Any]]): The filters to apply, includes 'time_range' (string, in the format of 'YYYY-MM-DD..YYYY-MM-DD'), 'language' (string, in the format of ISO 639-1 language code), and 'region' (string, in the format of ISO 3166-1 alpha-2 country code).
    """
    if not keyword or not isinstance(num_results, (int, str)) or int(num_results) <= 0:
        return {"error": "InvalidRequestException", "message": "The 'keyword' is empty or the 'num_results' is not a positive integer."}
    
    num_results = int(num_results)
    
    # Simulate news search results
    results = [
        {"title": f"News 1 for {keyword}", "snippet": f"Snippet for {keyword} news 1", "url": f"https://news.example.com/1", "source": "News Source 1"},
        {"title": f"News 2 for {keyword}", "snippet": f"Snippet for {keyword} news 2", "url": f"https://news.example.com/2", "source": "News Source 2"},
    ]
    if num_results < len(results):
        results = results[:num_results]
    
    # Add to history
    try:
        data = _load_data()
        history = data.get("search_history", [])
        history.append({
            "keyword": keyword,
            "time": datetime.now().strftime("%Y-%m-%d:%H:%M:%S"),
            "type": "news"
        })
        data["search_history"] = history
        _save_data(data)
    except Exception as e:
        # If data operation fails, still return results
        pass
    
    if not results:
        return {"error": "NotFoundException", "message": "No search results are found."}
    
    return {"results": results}

def get_search_trends(time_range: Optional[str] = None, location: Optional[str] = None) -> Dict[str, Any]:
    """
    Access the search trends on Google.

    Args:
        time_range (str): The time range to get the search trends, in the format of 'YYYY-MM-DD..YYYY-MM-DD'. Default is the past 7 days.
        location (str): The location to get the search trends, in the format of ISO 3166-1 alpha-2 country code. Default is not restricted to a specific location and shows global trends.

    Returns:
        dict: A dictionary containing the search trends or error.
    """
    # Validate time_range if provided
    if time_range and not _is_valid_time_range(time_range):
        return {"error": "InvalidRequestException", "message": "The 'time_range' is invalid."}
    
    # Simulate trends
    trends = [
        {"keyword": "trending topic 1", "search_volume": 1000, "increase_percentage": 20},
        {"keyword": "trending topic 2", "search_volume": 800, "increase_percentage": 15},
    ]
    
    return {"trends": trends}

def get_search_history(time_range: Optional[str] = None) -> Dict[str, Any]:
    """
    Retrieve the user's search history.

    Args:
        time_range (str): The time range to get the search history, in the format of 'YYYY-MM-DD..YYYY-MM-DD'. Default is the past 7 days.

    Returns:
        dict: A dictionary containing the user's search history or error.
    """
    if time_range and not _is_valid_time_range(time_range):
        return {"error": "InvalidRequestException", "message": "The 'time_range' is invalid."}
    
    try:
        data = _load_data()
        history = data.get("search_history", [])
        
        # Filter by time_range if provided
        if time_range:
            start_date, end_date = time_range.split('..')
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")
            filtered_history = []
            for item in history:
                item_date = datetime.strptime(item["time"].split(':')[0], "%Y-%m-%d")
                if start <= item_date <= end:
                    filtered_history.append(item)
            history = filtered_history
        
        return {"history": history}
    except Exception as e:
        return {"error": "InternalError", "message": "Failed to load search history."}

def _is_valid_time_range(time_range: str) -> bool:
    try:
        start, end = time_range.split('..')
        datetime.strptime(start, "%Y-%m-%d")
        datetime.strptime(end, "%Y-%m-%d")
        return True
    except:
        return False