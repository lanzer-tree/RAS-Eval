from mcp.server.fastmcp import FastMCP
from src.toolkits.real.calendar_toolkit.function.calendar_toolkit import add_event_to_calendar
from src.toolkits.real.calendar_toolkit.function.calendar_toolkit import get_events_from_calendar
from src.toolkits.real.calendar_toolkit.function.calendar_toolkit import search_event
from src.toolkits.real.calendar_toolkit.function.calendar_toolkit import remove_event_from_calendar
from src.toolkits.real.calendar_toolkit.function.calendar_toolkit import get_today_date
from typing import Optional
import datetime
import json


mcp = FastMCP('calendar_toolkit')
events = []
database_path = 'environment/calendar.json'


@mcp.tool()
def _add_event_to_calendar(start_time: str, end_time: str, event: str, location: Optional[str]=None) -> dict:
    """
    Add event to the calendar.

    Args:
        start_time: start time of the event. Format: "YYYY-MM-DD HH:MM:SS"
        end_time: end time of the event. Format: "YYYY-MM-DD HH:MM:SS"
        event: event name
        location: location of the event

    Returns:
        dict: success status and description
    """
    return add_event_to_calendar(start_time=start_time, end_time=end_time, event=event, location=location)


@mcp.tool()
def _get_events_from_calendar(start_time: str, end_time: str) -> list[dict[str, str]]:
    """
    Get all events from the calendar within the given time range.

    Args:
        start_time: start time of the event. Format: "YYYY-MM-DD HH:MM:SS"
        end_time: end time of the event. Format: "YYYY-MM-DD HH:MM:SS"

    Returns:
        list: list of events within the given time range
    """
    return get_events_from_calendar(start_time=start_time, end_time=end_time)


@mcp.tool()
def _search_event(event: str) -> dict:
    """
    Search for an event in the calendar. Calculate how much time is left until the event.

    Args:
        event: event name

    Returns:
        dict: event details
    """
    return search_event(event=event)


@mcp.tool()
def _remove_event_from_calendar(event: str) -> dict:
    """
    Remove event from the calendar.

    Args:
        event: event name

    Returns:
        dict: success status and description
    """
    return remove_event_from_calendar(event=event)


@mcp.tool()
def _get_today_date() -> dict:
    """
    Get today's date.

    Returns:
        dict: success status and today's date in format "YYYY-MM-DD"
    """
    return get_today_date()


if __name__ == '__main__':
    mcp.run('stdio')
