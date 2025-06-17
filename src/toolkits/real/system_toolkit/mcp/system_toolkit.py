from mcp.server.fastmcp import FastMCP
from src.toolkits.real.system_toolkit.function.system_toolkit import get_cpu_info
from src.toolkits.real.system_toolkit.function.system_toolkit import get_disk_info
from src.toolkits.real.system_toolkit.function.system_toolkit import get_memory_info
from src.toolkits.real.system_toolkit.function.system_toolkit import download_file
from src.toolkits.real.system_toolkit.function.system_toolkit import list_files
from src.toolkits.real.system_toolkit.function.system_toolkit import delete_file
import psutil
import requests
import os


mcp = FastMCP('system_toolkit')


@mcp.tool()
def _get_cpu_info() -> dict[str, str | int]:
    """
    A tool that provides real-time access to CPU information.

    Returns:
        dict[str, str | int]: The CPU information.
    """
    return get_cpu_info()


@mcp.tool()
def _get_disk_info() -> dict[str, str]:
    """
    A tool that provides real-time access to disk information.

    Returns:
        dict[str, str]: The disk information.
    """
    return get_disk_info()


@mcp.tool()
def _get_memory_info() -> dict[str, str]:
    """
    A tool that provides real-time access to memory information.

    Returns:
        dict[str, str]: The memory information.
    """
    return get_memory_info()


@mcp.tool()
def _download_file(url: str, path: str) -> dict:
    """
    Download a file from the internet and save it to the specified path.

    Args:
        url (str): The URL of the file to download.
        path (str): The path to save the downloaded file.

    Returns:
        dict: success status and description.
    """
    return download_file(url=url, path=path)


@mcp.tool()
def _list_files(path: str) -> dict:
    """
    List all files in the specified path.

    Args:
        path (str): The path to list files from.

    Returns:
        dict: success status and description.
    """
    return list_files(path=path)


@mcp.tool()
def _delete_file(path: str) -> dict:
    """
    Delete a file from the specified path.

    Args:
        path (str): The path of the file to delete.

    Returns:
        dict: success status and description.
    """
    return delete_file(path=path)


if __name__ == '__main__':
    mcp.run('stdio')
