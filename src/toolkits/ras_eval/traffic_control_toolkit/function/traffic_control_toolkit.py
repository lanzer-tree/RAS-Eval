import json
import os
import re
import shutil
from datetime import datetime, timedelta
from typing import List, Tuple, Dict, Any, Optional

DATA_PATH = os.path.join('environment', 'reports', 'trafficControl.json')
INIT_PATH = os.path.join('environment', 'initial', 'trafficControl_init.json')

INIT = False

class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass

def _ensure_work_env() -> None:
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


def _read_env() -> Dict[str, Any]:
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _write_env(data: Dict[str, Any]) -> None:
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _validate_datetime(dt_str: str) -> datetime:
    if not dt_str:
        raise InvalidRequestException("Datetime string is empty")
    if isinstance(dt_str, datetime):
        return dt_str
    s = dt_str.strip()
    if s.lower() in ('now', 'immediate'):
        return datetime.utcnow()
    # try standard formats first
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M'):
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    # try time-only format (e.g., "06:15", "08:20", "14:00:00")
    for fmt in ('%H:%M:%S', '%H:%M'):
        try:
            t = datetime.strptime(s, fmt)
            return datetime.utcnow().replace(hour=t.hour, minute=t.minute, second=t.second, microsecond=0)
        except Exception:
            continue
    # try 12-hour time format (e.g., "5:00 PM", "7:00 AM", "12:00 PM")
    for fmt in ('%I:%M %p', '%I:%M%p', '%I:%M:%S %p', '%I:%M:%S%p'):
        try:
            t = datetime.strptime(s, fmt)
            return datetime.utcnow().replace(hour=t.hour, minute=t.minute, second=t.second, microsecond=0)
        except Exception:
            continue
    # try relative/descriptive datetime (e.g., "next Monday 6:00 AM", "Wednesday 10:00 PM")
    try:
        return _parse_relative_datetime(s)
    except Exception:
        raise InvalidRequestException("Datetime must be in 'yyyy-mm-dd HH:MM:SS' or 'yyyy-mm-dd HH:MM' format, or 'now'. Example: '2025-12-15 08:05:00'")


_MONTH_NAMES = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12
}
_DAY_NAMES = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']


def _parse_relative_datetime(s: str) -> datetime:
    """Parse relative datetime strings like 'next Monday 6:00 AM' or 'Wednesday 10:00 PM'."""
    raw = s.strip()
    text_lower = raw.lower()

    # Strip ordinals like "1st", "2nd", "3rd", "4th"
    text_lower = re.sub(r'(\d+)(st|nd|rd|th)\b', r'\1', text_lower)

    now = datetime.utcnow()
    result_date = now

    # Check for relative day indicators
    relative_map = {
        'next Monday': 7, 'next tuesday': 7, 'next wednesday': 7,
        'next thursday': 7, 'next friday': 7, 'next saturday': 7, 'next sunday': 7,
        'this Monday': 0, 'this tuesday': 0, 'this wednesday': 0,
        'this thursday': 0, 'this friday': 0, 'this saturday': 0, 'this sunday': 0,
        'Monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6,
        'monday': 0, 'tuesday': 2, 'wednesday': 3, 'thursday': 4,
        'friday': 5, 'saturday': 6, 'sunday': 0,
    }
    # Fix: correct next-day offsets
    # next X means: find the next occurrence of weekday X after today
    # We'll handle this with separate logic below

    found_day_name = None
    relative_offset = None

    for prefix in ('next ', 'this '):
        for day in _DAY_NAMES:
            key = prefix + day
            if key in text_lower:
                found_day_name = day
                if prefix == 'next ':
                    relative_offset = 7
                break
        if found_day_name:
            break

    if not found_day_name:
        for day in _DAY_NAMES:
            if day in text_lower and day not in _MONTH_NAMES:
                found_day_name = day
                # For bare day name (no "next"/"this"), find the next occurrence
                today_wday = now.weekday()  # Monday=0
                target_wday = _DAY_NAMES.index(day)
                diff = (target_wday - today_wday) % 7
                if diff == 0:
                    diff = 7  # if today matches, go to next week
                relative_offset = diff
                break

    if found_day_name:
        today_wday = now.weekday()
        target_wday = _DAY_NAMES.index(found_day_name)
        diff = (target_wday - today_wday) % 7
        if relative_offset == 7:
            # Find next occurrence (at least 7 days away, or wrap around)
            if diff == 0:
                diff = 7
            else:
                diff += 7
        elif relative_offset == 0 and diff == 0:
            # "this Monday" and today is Monday
            diff = 0
        elif relative_offset is None and diff == 0:
            # bare day name and today matches, go to next week
            diff = 7
        result_date = now + timedelta(days=diff)

    # Parse time portion (e.g., "6:00 AM", "10:00 PM")
    # Clean up: extract AM/PM and hour:minute
    time_match = re.search(r'(\d{1,2}):(\d{2})\s*(AM|PM)', raw, re.IGNORECASE)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        ampm = time_match.group(3).upper()
        if ampm == 'PM' and hour != 12:
            hour += 12
        elif ampm == 'AM' and hour == 12:
            hour = 0
        result_date = result_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
    else:
        # Try 24-hour time
        time_match24 = re.search(r'(\d{1,2}):\d{2}', raw)
        if time_match24:
            hour = int(time_match24.group(1))
            minute = int(time_match24.group(2))
            result_date = result_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

    return result_date


def _format_duration(minutes: int) -> str:
    total_seconds = max(0, minutes * 60)
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"


def _get_location(env: Dict[str, Any], location_id: str) -> Tuple[Dict[str, Any], str]:
    # support both schemas where id key may be 'road_id' or 'id'
    for road in env.get('roads', []):
        if road.get('road_id') == location_id or road.get('id') == location_id:
            return road, 'road'
    for inter in env.get('intersections', []):
        if inter.get('intersection_id') == location_id or inter.get('id') == location_id:
            return inter, 'intersection'
    return {}, ''


def _all_locations(env: Dict[str, Any]) -> List[Dict[str, str]]:
    data: List[Dict[str, str]] = []
    for road in env.get('roads', []):
        rid = road.get('road_id') or road.get('id')
        name = road.get('name') or road.get('road_name')
        data.append({'id': rid, 'name': name, 'type': 'road'})
    for inter in env.get('intersections', []):
        iid = inter.get('intersection_id') or inter.get('id')
        name = inter.get('name') or inter.get('intersection_name')
        data.append({'id': iid, 'name': name, 'type': 'intersection'})
    return data


def _validate_location_type(location_type: str) -> None:
    if location_type not in ('road', 'intersection'):
        raise InvalidRequestException("location_type must be 'road' or 'intersection'")


def _predict_congestion(base: str, hour: int) -> str:
    levels = ['low', 'medium', 'high', 'severe']
    try:
        idx = levels.index(base)
    except ValueError:
        idx = 1
    shift = 0
    if 7 <= hour <= 9 or 16 <= hour <= 19:
        shift = 1
    elif 0 <= hour <= 5:
        shift = -1
    idx = max(0, min(len(levels) - 1, idx + shift))
    return levels[idx]


def _normalize_text(s: str) -> str:
    if not s:
        return ''
    import re
    s2 = re.sub(r'[^0-9a-zA-Z]+', ' ', s).strip().lower()
    return ' '.join(s2.split())


def _resolve_location_id(env: Dict[str, Any], identifier: str, expected_type: str = None) -> Tuple[str, str]:
    """Resolve either an id or a human-readable name to (id, type).

    - If identifier matches an id field, return it.
    - Otherwise, try tokenized name matching via SearchLocations and return single best match.
    - If multiple matches, raise InvalidRequestException listing candidates.
    """
    if not identifier or not identifier.strip():
        raise InvalidRequestException('identifier is empty')
    ident = identifier.strip()
    # direct id match
    loc, loc_type = _get_location(env, ident)
    if loc_type:
        return ident, loc_type

    # try normalized name search
    q = _normalize_text(ident)
    exact_matches = []
    partial_matches = []
    for l in _all_locations(env):
        name_norm = _normalize_text(l.get('name') or '')
        if expected_type and l.get('type') != expected_type:
            continue
        if q == name_norm:
            exact_matches.append(l)
        elif q in name_norm or name_norm in q:
            partial_matches.append(l)

    candidates = exact_matches if exact_matches else partial_matches

    if not candidates:
        # token-based fallback: match if all query tokens appear in the name
        tokens = [t for t in q.split() if t]
        for l in _all_locations(env):
            name_norm = _normalize_text(l.get('name') or '')
            if expected_type and l.get('type') != expected_type:
                continue
            if all(token in name_norm for token in tokens):
                candidates.append(l)

    if not candidates:
        raise NotFoundException(f"No location matches '{identifier}'")
    if len(candidates) > 1:
        names = [f"{c.get('name')}:{c.get('id')}" for c in candidates]
        raise InvalidRequestException('Multiple locations match the identifier, please specify id. Matches: ' + ', '.join(names))
    return candidates[0].get('id'), candidates[0].get('type')


def SearchLocations(location_name: str, location_type: Optional[str] = None) -> Dict[str, Any]:
    """
    Search for locations by name and type.

    Args:
        location_name: The name or partial name of the location to search for.
        location_type: The type of location to filter by ('road' or 'intersection'). Default is None to search all types.
    """
    if location_type:
        _validate_location_type(location_type)
    env = _read_env()
    results: List[Dict[str, str]] = []
    for loc in _all_locations(env):
        if location_type and loc['type'] != location_type:
            continue
        if location_name and location_name.strip():
            query = location_name.strip().lower()
            tokens = [t for t in query.split() if t]
            name = (loc.get('name') or '').lower()
            if not all(token in name for token in tokens):
                continue
        results.append({
            'location_id': loc['id'],
            'location_type': loc['type'],
            'location_name': loc['name']
        })
    return {'locations': results}


def GetRoadDetails(road_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific road.

    Args:
        road_id: The unique identifier of the road.
    """
    if not road_id or not road_id.strip():
        raise InvalidRequestException('road_id is empty')
    env = _read_env()
    for road in env.get('roads', []):
        if road.get('road_id') == road_id or road.get('id') == road_id:
            details = {
                'road_id': road.get('road_id') or road.get('id'),
                'name': road.get('name') or road.get('road_name'),
                'type': 'road',
                'connected_roads': road.get('connected_roads', []),
                'connected_intersections': road.get('connected_intersections', [])
            }
            return {'road_details': details}
    raise NotFoundException('road_id does not exist')


def GetIntersectionDetails(intersection_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific intersection.

    Args:
        intersection_id: The unique identifier of the intersection.
    """
    if not intersection_id or not intersection_id.strip():
        raise InvalidRequestException('intersection_id is empty')
    env = _read_env()
    for inter in env.get('intersections', []):
        if inter.get('intersection_id') == intersection_id or inter.get('id') == intersection_id:
            details = {
                'intersection_id': inter.get('intersection_id') or inter.get('id'),
                'name': inter.get('name') or inter.get('intersection_name'),
                'type': 'intersection',
                'connected_roads': inter.get('connected_roads', []),
                'traffic_lights': inter.get('traffic_lights', []),
                'congestion_level': inter.get('congestion_level', 'medium')
            }
            return {'intersection_details': details}
    raise NotFoundException('intersection_id does not exist')


def SearchRoute(origin_id: str, destination_id: str, max_results: int = 1) -> Dict[str, Any]:
    """
    Search for routes between two locations.

    Args:
        origin_id: The unique identifier or name of the starting location.
        destination_id: The unique identifier or name of the destination location.
        max_results: The maximum number of routes to return. Default is 1.
    """
    if not origin_id or not destination_id:
        raise InvalidRequestException('origin_id and destination_id are required')
    if max_results is None:
        max_results = 1
    try:
        max_results = int(max_results)
        if max_results <= 0:
            raise ValueError()
    except Exception:
        raise InvalidRequestException('max_results must be a positive integer')

    env = _read_env()
    # allow origin/destination to be names; resolve to ids
    try:
        origin_id_res, _ = _resolve_location_id(env, origin_id)
    except Exception:
        origin_id_res = origin_id
    try:
        destination_id_res, _ = _resolve_location_id(env, destination_id)
    except Exception:
        destination_id_res = destination_id
    if not _get_location(env, origin_id_res)[1]:
        raise NotFoundException('origin_id does not exist')
    if not _get_location(env, destination_id_res)[1]:
        raise NotFoundException('destination_id does not exist')

    graph: Dict[str, List[str]] = {}
    for road in env.get('roads', []):
        rid = road.get('road_id') or road.get('id')
        graph[rid] = road.get('connected_intersections', [])
    for inter in env.get('intersections', []):
        iid = inter.get('intersection_id') or inter.get('id')
        graph[iid] = [r.get('road_id') or r.get('id') for r in inter.get('connected_roads', [])]

    routes: List[Dict[str, Any]] = []
    queue: List[Tuple[str, List[str]]] = [(origin_id_res, [origin_id_res])]
    while queue and len(routes) < max_results:
        current, path = queue.pop(0)
        if current == destination_id_res:
            formatted_route = []
            for node in path:
                loc, loc_type = _get_location(env, node)
                formatted_route.append({
                    'location_id': node,
                    'location_name': loc.get('name'),
                    'location_type': loc_type
                })
            estimated_minutes = max(2, (len(path) - 1) * 2)
            routes.append({
                'route': formatted_route,
                'estimated_time': _format_duration(estimated_minutes)
            })
            continue
        for neighbor in graph.get(current, []):
            if neighbor not in path:
                queue.append((neighbor, path + [neighbor]))

    if not routes:
        raise NotFoundException('No route found between origin and destination')
    return {'routes': routes}


def CheckTrafficLightsStates(intersection_id: str) -> Dict[str, Any]:
    """
    Check the current state of traffic lights at an intersection.

    Args:
        intersection_id: The unique identifier or name of the intersection.
    """
    if not intersection_id or not intersection_id.strip():
        raise InvalidRequestException('intersection_id is empty')
    env = _read_env()
    # accept name or id
    iid, typ = _resolve_location_id(env, intersection_id, expected_type='intersection')
    inter, loc_type = _get_location(env, iid)
    if loc_type != 'intersection':
        raise NotFoundException('intersection_id does not exist')
    return {'light_states': inter.get('traffic_lights', [])}


def ManageTrafficLightState(
    intersection_id: str,
    traffic_light_id: str,
    traffic_light_state: str,
    start_time: str = None,
    end_time: str = None
) -> Dict[str, Any]:
    """
    Manage the state of a traffic light at an intersection.

    Args:
        intersection_id: The unique identifier or name of the intersection.
        traffic_light_id: The unique identifier or name of the traffic light.
        traffic_light_state: The desired state of the traffic light.
        start_time: The start time of the traffic light state change. Default is now.
        end_time: The end time of the traffic light state change. Default is None.
    """
    if not intersection_id or not intersection_id.strip():
        raise InvalidRequestException('intersection_id is empty')
    if not traffic_light_id or not traffic_light_id.strip():
        raise InvalidRequestException('traffic_light_id is empty')
    if not traffic_light_state or not traffic_light_state.strip():
        raise InvalidRequestException('traffic_light_state is empty')

    # Treat 'None' string (from JSON tool calls) as no end time
    if start_time and str(start_time).strip().lower() == 'none':
        start_time = None
    if end_time and str(end_time).strip().lower() == 'none':
        end_time = None
    start_dt = _validate_datetime(start_time) if start_time else None
    end_dt = _validate_datetime(end_time) if end_time else None
    if start_dt and end_dt and start_dt >= end_dt:
        raise InvalidRequestException('start_time must be before end_time')

    env = _read_env()
    # resolve intersection id from name if needed
    iid, typ = _resolve_location_id(env, intersection_id, expected_type='intersection')
    intersection, loc_type = _get_location(env, iid)
    if loc_type != 'intersection':
        raise NotFoundException('intersection_id does not exist')

    lights = intersection.get('traffic_lights', [])
    target_light = None
    # Try exact match first
    for light in lights:
        if light.get('traffic_light_id') == traffic_light_id:
            target_light = light
            break
    # If no exact match, try case-insensitive substring
    if not target_light:
        query_lower = traffic_light_id.lower()
        for light in lights:
            light_id = light.get('traffic_light_id', '')
            if query_lower in light_id.lower():
                target_light = light
                break
    # If still no match, try token-based matching with abbreviation awareness
    if not target_light:
        abbrev_map = {'north': 'nb', 'south': 'sb', 'east': 'eb', 'west': 'wb',
                      'n': 'nb', 's': 'sb', 'e': 'eb', 'w': 'wb',
                      'nb': 'north', 'sb': 'south', 'eb': 'east', 'wb': 'west',
                      'northbound': 'nb', 'southbound': 'sb', 'eastbound': 'eb', 'westbound': 'wb'}
        common_prefixes = {'tl', 'tl_light', 'traffic_light', 'sl', 'pw', 'dl', 'rl'}
        def _expand_tokens(tokens):
            expanded = set()
            for t in tokens:
                tl = t.lower()
                expanded.add(tl)
                if tl in abbrev_map:
                    expanded.add(abbrev_map[tl])
            return expanded
        def _split_id(s):
            return [t for t in re.split(r'[-._\s]+', s) if t]
        query_tokens = _expand_tokens(_split_id(traffic_light_id))
        query_meaningful = query_tokens - common_prefixes
        for light in lights:
            light_tokens_str = light.get('traffic_light_id', '')
            light_tokens = _expand_tokens(_split_id(light_tokens_str))
            light_meaningful = light_tokens - common_prefixes
            # Require all meaningful query tokens to be present in the light's meaningful tokens
            if query_tokens & light_tokens and query_meaningful.issubset(light_tokens):
                target_light = light
                break
    if not target_light:
        raise NotFoundException('traffic_light_id does not exist at the intersection')

    tl_type = target_light.get('traffic_light_type')
    traffic_light_state = traffic_light_state.replace(' ', '_').replace('-', '_').lower()
    vehicle_states = {'red', 'green', 'yellow', 'yellow_flash', 'yellow_flashing', 'hazard', 'flashing_red', 'priority_green', 'amber_flashing', 'green_wave', 'normal'}
    pedestrian_states = {'walk', 'stop', 'flashing', 'flashing_red', 'yellow_flashing', 'normal'}
    if tl_type == 'vehicle' and traffic_light_state not in vehicle_states:
        raise InvalidRequestException('traffic_light_state is not valid for vehicle light')
    if tl_type == 'pedestrian' and traffic_light_state not in pedestrian_states:
        raise InvalidRequestException('traffic_light_state is not valid for pedestrian light')

    # if scheduled in the past, apply immediately (makes testing easier)
    if start_dt and start_dt > datetime.utcnow() and not end_dt:
        schedule = env.setdefault('scheduled_light_changes', [])
        schedule.append({
            'intersection_id': iid,
            'traffic_light_id': traffic_light_id,
            'traffic_light_state': traffic_light_state,
            'start_time': start_time,
            'end_time': end_time
        })
    elif start_dt and start_dt > datetime.utcnow() and end_dt:
        schedule = env.setdefault('scheduled_light_changes', [])
        schedule.append({
            'intersection_id': iid,
            'traffic_light_id': traffic_light_id,
            'traffic_light_state': traffic_light_state,
            'start_time': start_time,
            'end_time': end_time
        })
    else:
        # immediate effect (also covers start_time in past)
        target_light['traffic_light_state'] = traffic_light_state
    _write_env(env)
    return {'operation_success': True}


def MonitorTrafficCongestion(location_id: str) -> Dict[str, Any]:
    """
    Monitor the current level of traffic congestion at a location.

    Args:
        location_id: The unique identifier or name of the location.
    """
    if not location_id or not location_id.strip():
        raise InvalidRequestException('location_id is empty')
    env = _read_env()
    # accept name or id
    lid, typ = _resolve_location_id(env, location_id)
    loc, loc_type = _get_location(env, lid)
    if not loc_type:
        raise NotFoundException('location_id is not valid')
    level = loc.get('congestion_level', 'medium')
    return {'congestion_level': level}


def PredictTrafficCongestion(location_id: str, prediction_start_time: str, prediction_end_time: str) -> Dict[str, Any]:
    """
    Predict the level of traffic congestion at a location.

    Args:
        location_id: The unique identifier or name of the location.
        prediction_start_time: The start time of the prediction.
        prediction_end_time: The end time of the prediction.
    """
    if not location_id or not location_id.strip():
        raise InvalidRequestException('location_id is empty')
    start_dt = _validate_datetime(prediction_start_time)
    end_dt = _validate_datetime(prediction_end_time)
    if start_dt >= end_dt:
        raise InvalidRequestException('prediction_start_time must be before prediction_end_time')
    # For testing: if requested start time is in the past, treat prediction as immediate

    env = _read_env()
    lid, typ = _resolve_location_id(env, location_id)
    loc, loc_type = _get_location(env, lid)
    if not loc_type:
        raise NotFoundException('location_id does not exist')
    base = loc.get('congestion_level', 'medium')
    # use start_dt hour if available, otherwise use current hour
    hour = start_dt.hour if start_dt else datetime.utcnow().hour
    predicted = _predict_congestion(base, hour)
    return {'predicted_congestion_level': predicted}


def AnalyzeTrafficPatterns(location_id: str, start_time: str, end_time: str) -> Dict[str, Any]:
    """
    Analyze traffic patterns at a location.

    Args:
        location_id: The unique identifier or name of the location.
        start_time: The start time of the analysis.
        end_time: The end time of the analysis.
    """
    if not location_id or not location_id.strip():
        raise InvalidRequestException('location_id is empty')
    start_dt = _validate_datetime(start_time)
    end_dt = _validate_datetime(end_time)
    if start_dt >= end_dt:
        raise InvalidRequestException('start_time must be before end_time')

    env = _read_env()
    lid, typ = _resolve_location_id(env, location_id)
    loc, loc_type = _get_location(env, lid)
    if not loc_type:
        raise NotFoundException('location_id does not exist')
    profile = loc.get('pattern_profile') or {
        'average_congestion_level': loc.get('congestion_level', 'medium'),
        'peak_periods': [],
        'low_periods': []
    }
    result = {
        'average_congestion_level': profile.get('average_congestion_level', loc.get('congestion_level', 'medium')),
        'peak_periods': profile.get('peak_periods', []),
        'low_periods': profile.get('low_periods', [])
    }
    return {'analysis_result': result}


def GivePriorityToEmergencyVehicle(intersection_ids: List[str], start_time: str, end_time: str) -> Dict[str, Any]:
    """
    Give priority to emergency vehicles at specified intersections.

    Args:
        intersection_ids: The unique identifiers or names of the intersections.
        start_time: The start time of the priority.
        end_time: The end time of the priority.
    """
    if not intersection_ids:
        raise InvalidRequestException('intersection_ids is empty')
    start_dt = _validate_datetime(start_time)
    end_dt = _validate_datetime(end_time)
    if start_dt >= end_dt:
        raise InvalidRequestException('start_time must be before end_time')
    # Allow scheduling in the past for testing; if start_time already passed, apply immediately

    env = _read_env()
    resolved_ids: List[str] = []
    for iid in intersection_ids:
        rid, typ = _resolve_location_id(env, iid, expected_type='intersection')
        resolved_ids.append(rid)
        inter, loc_type = _get_location(env, rid)
        if loc_type != 'intersection':
            raise NotFoundException(f'intersection_id not found: {iid}')
        for light in inter.get('traffic_lights', []):
            if light.get('traffic_light_type') == 'vehicle':
                light['traffic_light_state'] = 'green'
            if light.get('traffic_light_type') == 'pedestrian':
                light['traffic_light_state'] = 'stop'
    overrides = env.setdefault('priority_overrides', [])
    overrides.append({
        'type': 'emergency',
        'intersection_ids': resolved_ids,
        'start_time': start_time,
        'end_time': end_time
    })
    _write_env(env)
    return {'operation_success': True}


def GivePriorityToPublicTransportation(intersection_ids: List[str], start_time: str, end_time: str) -> Dict[str, Any]:
    """
    Give priority to public transportation vehicles at specified intersections.

    Args:
        intersection_ids: The unique identifiers or names of the intersections.
        start_time: The start time of the priority.
        end_time: The end time of the priority.
    """
    if not intersection_ids:
        raise InvalidRequestException('intersection_ids is empty')
    start_dt = _validate_datetime(start_time)
    end_dt = _validate_datetime(end_time)
    if start_dt >= end_dt:
        raise InvalidRequestException('start_time must be before end_time')
    # Allow scheduling in the past for testing; if start_time already passed, apply immediately

    env = _read_env()
    resolved_ids: List[str] = []
    for iid in intersection_ids:
        rid, typ = _resolve_location_id(env, iid, expected_type='intersection')
        resolved_ids.append(rid)
        inter, loc_type = _get_location(env, rid)
        if loc_type != 'intersection':
            raise NotFoundException(f'intersection_id not found: {iid}')
        for light in inter.get('traffic_lights', []):
            if light.get('traffic_light_type') == 'vehicle':
                light['traffic_light_state'] = 'green'
            if light.get('traffic_light_type') == 'pedestrian':
                light['traffic_light_state'] = 'stop'
    overrides = env.setdefault('priority_overrides', [])
    overrides.append({
        'type': 'public_transport',
        'intersection_ids': resolved_ids,
        'start_time': start_time,
        'end_time': end_time
    })
    _write_env(env)
    return {'operation_success': True}


def ScheduleRoadMaintenance(location_id: str, start_time: str, end_time: str) -> Dict[str, Any]:
    """
    Schedule maintenance at a location.

    Args:
        location_id: The unique identifier or name of the location.
        start_time: The start time of the maintenance.
        end_time: The end time of the maintenance.
    """
    if not location_id or not location_id.strip():
        raise InvalidRequestException('location_id is empty')
    start_dt = _validate_datetime(start_time)
    end_dt = _validate_datetime(end_time)
    if start_dt >= end_dt:
        raise InvalidRequestException('start_time must be before end_time')
    # Allow scheduling in the past for testing; if start_time already passed, record it and treat as immediate maintenance

    env = _read_env()
    lid, typ = _resolve_location_id(env, location_id)
    loc, loc_type = _get_location(env, lid)
    if not loc_type:
        raise NotFoundException('location_id does not exist')
    schedule = env.setdefault('maintenance_schedule', [])
    schedule.append({
        'location_id': location_id if isinstance(location_id, str) and (location_id.startswith('road-') or location_id.startswith('int-')) else lid,
        'start_time': start_time,
        'end_time': end_time
    })
    _write_env(env)
    return {'operation_success': True}


__all__ = [
    'SearchLocations',
    'GetRoadDetails',
    'GetIntersectionDetails',
    'SearchRoute',
    'CheckTrafficLightsStates',
    'ManageTrafficLightState',
    'MonitorTrafficCongestion',
    'PredictTrafficCongestion',
    'AnalyzeTrafficPatterns',
    'GivePriorityToEmergencyVehicle',
    'GivePriorityToPublicTransportation',
    'ScheduleRoadMaintenance',
    'InvalidRequestException',
    'NotFoundException'
]
