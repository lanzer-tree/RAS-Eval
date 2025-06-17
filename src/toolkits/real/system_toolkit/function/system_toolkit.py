import psutil
import requests
import os


def get_cpu_info() -> dict[str, str | int]:
    """
    A tool that provides real-time access to CPU information.

    Returns:
        dict[str, str | int]: The CPU information.
    """
    cpu_info = {
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": f"{psutil.cpu_percent(interval=1)}%",
    }
    return cpu_info


def get_disk_info() -> dict[str, str]:
    """
    A tool that provides real-time access to disk information.

    Returns:
        dict[str, str]: The disk information.
    """
    disk_info = {
        "disk_usage": f"{psutil.disk_usage('/').percent}%",
        "disk_total": f"{psutil.disk_usage('/').total / 1024 ** 3:.2f} GB",
        "disk_free": f"{psutil.disk_usage('/').free / 1024 ** 3:.2f} GB",
        "disk_used": f"{psutil.disk_usage('/').used / 1024 ** 3:.2f} GB",
    }
    return disk_info


def get_memory_info() -> dict[str, str]:
    """
    A tool that provides real-time access to memory information.

    Returns:
        dict[str, str]: The memory information.
    """
    memory_info = {
        "memory_usage": f"{psutil.virtual_memory().percent}%",
        "memory_total": f"{psutil.virtual_memory().total / 1024 ** 3:.2f} GB",
        "memory_free": f"{psutil.virtual_memory().free / 1024 ** 3:.2f} GB",
        "memory_used": f"{psutil.virtual_memory().used / 1024 ** 3:.2f} GB",
    }
    return memory_info


def download_file(url: str, path: str) -> dict:
    """
    Download a file from the internet and save it to the specified path.

    Args:
        url (str): The URL of the file to download.
        path (str): The path to save the downloaded file.

    Returns:
        dict: success status and description.
    """
    try:
        response = requests.get(url)
        with open(path, "wb") as file:
            file.write(response.content)
        return {"success": True, "description": f"File {path} downloaded successfully."}
    except Exception as error:
        return {"success": False, "description": f"Error: {error}"}
    

def list_files(path: str) -> dict:
    """
    List all files in the specified path.

    Args:
        path (str): The path to list files from.

    Returns:
        dict: success status and description.
    """
    try:
        res = os.listdir(path)
    except Exception as error:
        return {"success": False, "description": f"Error: {error}"}
    else:
        return {"success": True, "files": res}
    

def delete_file(path: str) -> dict:
    """
    Delete a file from the specified path.

    Args:
        path (str): The path of the file to delete.

    Returns:
        dict: success status and description.
    """
    try:
        os.remove(path)
        return {"success": True, "description": f"File {path} deleted successfully."}
    except Exception as error:
        return {"success": False, "description": f"Error: {error}"}
    