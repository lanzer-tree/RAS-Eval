from langchain_core.tools import tool
from mcp.server.fastmcp import FastMCP
import time
import json


mcp = FastMCP('clock_toolkit')
alarms = []


database_path = 'environment/clock.json'


def _connect_to_clock() -> list:
    with open(database_path, 'r') as file:
        alarms: list = json.load(file)
    for index, alarm in enumerate(alarms):
        alarms[index] = time.strptime(alarm, '%H:%M:%S')
    return alarms


def _disconnect_from_clock(alarms: list) -> None:
    for index, alarm in enumerate(alarms):
        alarms[index] = time.strftime('%H:%M:%S', alarm)
    with open(database_path, 'w') as file:
        json.dump(alarms, file, indent=4)


def set_alarm(alarm_time: str) -> dict:
    """
    Set an alarm for a specific time.

    Args:
        alarm_time (str): The time to set the alarm for. Format: HH:MM:SS

    Returns:
        dict: A dictionary containing a success flag and a description.
    """
    alarms = _connect_to_clock()
    alarm = time.strptime(alarm_time, '%H:%M:%S')
    alarms.append(alarm)
    _disconnect_from_clock(alarms)
    return {'success': True, 'description': f'Alarm set for {alarm_time}.'}


@tool(parse_docstring=True)
def langgraph_set_alarm(alarm_time: str) -> dict:
    """
    Set an alarm for a specific time.

    Args:
        alarm_time (str): The time to set the alarm for. Format: HH:MM:SS

    Returns:
        dict: A dictionary containing a success flag and a description.
    """
    return set_alarm(alarm_time=alarm_time)


@mcp.tool()
def mcp_set_alarm(alarm_time: str) -> dict:
    """
    Set an alarm for a specific time.

    Args:
        alarm_time (str): The time to set the alarm for. Format: HH:MM:SS

    Returns:
        dict: A dictionary containing a success flag and a description.
    """
    return set_alarm(alarm_time=alarm_time)


def cancel_alarm(alarm_time: str) -> dict:
    """
    Cancel the currently set alarm.

    Args:
        alarm_time (str): The time of the alarm to cancel. Format: HH:MM:SS

    Returns:
        dict: A dictionary containing a success flag and a description.
    """
    alarms = _connect_to_clock()
    alarm = time.strptime(alarm_time, '%H:%M:%S')
    if alarm not in alarms:
        return {'success': False, 'description': f'No alarm is set at {alarm_time}'}
    alarms.remove(alarm)
    _disconnect_from_clock(alarms)
    return {'success': True, 'description': f'Alarm at {alarm_time} has been cancelled.'}


@tool(parse_docstring=True)
def langgraph_cancel_alarm(alarm_time: str) -> dict:
    """
    Cancel the currently set alarm.

    Args:
        alarm_time (str): The time of the alarm to cancel. Format: HH:MM:SS

    Returns:
        dict: A dictionary containing a success flag and a description.
    """
    return cancel_alarm(alarm_time=alarm_time)


@mcp.tool()
def mcp_cancel_alarm(alarm_time: str) -> dict:
    """
    Cancel the currently set alarm.

    Args:
        alarm_time (str): The time of the alarm to cancel. Format: HH:MM:SS

    Returns:
        dict: A dictionary containing a success flag and a description.
    """
    return cancel_alarm(alarm_time=alarm_time)


def get_current_time() -> dict:
    """
    Get the current time.

    Returns:
        dict: A dictionary containing the current time in the format "HH:MM:SS".
    """
    current_time = time.strftime('%H:%M:%S', time.localtime(time.time()))
    return {'current_time': current_time}


@tool(parse_docstring=True)
def langgraph_get_current_time() -> dict:
    """
    Get the current time.

    Returns:
        dict: A dictionary containing the current time in the format "HH:MM:SS".
    """
    return get_current_time()


@mcp.tool()
def mcp_get_current_time() -> dict:
    """
    Get the current time.

    Returns:
        dict: A dictionary containing the current time in the format "HH:MM:SS".
    """
    return get_current_time()


def timer(duration: float) -> dict:
    """
    Start a timer for a specific duration.

    Args:
        duration (float): The duration of the timer in seconds.

    Returns:
        dict: A dictionary containing a success flag and a description.
    """
    time.sleep(duration)
    return {'success': True, 'description': f'Timer finished after {duration} seconds.'}


@tool(parse_docstring=True)
def langgraph_timer(duration: float) -> dict:
    """
    Start a timer for a specific duration.

    Args:
        duration (float): The duration of the timer in seconds.

    Returns:
        dict: A dictionary containing a success flag and a description.
    """
    return timer(duration=duration)


@mcp.tool()
def mcp_timer(duration: float) -> dict:
    """
    Start a timer for a specific duration.

    Args:
        duration (float): The duration of the timer in seconds.

    Returns:
        dict: A dictionary containing a success flag and a description.
    """
    return timer(duration=duration)


