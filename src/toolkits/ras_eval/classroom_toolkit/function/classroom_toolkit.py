import datetime
import json
import os
import re
import shutil
from typing import Any, Dict, List, Optional

INIT_PATH = 'environment/initial/ClassroomManagement_init.json'
DATA_PATH = 'environment/reports/ClassroomManagement.json'
INIT = False

SUPPORTED_BORROW_TYPES = {'date_period', 'day', 'week'}

NAMED_PERIODS = {
    'morning': ('08:00', '12:00'),
    'afternoon': ('13:00', '17:00'),
    'evening': ('17:00', '21:00'),
}


class InvalidRequestException(Exception):
    pass


class ClassroomOccupiedException(Exception):
    pass


class InvalidBorrowTypeException(Exception):
    pass


class EmailSendFailedException(Exception):
    pass


class RepairAlreadyReportedException(Exception):
    pass


def _normalize_text(value: str) -> str:
    """Normalize an identifier for case-insensitive, symbol-free matching."""
    return re.sub(r"[^0-9a-z]", "", value.lower())


def _ensure_work_env() -> None:
    """Ensure working environment files exist by copying from the init data."""
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
    with open(DATA_PATH, 'r') as file:
        return json.load(file)


def _save_data(data: Dict[str, Any]) -> None:
    with open(DATA_PATH, 'w') as file:
        json.dump(data, file, indent=4)


def _find_classroom(
    data: Dict[str, Any],
    classroom_id: Optional[str] = None,
    classroom_name: Optional[str] = None
) -> Dict[str, Any]:
    classrooms = data.get('classrooms', [])
    normalized_id = _normalize_text(classroom_id) if classroom_id else ''
    normalized_name = _normalize_text(classroom_name) if classroom_name else ''
    for classroom in classrooms:
        classroom_id_value = classroom.get('id', '')
        classroom_name_value = classroom.get('name', '')
        classroom_combo = f"{classroom_name_value} ({classroom_id_value})"
        if normalized_id and _normalize_text(classroom_id_value) == normalized_id:
            return classroom
        if normalized_name:
            if _normalize_text(classroom_name_value).startswith(normalized_name):
                return classroom
            if normalized_name in _normalize_text(classroom_combo):
                return classroom
            classroom_location = _normalize_text(classroom.get('location', ''))
            if normalized_name in _normalize_text(f"{classroom_location} {classroom_name_value}"):
                return classroom
            match = re.match(r'^([a-z])(\d+)$', normalized_name)
            if match:
                building_letter = match.group(1)
                room_number = match.group(2)
                if building_letter in classroom_location and room_number in _normalize_text(classroom_name_value):
                    return classroom
    raise InvalidRequestException('Please provide a valid classroom ID or name.')


def _parse_period(period: str) -> tuple[datetime.time, datetime.time]:
    if period.lower() in NAMED_PERIODS:
        start, end = NAMED_PERIODS[period.lower()]
        return (
            datetime.datetime.strptime(start, '%H:%M').time(),
            datetime.datetime.strptime(end, '%H:%M').time()
        )
    start, end = period.split('-')
    return (
        datetime.datetime.strptime(start.strip(), '%H:%M').time(),
        datetime.datetime.strptime(end.strip(), '%H:%M').time()
    )


def _periods_overlap(period_a: str, period_b: str) -> bool:
    start_a, end_a = _parse_period(period_a)
    start_b, end_b = _parse_period(period_b)
    return not (end_a <= start_b or end_b <= start_a)


def _has_conflict(date: str, period: str, entries: List[Dict[str, Any]]) -> bool:
    for entry in entries:
        if entry.get('date') != date:
            continue
        if _periods_overlap(period, entry.get('period', '00:00-23:59')):
            return True
    return False


def _has_current_reservation(classroom: Dict[str, Any]) -> bool:
    now = datetime.datetime.now()
    today = now.strftime('%Y-%m-%d')
    current_time = now.time()
    for entry in classroom.get('schedule', []) + classroom.get('bookings', []):
        if entry.get('date') != today:
            continue
        start, end = _parse_period(entry.get('period'))
        if start <= current_time <= end:
            return True
    return False


def QueryClassroom(
    classroom_id: Optional[str] = None,
    classroom_name: Optional[str] = None
) -> Dict[str, Any]:
    """Return metadata for a specific classroom.

    Args:
        classroom_id (Optional[str]): The ID of the classroom to query.
        classroom_name (Optional[str]): The name of the classroom to query.
    """
    data = _load_data()
    classroom = _find_classroom(data, classroom_id, classroom_name)
    occupied = classroom.get('status', 'available') != 'available' or _has_current_reservation(classroom)
    return {
        'location': classroom.get('location'),
        'size': classroom.get('size'),
        'seats': classroom.get('seats'),
        'equipment': classroom.get('equipment', 'Not specified'),
        'occupied': occupied,
        'available_times': classroom.get('available_times', [])
    }


def BorrowClassroom(
    classroom_id: Optional[str] = None,
    classroom_name: Optional[str] = None,
    borrow_type: str = '',
    borrow_details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Reserve a classroom after checking its current status.

    Args:
        classroom_id (Optional[str]): The ID of the classroom to reserve.
        classroom_name (Optional[str]): The name of the classroom to reserve.
        borrow_type (str): The type of borrowing, must be 'date_period', 'day', or 'week'.
        borrow_details (Optional[Dict[str, Any]]): Details about the borrowing request including date, period, purpose, etc.
    """
    if not borrow_details:
        raise InvalidRequestException('borrow_details must be provided.')
    normalized_type = borrow_type.lower()
    if normalized_type not in SUPPORTED_BORROW_TYPES:
        if borrow_details.get('period') or (borrow_details.get('start_time') and borrow_details.get('end_time')):
            normalized_type = 'date_period'
        elif borrow_details.get('day'):
            normalized_type = 'day'
        elif borrow_details.get('week_start'):
            normalized_type = 'week'
        else:
            raise InvalidBorrowTypeException('Unsupported borrow type.')
    data = _load_data()
    classroom = _find_classroom(data, classroom_id, classroom_name)
    if classroom.get('status') == 'maintenance':
        raise ClassroomOccupiedException('Classroom is under maintenance and cannot be borrowed.')
    week_range: Optional[str] = None
    borrow_type = normalized_type
    if borrow_type == 'date_period':
        date = borrow_details.get('date')
        period = borrow_details.get('period')
        if not period:
            start_time = borrow_details.get('start_time')
            end_time = borrow_details.get('end_time')
            if start_time and end_time:
                period = f"{start_time}-{end_time}"
        if not date or not period:
            raise InvalidRequestException('date and period are required for date_period borrowings.')
        if _has_conflict(date, period, classroom.get('schedule', []) + classroom.get('bookings', [])):
            raise ClassroomOccupiedException('The requested time slot is already occupied.')
        record_period = period
    elif borrow_type == 'day':
        day = borrow_details.get('day')
        if not day:
            raise InvalidRequestException('day is required for day borrowings.')
        record_period = '08:00-20:00'
        if _has_conflict(day, record_period, classroom.get('schedule', []) + classroom.get('bookings', [])):
            raise ClassroomOccupiedException('The classroom has an existing event on that day.')
        date = day
    else:  # week
        week_start = borrow_details.get('week_start')
        week_end = borrow_details.get('week_end')
        if not week_start or not week_end:
            raise InvalidRequestException('week_start and week_end are required for week borrowings.')
        if _has_conflict(week_start, '00:00-23:59', classroom.get('schedule', []) + classroom.get('bookings', [])):
            raise ClassroomOccupiedException('The classroom has a conflict at the start of the week.')
        date = week_start
        record_period = '00:00-23:59'
        week_range = f'{week_start} to {week_end}'
    booking = {
        'date': date,
        'period': record_period,
        'borrow_type': borrow_type,
        'purpose': borrow_details.get('purpose', 'Reserved by agent'),
        'reserved_by': borrow_details.get('reserved_by', 'ClassroomAgent'),
        'added_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    if week_range:
        booking['week_range'] = week_range
    classroom.setdefault('bookings', []).append(booking)
    classroom['status'] = 'occupied'
    _save_data(data)
    return {
        'success': True,
        'message': f"{classroom.get('name')} reserved for {booking['purpose']} on {booking['date']}."
    }


def GetClassroomSchedule(
    classroom_id: Optional[str] = None,
    classroom_name: Optional[str] = None
) -> Dict[str, Any]:
    """Return the course schedule for a given classroom.

    Args:
        classroom_id (Optional[str]): The ID of the classroom to query.
        classroom_name (Optional[str]): The name of the classroom to query.
    """
    data = _load_data()
    classroom = _find_classroom(data, classroom_id, classroom_name)
    return {
        'schedule': classroom.get('schedule', [])
    }


def CheckSelfStudyClassroom(
    classroom_id: Optional[str] = None,
    classroom_name: Optional[str] = None
) -> Dict[str, Any]:
    """Determine if the classroom is available for self-study right now.

    Args:
        classroom_id (Optional[str]): The ID of the classroom to check.
        classroom_name (Optional[str]): The name of the classroom to check.
    """
    classroom = _find_classroom(_load_data(), classroom_id, classroom_name)
    is_available_now = classroom.get('status', 'available') == 'available' and not _has_current_reservation(classroom)
    return {
        'is_self_study': is_available_now
    }


def _send_repair_email(classroom_name: str, repair_info: str) -> bool:
    email_body = (
        f"Repair request for {classroom_name}: {repair_info}"
    )
    return True


def ReportClassroomRepair(
    classroom_id: Optional[str] = None,
    classroom_name: Optional[str] = None,
    repair_info: str = ''
) -> Dict[str, Any]:
    """Log a repair request and notify the maintenance team.

    Args:
        classroom_id (Optional[str]): The ID of the classroom needing repair.
        classroom_name (Optional[str]): The name of the classroom needing repair.
        repair_info (str): Description of the repair issue.
    """
    if not repair_info.strip():
        raise InvalidRequestException('repair_info is required.')
    data = _load_data()
    classroom = _find_classroom(data, classroom_id, classroom_name)
    if classroom.get('status') == 'maintenance':
        raise RepairAlreadyReportedException('A repair is already in progress.')
    repair_entry = {
        'reported_at': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'details': repair_info
    }
    classroom.setdefault('repairs', []).append(repair_entry)
    classroom['status'] = 'maintenance'
    email_sent = _send_repair_email(classroom.get('name', ''), repair_info)
    if not email_sent:
        raise EmailSendFailedException('Unable to send repair notification email.')
    _save_data(data)
    return {
        'success': True,
        'email_sent': email_sent
    }