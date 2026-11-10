import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional
import uuid

DATA_PATH = 'environment/reports/MeetMin.json'
INIT_PATH = 'environment/initial/MeetMin_init.json'

INIT = False


class InvalidRequestException(Exception):
    """Exception raised for invalid request parameters."""
    pass


class NotFoundException(Exception):
    """Exception raised when a resource is not found."""
    pass


def _ensure_dir(path: str):
    """Ensure directory exists."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


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


def _load_data() -> Dict[str, Any]:
    """Load data from the working environment file."""
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_data(data: Dict[str, Any]):
    """Save data to the working environment file."""
    _ensure_dir(os.path.dirname(DATA_PATH))
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _generate_id(prefix: str) -> str:
    """Generate a unique ID with the given prefix."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _get_meeting(data: Dict[str, Any], meeting_id: str) -> Dict[str, Any]:
    """Get a meeting by ID."""
    meeting = next((m for m in data.get('meetings', []) if m.get('meeting_id') == meeting_id), None)
    if not meeting:
        raise NotFoundException(f'Meeting not found: {meeting_id}')
    return meeting


def _get_minutes(data: Dict[str, Any], minutes_id: str) -> Dict[str, Any]:
    """Get meeting minutes by ID."""
    minutes = next((m for m in data.get('minutes', []) if m.get('minutes_id') == minutes_id), None)
    if not minutes:
        raise NotFoundException(f'Meeting minutes not found: {minutes_id}')
    return minutes


def _get_task(data: Dict[str, Any], task_id: str) -> Dict[str, Any]:
    """Get a task by ID."""
    task = next((t for t in data.get('tasks', []) if t.get('task_id') == task_id), None)
    if not task:
        raise NotFoundException(f'Task not found: {task_id}')
    return task


def _validate_participant(participant: Dict[str, Any]) -> bool:
    """Validate participant data structure."""
    required_fields = ['id', 'name', 'role']
    return all(field in participant for field in required_fields)


def _get_current_time() -> str:
    """Get current time in ISO format."""
    return datetime.utcnow().isoformat() + 'Z'


def init_meeting(meeting_id: str, title: str, start_time: str, participants: List[Dict[str, str]], 
                 end_time: str = None, meeting_type: str = "offline", 
                 meeting_link: str = None, host_id: str = None) -> Dict[str, Any]:
    """
    Initialize a meeting with basic information.

    Args:
        meeting_id (str): The unique identifier for the meeting.
        title (str): The title of the meeting.
        start_time (str): The start time of the meeting in format 'YYYY-MM-DD HH:MM:SS'.
        participants (List[Dict[str, str]]): List of participants, each with 'id', 'name', and 'role'.
        end_time (str, optional): The expected end time of the meeting in format 'YYYY-MM-DD HH:MM:SS'.
        meeting_type (str, optional): Type of meeting, either 'online' or 'offline'. Default is 'offline'.
        meeting_link (str, optional): The link for online meetings (e.g., Zoom, Tencent Meeting).
        host_id (str, optional): The ID of the meeting host.

    Returns:
        dict: A dictionary containing operation result and meeting basic information receipt.
    """
    if not meeting_id or not meeting_id.strip():
        raise InvalidRequestException("The 'meeting_id' parameter cannot be empty.")
    if not title or not title.strip():
        raise InvalidRequestException("The 'title' parameter cannot be empty.")
    if not start_time or not start_time.strip():
        raise InvalidRequestException("The 'start_time' parameter cannot be empty.")
    if not participants or len(participants) == 0:
        raise InvalidRequestException("The 'participants' parameter cannot be empty.")
    
    if meeting_type is None:
        meeting_type = "offline"
    
    # Validate participants
    for p in participants:
        if not _validate_participant(p):
            raise InvalidRequestException("Each participant must have 'id', 'name', and 'role' fields.")
    
    if meeting_type not in ['online', 'offline']:
        raise InvalidRequestException("The 'meeting_type' must be either 'online' or 'offline'.")
    
    if meeting_type == 'online' and not meeting_link:
        raise InvalidRequestException("The 'meeting_link' is required for online meetings.")
    
    data = _load_data()
    
    # Check if meeting_id already exists
    existing = next((m for m in data.get('meetings', []) if m.get('meeting_id') == meeting_id), None)
    if existing:
        raise InvalidRequestException(f"Meeting with ID '{meeting_id}' already exists.")
    
    meeting = {
        'meeting_id': meeting_id,
        'title': title.strip(),
        'start_time': start_time,
        'end_time': end_time,
        'meeting_type': meeting_type,
        'meeting_link': meeting_link,
        'host_id': host_id,
        'participants': participants,
        'status': 'initialized',
        'created_at': _get_current_time()
    }
    
    data.setdefault('meetings', []).append(meeting)
    _save_data(data)
    
    return {
        'success': True,
        'message': f"Meeting '{title}' initialized successfully.",
        'meeting': meeting
    }


def record_meeting_content(meeting_id: str, content_type: str, content: str,
                           speaker_id: str = None, record_time: str = None,
                           tags: List[str] = None) -> Dict[str, Any]:
    """
    Record meeting content in real-time.

    Args:
        meeting_id (str): The unique identifier of the meeting.
        content_type (str): Type of content: 'speech_to_text', 'text_record', or 'key_point'.
        content (str): The content to record.
        speaker_id (str, optional): The ID of the speaker.
        record_time (str, optional): The time of recording in format 'YYYY-MM-DD HH:MM:SS'. Default is current time.
        tags (List[str], optional): Content tags such as 'decision', 'todo', 'discussion'.

    Returns:
        dict: A dictionary containing operation result and record ID.
    """
    if not meeting_id or not meeting_id.strip():
        raise InvalidRequestException("The 'meeting_id' parameter cannot be empty.")
    if not content_type or content_type not in ['speech_to_text', 'text_record', 'key_point']:
        raise InvalidRequestException("The 'content_type' must be 'speech_to_text', 'text_record', or 'key_point'.")
    if not content or not content.strip():
        raise InvalidRequestException("The 'content' parameter cannot be empty.")
    
    valid_tags = ['decision', 'todo', 'discussion', 'conclusion', 'action_item', 'controversy', 'follow-up', 'action-items', 'key_point']
    
    data = _load_data()
    _get_meeting(data, meeting_id)  # Validate meeting exists
    
    record_id = _generate_id('record')
    record = {
        'record_id': record_id,
        'meeting_id': meeting_id,
        'content_type': content_type,
        'content': content.strip(),
        'speaker_id': speaker_id,
        'record_time': record_time or _get_current_time(),
        'tags': tags or [],
        'created_at': _get_current_time()
    }
    
    data.setdefault('records', []).append(record)
    _save_data(data)
    
    return {
        'success': True,
        'message': 'Meeting content recorded successfully.',
        'record_id': record_id
    }


def extract_key_points(meeting_id: str, extract_types: List[str] = None,
                       content_ids: List[str] = None) -> Dict[str, Any]:
    """
    Extract key information from meeting records.

    Args:
        meeting_id (str): The unique identifier of the meeting.
        extract_types (List[str], optional): Types to extract: 'decision', 'todo', 'controversy', 'conclusion'. Default is all.
        content_ids (List[str], optional): Specific record IDs to extract from. Default is all records.

    Returns:
        dict: A dictionary containing structured key information list with type, content, time, and speaker.
    """
    if not meeting_id or not meeting_id.strip():
        raise InvalidRequestException("The 'meeting_id' parameter cannot be empty.")
    
    valid_types = ['decision', 'todo', 'controversy', 'conclusion']
    if extract_types:
        for t in extract_types:
            if t not in valid_types:
                raise InvalidRequestException(f"Invalid extract type '{t}'. Valid types are: {valid_types}")
    else:
        extract_types = valid_types
    
    data = _load_data()
    _get_meeting(data, meeting_id)  # Validate meeting exists
    
    # Filter records
    records = [r for r in data.get('records', []) if r.get('meeting_id') == meeting_id]
    if content_ids:
        records = [r for r in records if r.get('record_id') in content_ids]
    
    key_points = []
    for record in records:
        record_tags = record.get('tags', [])
        for extract_type in extract_types:
            if extract_type in record_tags or record.get('content_type') == 'key_point':
                key_points.append({
                    'type': extract_type if extract_type in record_tags else 'key_point',
                    'content': record.get('content'),
                    'time': record.get('record_time'),
                    'speaker_id': record.get('speaker_id'),
                    'record_id': record.get('record_id')
                })
                break
    
    return {
        'success': True,
        'meeting_id': meeting_id,
        'key_points': key_points,
        'total_count': len(key_points)
    }


def generate_meeting_minutes(meeting_id: str, template_type: str = "general",
                             include_items: List[str] = None,
                             language: str = "zh") -> Dict[str, Any]:
    """
    Generate standardized meeting minutes.

    Args:
        meeting_id (str): The unique identifier of the meeting.
        template_type (str): Template type: 'general', 'project_meeting', or 'business_meeting'. Default is 'general'.
        include_items (List[str], optional): Items to include: 'key_points', 'task_list', 'participants'. Default is all.
        language (str, optional): Language for the minutes, e.g., 'zh' for Chinese, 'en' for English. Default is 'zh'.

    Returns:
        dict: A dictionary containing standardized meeting minutes document and minutes ID.
    """
    if not meeting_id or not meeting_id.strip():
        raise InvalidRequestException("The 'meeting_id' parameter cannot be empty.")
    
    valid_templates = ['general', 'project_meeting', 'business_meeting']
    if template_type not in valid_templates:
        raise InvalidRequestException(f"Invalid template type. Valid types are: {valid_templates}")
    
    valid_items = ['key_points', 'task_list', 'participants', 'decisions', 'action_items']
    include_items = include_items or ['key_points', 'task_list', 'participants']
    for item in include_items:
        if item not in valid_items:
            raise InvalidRequestException(f"Invalid include item '{item}'. Valid items are: {valid_items}")
    
    if not language:
        language = 'zh'
    if language not in ['zh', 'en']:
        raise InvalidRequestException("Language must be 'zh' or 'en'.")
    
    data = _load_data()
    meeting = _get_meeting(data, meeting_id)
    
    # Get related records and tasks
    records = [r for r in data.get('records', []) if r.get('meeting_id') == meeting_id]
    tasks = [t for t in data.get('tasks', []) if t.get('meeting_id') == meeting_id]
    
    minutes_id = _generate_id('minutes')
    
    # Build minutes content
    minutes_content = {
        'basic_info': {
            'title': meeting.get('title'),
            'start_time': meeting.get('start_time'),
            'end_time': meeting.get('end_time'),
            'meeting_type': meeting.get('meeting_type'),
            'host_id': meeting.get('host_id')
        }
    }
    
    if 'participants' in include_items:
        minutes_content['participants'] = meeting.get('participants', [])
    
    if 'key_points' in include_items:
        minutes_content['key_points'] = [
            {'content': r.get('content'), 'speaker_id': r.get('speaker_id'), 'tags': r.get('tags')}
            for r in records if r.get('content_type') == 'key_point' or r.get('tags')
        ]
    
    if 'task_list' in include_items:
        minutes_content['task_list'] = [
            {'description': t.get('description'), 'assignee_id': t.get('assignee_id'), 
             'deadline': t.get('deadline'), 'priority': t.get('priority')}
            for t in tasks
        ]
    
    minutes = {
        'minutes_id': minutes_id,
        'meeting_id': meeting_id,
        'template_type': template_type,
        'language': language,
        'content': minutes_content,
        'status': 'draft',
        'created_at': _get_current_time(),
        'version': 1,
        'history': []
    }
    
    data.setdefault('minutes', []).append(minutes)
    _save_data(data)
    
    return {
        'success': True,
        'message': 'Meeting minutes generated successfully.',
        'minutes_id': minutes_id,
        'minutes': minutes
    }


def assign_meeting_tasks(meeting_id: str, tasks: List[Dict[str, Any]],
                         task_source: str = None) -> Dict[str, Any]:
    """
    Assign meeting todo tasks.

    Args:
        meeting_id (str): The unique identifier of the meeting.
        tasks (List[Dict[str, Any]]): List of tasks, each with 'description', 'assignee_id', 'deadline', and 'priority'.
        task_source (str, optional): Source record ID of the task.

    Returns:
        dict: A dictionary containing operation result and task list with task IDs.
    """
    if not meeting_id or not meeting_id.strip():
        raise InvalidRequestException("The 'meeting_id' parameter cannot be empty.")
    if not tasks or len(tasks) == 0:
        raise InvalidRequestException("The 'tasks' parameter cannot be empty.")
    if not isinstance(tasks, list) or not all(isinstance(task, dict) for task in tasks):
        raise InvalidRequestException("The 'tasks' parameter must be a list of task objects.")
    
    valid_priorities = ['high', 'medium', 'low']
    
    data = _load_data()
    meeting = _get_meeting(data, meeting_id)
    participant_ids = [p.get('id') for p in meeting.get('participants', [])]
    
    created_tasks = []
    for task in tasks:
        if not task.get('description'):
            raise InvalidRequestException("Each task must have a 'description'.")
        if not task.get('assignee_id'):
            raise InvalidRequestException("Each task must have an 'assignee_id'.")
        if task.get('assignee_id') not in participant_ids:
            raise InvalidRequestException(f"Assignee '{task.get('assignee_id')}' is not a meeting participant.")
        if task.get('priority') and task.get('priority') not in valid_priorities:
            raise InvalidRequestException(f"Invalid priority. Valid priorities are: {valid_priorities}")
        
        task_id = _generate_id('task')
        new_task = {
            'task_id': task_id,
            'meeting_id': meeting_id,
            'description': task.get('description'),
            'assignee_id': task.get('assignee_id'),
            'deadline': task.get('deadline'),
            'priority': task.get('priority', 'medium'),
            'status': 'not_started',
            'source_record_id': task_source,
            'created_at': _get_current_time()
        }
        data.setdefault('tasks', []).append(new_task)
        created_tasks.append(new_task)
    
    _save_data(data)
    
    return {
        'success': True,
        'message': f'{len(created_tasks)} task(s) assigned successfully.',
        'tasks': created_tasks
    }


def track_task_progress(meeting_id: str, task_id: str = None,
                        progress_status: str = None) -> Dict[str, Any]:
    """
    Track todo task progress.

    Args:
        meeting_id (str): The unique identifier of the meeting.
        task_id (str, optional): The specific task ID to query.
        progress_status (str, optional): Filter by status: 'not_started', 'in_progress', or 'completed'.

    Returns:
        dict: A dictionary containing task progress list with task ID, description, assignee, progress, and deadline.
    """
    if not meeting_id or not meeting_id.strip():
        raise InvalidRequestException("The 'meeting_id' parameter cannot be empty.")
    
    valid_statuses = ['not_started', 'in_progress', 'completed']
    if progress_status and progress_status not in valid_statuses:
        raise InvalidRequestException(f"Invalid status. Valid statuses are: {valid_statuses}")
    
    data = _load_data()
    _get_meeting(data, meeting_id)  # Validate meeting exists
    
    tasks = [t for t in data.get('tasks', []) if t.get('meeting_id') == meeting_id]
    
    if task_id:
        tasks = [t for t in tasks if t.get('task_id') == task_id]
    
    if progress_status:
        tasks = [t for t in tasks if t.get('status') == progress_status]
    
    progress_list = [
        {
            'task_id': t.get('task_id'),
            'description': t.get('description'),
            'assignee_id': t.get('assignee_id'),
            'status': t.get('status'),
            'priority': t.get('priority'),
            'deadline': t.get('deadline')
        }
        for t in tasks
    ]
    
    return {
        'success': True,
        'meeting_id': meeting_id,
        'tasks': progress_list,
        'total_count': len(progress_list)
    }


def update_meeting_minutes(minutes_id: str, update_data: Dict[str, Any],
                           update_reason: str = None,
                           operator_id: str = None) -> Dict[str, Any]:
    """
    Update meeting minutes.

    Args:
        minutes_id (str): The unique identifier of the meeting minutes.
        update_data (Dict[str, Any]): Update content including supplementary points, task corrections, or conclusion modifications.
        update_reason (str, optional): Reason for the update.
        operator_id (str, optional): ID of the person making the update.

    Returns:
        dict: A dictionary containing operation result and updated minutes fragment.
    """
    if not minutes_id or not minutes_id.strip():
        raise InvalidRequestException("The 'minutes_id' parameter cannot be empty.")
    if not update_data:
        raise InvalidRequestException("The 'update_data' parameter cannot be empty.")
    
    data = _load_data()
    minutes = _get_minutes(data, minutes_id)
    
    if minutes.get('status') == 'archived':
        raise InvalidRequestException("Cannot update archived minutes.")
    
    # Save current version to history
    history_entry = {
        'version': minutes.get('version'),
        'content': minutes.get('content').copy(),
        'updated_at': minutes.get('updated_at', minutes.get('created_at')),
        'reason': update_reason,
        'operator_id': operator_id
    }
    minutes.setdefault('history', []).append(history_entry)
    
    # Apply updates
    content = minutes.get('content', {})
    for key, value in update_data.items():
        if key in content:
            if isinstance(content[key], list) and isinstance(value, list):
                content[key].extend(value)
            elif isinstance(content[key], dict) and isinstance(value, dict):
                content[key].update(value)
            else:
                content[key] = value
        else:
            content[key] = value
    
    minutes['content'] = content
    minutes['version'] = minutes.get('version', 1) + 1
    minutes['updated_at'] = _get_current_time()
    minutes['last_update_reason'] = update_reason
    minutes['last_operator_id'] = operator_id
    
    _save_data(data)
    
    return {
        'success': True,
        'message': 'Meeting minutes updated successfully.',
        'minutes_id': minutes_id,
        'new_version': minutes['version'],
        'updated_content': content
    }


def distribute_meeting_minutes(minutes_id: str, recipient_ids: List[str],
                               distribute_method: str,
                               attachments: List[str] = None) -> Dict[str, Any]:
    """
    Distribute meeting minutes to recipients.

    Args:
        minutes_id (str): The unique identifier of the meeting minutes.
        recipient_ids (List[str]): List of recipient IDs.
        distribute_method (str): Distribution method: 'email', 'wechat_work', or 'link_share'.
        attachments (List[str], optional): Attachments such as 'original_record' or 'task_list'.

    Returns:
        dict: A dictionary containing distribution result (success/failure counts) and distribution log.
    """
    if not minutes_id or not minutes_id.strip():
        raise InvalidRequestException("The 'minutes_id' parameter cannot be empty.")
    if not recipient_ids or len(recipient_ids) == 0:
        raise InvalidRequestException("The 'recipient_ids' parameter cannot be empty.")
    
    valid_methods = ['email', 'wechat_work', 'link_share']
    if distribute_method not in valid_methods:
        raise InvalidRequestException(f"Invalid distribution method. Valid methods are: {valid_methods}")
    
    valid_attachments = ['original_record', 'task_list', 'key_points']
    if attachments:
        for att in attachments:
            if att not in valid_attachments:
                raise InvalidRequestException(f"Invalid attachment type '{att}'. Valid types are: {valid_attachments}")
    
    data = _load_data()
    minutes = _get_minutes(data, minutes_id)
    
    # Simulate distribution
    distribution_log = {
        'log_id': _generate_id('dist'),
        'minutes_id': minutes_id,
        'distribute_method': distribute_method,
        'recipients': [],
        'attachments': attachments or [],
        'distributed_at': _get_current_time()
    }
    
    success_count = 0
    failure_count = 0
    
    for recipient_id in recipient_ids:
        # Simulate distribution (in reality, this would send emails, etc.)
        recipient_status = {
            'recipient_id': recipient_id,
            'status': 'sent',
            'read_status': 'unread',
            'sent_at': _get_current_time()
        }
        distribution_log['recipients'].append(recipient_status)
        success_count += 1
    
    # Generate share link if method is link_share
    if distribute_method == 'link_share':
        share_link = f"https://meetmin.example.com/share/{minutes_id}"
        distribution_log['share_link'] = share_link
        distribution_log['link_expires_at'] = '2025-12-27T23:59:59Z'  # 7 days validity
    
    data.setdefault('distribution_logs', []).append(distribution_log)
    _save_data(data)
    
    return {
        'success': True,
        'message': f'Minutes distributed successfully to {success_count} recipient(s).',
        'success_count': success_count,
        'failure_count': failure_count,
        'distribution_log': distribution_log
    }


def query_meeting_history(query_key: str, query_types: List[str] = None) -> Dict[str, Any]:
    """
    Query meeting history information.

    Args:
        query_key (str): Query keyword: meeting_id, meeting title, or time range (format: 'YYYY-MM-DD to YYYY-MM-DD').
        query_types (List[str], optional): Query types: 'minutes', 'tasks', 'records'. Default is all.

    Returns:
        dict: A dictionary containing meeting history information including basic info, related minutes, tasks, and records.
    """
    if not query_key or not query_key.strip():
        raise InvalidRequestException("The 'query_key' parameter cannot be empty.")
    
    valid_types = ['minutes', 'tasks', 'records']
    query_types = query_types or valid_types
    for qt in query_types:
        if qt not in valid_types:
            raise InvalidRequestException(f"Invalid query type '{qt}'. Valid types are: {valid_types}")
    
    data = _load_data()
    
    # Try to find meetings by ID, title, or time range
    meetings = data.get('meetings', [])
    matched_meetings = []
    
    # Check if query_key is a time range
    if ' to ' in query_key:
        try:
            start_date, end_date = query_key.split(' to ')
            for meeting in meetings:
                meeting_date = meeting.get('start_time', '')[:10]
                if start_date <= meeting_date <= end_date:
                    matched_meetings.append(meeting)
        except:
            pass
    else:
        # Search by ID or title
        for meeting in meetings:
            if (query_key.lower() in meeting.get('meeting_id', '').lower() or
                query_key.lower() in meeting.get('title', '').lower()):
                matched_meetings.append(meeting)
    
    results = []
    for meeting in matched_meetings:
        meeting_id = meeting.get('meeting_id')
        result = {
            'meeting': meeting
        }
        
        if 'minutes' in query_types:
            result['minutes'] = [m for m in data.get('minutes', []) if m.get('meeting_id') == meeting_id]
        
        if 'tasks' in query_types:
            result['tasks'] = [t for t in data.get('tasks', []) if t.get('meeting_id') == meeting_id]
        
        if 'records' in query_types:
            result['records'] = [r for r in data.get('records', []) if r.get('meeting_id') == meeting_id]
        
        results.append(result)
    
    return {
        'success': True,
        'query_key': query_key,
        'results': results,
        'total_meetings': len(results)
    }
