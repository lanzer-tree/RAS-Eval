import json
import os
import shutil
import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

DATA_PATH = os.path.join('environment', 'reports', 'twilio.json')
INIT_PATH = os.path.join('environment', 'initial', 'twilio_init.json')

class InvalidRequestException(Exception):
    pass

class NotFoundException(Exception):
    pass

INIT = False
def _ensure_work_env():
    """Ensure working environment file exists by copying from init if necessary."""
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

def _write_env(data: Dict[str, Any]):
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _validate_phone(phone: str) -> bool:
    if not phone:
        return False
    digits = re.sub(r'[^\d]', '', phone)
    return len(digits) >= 6

def _normalize_phone(phone: str) -> str:
    digits = re.sub(r'[^\d]', '', phone)
    return '+' + digits

def _validate_dt(dt_str: str, fmt: str = '%Y-%m-%d %H:%M:%S') -> bool:
    try:
        datetime.strptime(dt_str, fmt)
        return True
    except Exception:
        return False

def _parse_dt(dt_str: str):
    return datetime.strptime(dt_str, '%Y-%m-%d %H:%M:%S')

def SendSms(to_phone_numbers: Union[str, List[str]], message: str, scheduled_time: Optional[str] = None, is_recurring: bool = False, recurrence: Optional[str] = None) -> Dict[str, Any]:
    """Send SMS message to one or more phone numbers.

    Args:
        to_phone_numbers (str or list): Phone number(s) to send SMS to, can be a single number string, comma-separated string, or list of strings
        message (str): The SMS message content to send
        scheduled_time (str, optional): When to send the SMS in YYYY-MM-DD HH:MM:SS format
        is_recurring (bool): Whether the SMS should be sent recurrently
        recurrence (str, optional): Recurrence pattern when is_recurring is True
    """
    # Handle to_phone_numbers as string or list
    if isinstance(to_phone_numbers, str):
        to_phone_numbers = [num.strip() for num in to_phone_numbers.split(',') if num.strip()]
    elif not isinstance(to_phone_numbers, list):
        raise InvalidRequestException('to_phone_numbers must be a string or list')
    if not to_phone_numbers:
        raise InvalidRequestException('to_phone_numbers is empty')
    for num in to_phone_numbers:
        if not _validate_phone(num):
            raise InvalidRequestException('phone number format invalid')
    to_phone_numbers = [_normalize_phone(num) for num in to_phone_numbers]
    if not message or not message.strip():
        raise InvalidRequestException('message is empty')
    if scheduled_time and not _validate_dt(scheduled_time):
        raise InvalidRequestException('scheduled_time must be YYYY-MM-DD HH:MM:SS')
    if is_recurring and (not recurrence or not recurrence.strip()):
        raise InvalidRequestException('recurrence required when is_recurring is true')

    env = _read_env()
    if scheduled_time:
        action_id = uuid.uuid4().hex
        action = {
            'action_id': action_id,
            'action_type': 'send_sms',
            'to_phone_numbers': to_phone_numbers,
            'message': message,
            'scheduled_time': scheduled_time,
            'is_recurring': bool(is_recurring),
            'recurrence': recurrence if is_recurring else None
        }
        env.setdefault('scheduled_actions', []).append(action)
    else:
        now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        for num in to_phone_numbers:
            env.setdefault('sent_sms', []).append({
                'to_phone_number': num,
                'message': message,
                'timestamp': now
            })
    _write_env(env)
    return {'success': True}

def GetSmsHistory(to_phone_number: Optional[str] = None, datetime_range: Optional[Union[str, List[str]]] = None, keywords: Optional[str] = None, max_results: int = 10) -> Dict[str, Any]:
    """Retrieve SMS sending history with optional filters.

    Args:
        to_phone_number (str, optional): Filter by recipient phone number
        datetime_range (str or list, optional): Time range filter as [start, end] in YYYY-MM-DD HH:MM:SS format or comma-separated string
        keywords (str, optional): Filter by keywords in message content, comma-separated for multiple keywords
        max_results (int): Maximum number of results to return
    """
    if to_phone_number and not _validate_phone(to_phone_number):
        raise InvalidRequestException('to_phone_number invalid')
    normalized_to = _normalize_phone(to_phone_number) if to_phone_number else None
    # Handle datetime_range as string or list
    if isinstance(datetime_range, str):
        datetime_range = [dt.strip() for dt in datetime_range.split(',') if dt.strip()]
    if datetime_range:
        if not isinstance(datetime_range, list) or len(datetime_range) != 2 or not all(_validate_dt(ts) for ts in datetime_range):
            raise InvalidRequestException('datetime_range must be [start, end] in YYYY-MM-DD HH:MM:SS or "start,end"')
        start_dt, end_dt = map(_parse_dt, datetime_range)
    else:
        start_dt = end_dt = None
    if max_results is None:
        max_results = 10
    try:
        max_results = int(max_results)
        if max_results <= 0:
            raise ValueError()
    except Exception:
        raise InvalidRequestException('max_results must be positive integer')

    env = _read_env()
    records = env.get('sent_sms', [])
    results = []
    kw_list = [k.strip().lower() for k in (keywords or '').split(',') if k.strip()]
    for r in records:
        if to_phone_number and r.get('to_phone_number') != normalized_to:
            continue
        if datetime_range:
            ts = _parse_dt(r.get('timestamp'))
            if ts < start_dt or ts > end_dt:
                continue
        if kw_list:
            text = (r.get('message') or '').lower()
            if not any(k in text for k in kw_list):
                continue
        results.append(r)
        if len(results) >= max_results:
            break
    return {'sms_history': results}

def GetReceivedSmsMessages(from_phone_number: Optional[str] = None, datetime_range: Optional[Union[str, List[str]]] = None, keywords: Optional[str] = None, max_results: int = 10) -> Dict[str, Any]:
    """Retrieve received SMS messages with optional filters.

    Args:
        from_phone_number (str, optional): Filter by sender phone number
        datetime_range (str or list, optional): Time range filter as [start, end] in YYYY-MM-DD HH:MM:SS format or comma-separated string
        keywords (str, optional): Filter by keywords in message content, comma-separated for multiple keywords
        max_results (int): Maximum number of results to return
    """
    if from_phone_number and not _validate_phone(from_phone_number):
        raise InvalidRequestException('from_phone_number invalid')
    normalized_from = _normalize_phone(from_phone_number) if from_phone_number else None
    # Handle datetime_range as string or list
    if isinstance(datetime_range, str):
        datetime_range = [dt.strip() for dt in datetime_range.split(',') if dt.strip()]
    if datetime_range:
        if not isinstance(datetime_range, list) or len(datetime_range) != 2 or not all(_validate_dt(ts) for ts in datetime_range):
            raise InvalidRequestException('datetime_range must be [start, end] in YYYY-MM-DD HH:MM:SS or "start,end"')
        start_dt, end_dt = map(_parse_dt, datetime_range)
    else:
        start_dt = end_dt = None
    if max_results is None:
        max_results = 10
    try:
        max_results = int(max_results)
        if max_results <= 0:
            raise ValueError()
    except Exception:
        raise InvalidRequestException('max_results must be positive integer')

    env = _read_env()
    records = env.get('received_sms', [])
    results = []
    kw_list = [k.strip().lower() for k in (keywords or '').split(',') if k.strip()]
    for r in records:
        if from_phone_number and r.get('from_phone_number') != normalized_from:
            continue
        if datetime_range:
            ts = _parse_dt(r.get('timestamp'))
            if ts < start_dt or ts > end_dt:
                continue
        if kw_list:
            text = (r.get('message') or '').lower()
            if not any(k in text for k in kw_list):
                continue
        results.append(r)
        if len(results) >= max_results:
            break
    return {'received_messages': results}

def GetSmsPricing(country_code: int) -> Dict[str, Any]:
    """Get SMS pricing information for a specific country.

    Args:
        country_code (int): The numeric country code to query pricing for
    """
    try:
        cc = int(country_code)
    except Exception:
        raise InvalidRequestException('country_code must be integer')
    env = _read_env()
    pricing = env.get('pricing', [])
    entry = next((p for p in pricing if p.get('country_code') == cc), None)
    if not entry:
        raise InvalidRequestException('country_code not found')
    return {'pricing': entry}

def GetPhoneNumberInfo(phone_number: str) -> Dict[str, Any]:
    """Get detailed information about a specific phone number.

    Args:
        phone_number (str): The phone number to query information for
    """
    if not _validate_phone(phone_number):
        raise InvalidRequestException('phone_number invalid')
    normalized = _normalize_phone(phone_number)
    env = _read_env()
    entry = next((p for p in env.get('phone_numbers', []) if p.get('phone_number') == normalized), None)
    if not entry:
        raise NotFoundException('phone_number not found')
    return {'phone_number_info': entry}

def GetScheduledActions(max_results: int = 10) -> Dict[str, Any]:
    """Retrieve a list of scheduled SMS actions.

    Args:
        max_results (int): Maximum number of scheduled actions to return
    """
    if max_results is None:
        max_results = 10
    try:
        max_results = int(max_results)
        if max_results <= 0:
            raise ValueError()
    except Exception:
        raise InvalidRequestException('max_results must be positive integer')
    env = _read_env()
    actions = env.get('scheduled_actions', [])[:max_results]
    return {'scheduled_actions': actions}

def CancelScheduledAction(action_id: str) -> Dict[str, Any]:
    """Cancel a scheduled SMS action by its action ID.

    Args:
        action_id (str): The unique identifier of the scheduled action to cancel
    """
    env = _read_env()
    actions = env.get('scheduled_actions', [])
    action = next((a for a in actions if a.get('action_id') == action_id), None)
    if not action:
        raise NotFoundException('action_id not found')
    env['scheduled_actions'] = [a for a in actions if a.get('action_id') != action_id]
    _write_env(env)
    return {'success': True}

__all__ = [
    'SendSms', 'GetSmsHistory', 'GetReceivedSmsMessages', 'GetSmsPricing', 'GetPhoneNumberInfo',
    'GetScheduledActions', 'CancelScheduledAction', 'InvalidRequestException', 'NotFoundException'
]