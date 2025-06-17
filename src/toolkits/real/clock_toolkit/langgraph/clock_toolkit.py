from langchain_core.tools import tool
from src.toolkits.real.clock_toolkit.function.clock_toolkit import set_alarm
from src.toolkits.real.clock_toolkit.function.clock_toolkit import cancel_alarm
from src.toolkits.real.clock_toolkit.function.clock_toolkit import get_current_time
from src.toolkits.real.clock_toolkit.function.clock_toolkit import timer
import time
import json


alarms = []
database_path = 'environment/clock.json'


@tool(parse_docstring=True)
def _set_alarm(alarm_time: str) -> dict:
    """
    Set an alarm for a specific time.

    Args:
        alarm_time (str): The time to set the alarm for. Format: HH:MM:SS

    Returns:
        dict: A dictionary containing a success flag and a description.
    """
    return set_alarm(alarm_time=alarm_time)


@tool(parse_docstring=True)
def _cancel_alarm(alarm_time: str) -> dict:
    """
    Cancel the currently set alarm.

    Args:
        alarm_time (str): The time of the alarm to cancel. Format: HH:MM:SS

    Returns:
        dict: A dictionary containing a success flag and a description.
    """
    return cancel_alarm(alarm_time=alarm_time)


@tool(parse_docstring=True)
def _get_current_time() -> dict:
    """
    Get the current time.

    Returns:
        dict: A dictionary containing the current time in the format "HH:MM:SS".
    """
    return get_current_time()


@tool(parse_docstring=True)
def _timer(duration: float) -> dict:
    """
    Start a timer for a specific duration.

    Args:
        duration (float): The duration of the timer in seconds.

    Returns:
        dict: A dictionary containing a success flag and a description.
    """
    return timer(duration=duration)


