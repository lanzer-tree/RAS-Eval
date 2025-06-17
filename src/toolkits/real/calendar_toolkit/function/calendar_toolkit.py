from typing import Optional
import datetime
import json


events = []
database_path = "environment/calendar.json"


def _connect_to_calendar() -> list:
    with open(database_path, "r") as file:
        events: list = json.load(file)
    for index, event in enumerate(events):
        events[index]["start_time"] = datetime.datetime.strptime(event["start_time"], "%Y-%m-%d %H:%M:%S")
        events[index]["end_time"] = datetime.datetime.strptime(event["end_time"], "%Y-%m-%d %H:%M:%S")
    return events


def _disconnect_from_calendar(events: list) -> None:
    for index, event in enumerate(events):
        events[index]["start_time"] = datetime.datetime.strftime(event["start_time"], "%Y-%m-%d %H:%M:%S")
        events[index]["end_time"] = datetime.datetime.strftime(event["end_time"], "%Y-%m-%d %H:%M:%S")
    with open(database_path, "w") as file:
        json.dump(events, file, indent=4)


def add_event_to_calendar(start_time: str, end_time: str, event: str, location: Optional[str] = None) -> dict:
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
    if location is None:
        location = ""
    events = _connect_to_calendar()
    event_item = {
        "start_time": datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S"),
        "end_time": datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S"),
        "event": event.lower(),
        "location": location
    }
    events.append(event_item)
    _disconnect_from_calendar(events)
    return {"success": True, "description": f"Event {event} added to the calendar."}


def get_events_from_calendar(start_time: str, end_time: str) -> list[dict[str, str]]:
    """
    Get all events from the calendar within the given time range.

    Args:
        start_time: start time of the event. Format: "YYYY-MM-DD HH:MM:SS"
        end_time: end time of the event. Format: "YYYY-MM-DD HH:MM:SS"

    Returns:
        list: list of events within the given time range
    """
    events = _connect_to_calendar()
    start_time = datetime.datetime.strptime(start_time, "%Y-%m-%d %H:%M:%S")
    end_time = datetime.datetime.strptime(end_time, "%Y-%m-%d %H:%M:%S")
    result = []
    for event in events:
        if event["start_time"] >= start_time and event["end_time"] <= end_time:
            item = {
                "start_time": datetime.datetime.strftime(event["start_time"], "%Y-%m-%d %H:%M:%S"),
                "end_time": datetime.datetime.strftime(event["end_time"], "%Y-%m-%d %H:%M:%S"),
                "location": event["location"],
                "event": event["event"],
            }
            result.append(item)
    _disconnect_from_calendar(events)
    return result


def search_event(event: str) -> dict:
    """
    Search for an event in the calendar. Calculate how much time is left until the event.

    Args:
        event: event name

    Returns:
        dict: event details
    """
    events = _connect_to_calendar()
    for record in events:
        if record["event"] == event.lower():
            res = {
                "start_time": str(record["start_time"]),
                "end_time": str(record["end_time"]),
                "event": record["event"],
                "location": record["location"],
                "time_left": str(record["start_time"] - datetime.datetime.now())

            }
            _disconnect_from_calendar(events)
            return res
    _disconnect_from_calendar(events)
    return {"error": f"Event {event} not found."}


def remove_event_from_calendar(event: str) -> dict:
    """
    Remove event from the calendar.

    Args:
        event: event name

    Returns:
        dict: success status and description
    """
    events = _connect_to_calendar()
    for record in events:
        if record["event"] == event.lower():
            events.remove(record)
            _disconnect_from_calendar(events)
            return {"success": True, "description": f"Event {event} removed from the calendar."}
    _disconnect_from_calendar(events)
    return {"success": False, "description": f"Event {event} is not in calendar."}


def get_today_date() -> dict:
    """
    Get today's date.

    Returns:
        dict: success status and today's date in format "YYYY-MM-DD"
    """
    return {"success": True, "today": str(datetime.date.today())}

