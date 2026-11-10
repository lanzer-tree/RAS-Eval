import json
import os
import shutil
import re
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List


DATA_PATH = os.path.join('environment', 'reports', 'todolist.json')
INIT_PATH = os.path.join('environment', 'initial', 'todolist_init.json')

INIT = False
class InvalidRequestException(Exception):
    pass

class NotFoundException(Exception):
    pass

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

def _read_env():
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def _write_env(data):
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _validate_date(date_str, fmt='%Y-%m-%d'):
    try:
        datetime.strptime(date_str, fmt)
        return True
    except Exception:
        return False

def _validate_datetime(dt_str, fmt='%Y-%m-%d %H:%M:%S'):
    try:
        datetime.strptime(dt_str, fmt)
        return True
    except Exception:
        return False

def _validate_priority(p):
    if p is None:
        return True
    try:
        pi = int(p)
        return 1 <= pi <= 4
    except Exception:
        return False

def _find_task_by_id(tasks, task_id):
    for t in tasks:
        if t.get('task_id') == task_id:
            return t
    return None

def CreateTask(task_name: str, description: Optional[str] = None, due_date: Optional[str] = None, priority: Optional[int] = None) -> Dict[str, Any]:
    """Create a new task with the specified details.

    Args:
        task_name (str): The name/title of the task
        description (str, optional): Detailed description of the task
        due_date (str, optional): Due date in YYYY-MM-DD format
        priority (int, optional): Priority level from 1 to 4, where 1 is highest
    """
    if not task_name or not task_name.strip():
        raise InvalidRequestException('task_name is empty')
    if due_date and not _validate_date(due_date):
        raise InvalidRequestException('due_date not in YYYY-MM-DD format')
    if not _validate_priority(priority):
        raise InvalidRequestException('priority must be integer 1-4')

    env = _read_env()
    tasks = env.setdefault('tasks', [])
    task_id = uuid.uuid4().hex
    task = {
        'task_id': task_id,
        'task_name': task_name,
        'description': description or '',
        'due_date': due_date or '',
        'priority': int(priority) if priority is not None else None,
        'status': 'in progress',
        'reminders': [],
        'shared_with': [],
        'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    }
    tasks.append(task)
    _write_env(env)
    return {'task_id': task_id}

def UpdateTask(task_id: Optional[str] = None, task_name: Optional[str] = None, description: Optional[str] = None, due_date: Optional[str] = None, priority: Optional[int] = None, status: Optional[str] = None) -> Dict[str, Any]:
    """Update an existing task by ID or name.

    Args:
        task_id (str, optional): Unique identifier of the task to update
        task_name (str, optional): New name for the task
        description (str, optional): New description for the task
        due_date (str, optional): New due date in YYYY-MM-DD format
        priority (int, optional): New priority level from 1 to 4
        status (str, optional): New status, either 'in progress' or 'completed'
    """
    if not task_id and not task_name:
        raise InvalidRequestException('Either task_id or task_name must be provided')

    env = _read_env()
    tasks = env.get('tasks', [])

    # resolve name -> id when necessary
    if not task_id and task_name:
        matches = GetTaskIdsByName(task_name, exact=True, max_results=10).get('tasks', [])
        if not matches:
            # try fuzzy match
            matches = GetTaskIdsByName(task_name, exact=False, max_results=10).get('tasks', [])
        if not matches:
            raise NotFoundException('No task matches the given name')
        if len(matches) > 1:
            names = [m.get('task_name') + ':' + m.get('task_id') for m in matches]
            raise InvalidRequestException('Multiple tasks match the name, please specify task_id. Matches: ' + ', '.join(names))
        task_id = matches[0].get('task_id')

    task = _find_task_by_id(tasks, task_id)
    if not task:
        raise NotFoundException('task_id does not exist')
    if due_date and not _validate_date(due_date):
        raise InvalidRequestException('due_date not in YYYY-MM-DD format')
    if not _validate_priority(priority):
        raise InvalidRequestException('priority must be integer 1-4')
    if status and status not in ('in progress', 'completed'):
        raise InvalidRequestException("status must be 'in progress' or 'completed'")

    if task_name is not None:
        task['task_name'] = task_name
    if description is not None:
        task['description'] = description
    if due_date is not None:
        task['due_date'] = due_date
    if priority is not None:
        task['priority'] = int(priority)
    if status is not None:
        task['status'] = status

    _write_env(env)
    return {'success': True}

def DeleteTask(task_id: str) -> Dict[str, Any]:
    """Delete a task by its unique identifier.

    Args:
        task_id (str): Unique identifier of the task to delete
    """
    env = _read_env()
    tasks = env.get('tasks', [])
    task = _find_task_by_id(tasks, task_id)
    if not task:
        raise NotFoundException('task_id does not exist')
    tasks.remove(task)
    _write_env(env)
    return {'success': True}

def SearchTasks(keywords: Optional[str] = None, due_date: Optional[str] = None, priority: Optional[int] = None, status: Optional[str] = None, max_results: Optional[int] = 10) -> Dict[str, Any]:
    """Search for tasks matching the specified criteria.

    Args:
        keywords (str, optional): Keywords to search in task name and description
        due_date (str, optional): Filter by due date in YYYY-MM-DD format
        priority (int, optional): Filter by priority level from 1 to 4
        status (str, optional): Filter by status, either 'in progress' or 'completed'
        max_results (int, optional): Maximum number of results to return
    """
    if due_date and not _validate_date(due_date):
        raise InvalidRequestException('due_date not in YYYY-MM-DD format')
    if not _validate_priority(priority):
        raise InvalidRequestException('priority must be integer 1-4')
    if max_results is None:
        max_results = 10
    try:
        max_results = int(max_results)
        if max_results <= 0:
            raise ValueError()
    except Exception:
        raise InvalidRequestException('max_results must be positive integer')

    env = _read_env()
    tasks = env.get('tasks', [])
    results = []
    kw = (keywords or '').lower()
    for t in tasks:
        if keywords:
            if kw not in (t.get('task_name') or '').lower() and kw not in (t.get('description') or '').lower():
                continue
        if due_date and t.get('due_date') != due_date:
            continue
        if priority is not None and t.get('priority') != int(priority):
            continue
        if status and t.get('status') != status:
            continue
        results.append({
            'task_id': t.get('task_id'),
            'task_name': t.get('task_name'),
            'description': t.get('description'),
            'due_date': t.get('due_date'),
            'priority': t.get('priority'),
            'status': t.get('status')
        })
        if len(results) >= max_results:
            break
    return {'tasks': results}

def SetReminder(task_id: Optional[str], reminder_time: Optional[str]) -> Dict[str, Any]:
    """Set a reminder for a specific task.

    Args:
        task_id (str): Unique identifier of the task to set reminder for
        reminder_time (str): Reminder time in YYYY-MM-DD HH:MM:SS format
    """
    if not _validate_datetime(reminder_time):
        raise InvalidRequestException('reminder_time not in YYYY-MM-DD HH:MM:SS format')
    env = _read_env()
    tasks = env.get('tasks', [])
    task = _find_task_by_id(tasks, task_id)
    if not task:
        raise NotFoundException('task_id does not exist')
    reminders = task.setdefault('reminders', [])
    reminders.append(reminder_time)
    _write_env(env)
    return {'success': True}

def ShareTask(task_id: Optional[str], user_email: Optional[str]) -> Dict[str, Any]:
    """Share a task with another user via email.

    Args:
        task_id (str): Unique identifier of the task to share
        user_email (str): Email address of the user to share with
    """
    # very simple email validation
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", user_email or ''):
        raise InvalidRequestException('user_email is not in correct format')
    env = _read_env()
    tasks = env.get('tasks', [])
    task = _find_task_by_id(tasks, task_id)
    if not task:
        raise NotFoundException('task_id does not exist')
    shared = task.setdefault('shared_with', [])
    if user_email not in shared:
        shared.append(user_email)
    _write_env(env)
    return {'success': True}


def GetTaskIdsByName(name: str, exact: Optional[bool] = False, max_results: Optional[int] = 10) -> Dict[str, Any]:
    """Return a list of matching tasks (task_id and task_name) for a given name.

    Args:
        name (str): Search string to match against task names
        exact (bool, optional): If True, only exact (case-insensitive) matches on task_name are returned
        max_results (int, optional): Maximum number of results to return
    """
    if not name or not name.strip():
        return {'tasks': []}
    if max_results is None:
        max_results = 10
    try:
        max_results = int(max_results)
        if max_results <= 0:
            raise ValueError()
    except Exception:
        raise InvalidRequestException('max_results must be positive integer')

    env = _read_env()
    tasks = env.get('tasks', [])
    results = []
    search_name = name.strip().lower()
    for t in tasks:
        task_name = t.get('task_name', '').lower()
        if exact:
            if task_name == search_name:
                results.append({
                    'task_id': t.get('task_id'),
                    'task_name': t.get('task_name')
                })
        else:
            if search_name in task_name:
                results.append({
                    'task_id': t.get('task_id'),
                    'task_name': t.get('task_name')
                })
        if len(results) >= max_results:
            break
    return {'tasks': results}


def todowrite(todos: Optional[List[Dict[str, Any]]] = None, content: Optional[str] = None, status: Optional[str] = None, priority: Optional[str] = None) -> List[Dict[str, Any]]:
    """Create and maintain a structured task list for the current session.

    Args:
        todos (list, optional): List of todo items with content, status, priority keys.
        content (str, optional): Single todo item content (flat format).
        status (str, optional): Single todo item status (flat format).
        priority (str, optional): Single todo item priority (flat format).
    """
    if todos is not None:
        return todos
    if content is not None:
        return [{"content": content, "status": status or "pending", "priority": priority or "medium"}]
    return []


__all__ = [
    'CreateTask', 'UpdateTask', 'DeleteTask', 'SearchTasks', 'SetReminder', 'ShareTask', 'GetTaskIdsByName',
    'todowrite',
    'InvalidRequestException', 'NotFoundException'
]