import json
import os
import shutil
from datetime import datetime
from typing import Any, Dict, Iterable, List

DATA_PATH = 'environment/reports/EvernoteManager.json'
INIT_PATH = 'environment/initial/EvernoteManager_init.json'

INIT = False


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


def _ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def _ensure_work_env():
    global INIT
    if not os.path.exists(INIT_PATH):
        raise InvalidRequestException(f'Init file not found: {INIT_PATH}')
    _ensure_dir(os.path.dirname(DATA_PATH))
    if not INIT:
        shutil.copyfile(INIT_PATH, DATA_PATH)
        INIT = True
    if not os.path.exists(DATA_PATH):
        shutil.copyfile(INIT_PATH, DATA_PATH)


def _load_data() -> Dict[str, Any]:
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_data(data: Dict[str, Any]):
    _ensure_dir(os.path.dirname(DATA_PATH))
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def _increment(data: Dict[str, Any], key: str, prefix: str) -> str:
    value = data.get(key, 1)
    identifier = f"{prefix}-{value:03d}"
    data[key] = value + 1
    return identifier


def _get_note(data: Dict[str, Any], note_id: str) -> Dict[str, Any]:
    note = next((n for n in data.get('notes', []) if n.get('note_id') == note_id), None)
    if not note:
        raise NotFoundException('Note not found.')
    return note


def _get_notebook(data: Dict[str, Any], notebook_id: str) -> Dict[str, Any]:
    notebook = next((n for n in data.get('notebooks', []) if n.get('notebook_id') == notebook_id), None)
    if not notebook:
        raise NotFoundException('Notebook not found.')
    return notebook


def _validate_tags(tags: Any):
    if tags is None:
        return []
    if not isinstance(tags, list):
        raise InvalidRequestException("The 'tags' argument must be a list of strings.")
    for tag in tags:
        if not isinstance(tag, str) or not tag.strip():
            raise InvalidRequestException("Each tag must be a non-empty string.")
    return [tag.strip() for tag in tags]


def CreateNote(title: str, content: str, attachments: List[str] = None, notebook_id: str = None, tags: List[str] = None) -> Dict[str, Any]:
    """Create a new note with title, content, attachments, optional notebook, and optional tags.

    Args:
        title (str): The title of the note.
        content (str): The content of the note.
        attachments (List[str]): List of file paths to attach to the note.
        notebook_id (str): Optional notebook ID to associate the note with.
        tags (List[str]): Optional list of tags for the note.
    """
    if not title or not title.strip():
        raise InvalidRequestException("The 'title' parameter cannot be empty.")
    if not content or not content.strip():
        raise InvalidRequestException("The 'content' parameter cannot be empty.")
    attachments = attachments or []
    if isinstance(attachments, str):
        attachments = [attachments]
    elif not isinstance(attachments, list):
        raise InvalidRequestException("The 'attachments' parameter must be a list of file paths or a single string.")
    tags = _validate_tags(tags or [])
    data = _load_data()
    note_id = _increment(data, 'next_note_id', 'note')
    note = {
        'note_id': note_id,
        'title': title.strip(),
        'content': content.strip(),
        'attachments': attachments,
        'notebook_id': notebook_id,
        'tags': tags,
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    data.setdefault('notes', []).append(note)
    if notebook_id:
        notebook = _get_notebook(data, notebook_id)
        notebook.setdefault('note_ids', []).append(note_id)
    _save_data(data)
    return {'note_id': note_id}


def ReadNote(note_id: str) -> Dict[str, Any]:
    """Read a note by its ID.

    Args:
        note_id (str): The ID of the note to read.
    """
    data = _load_data()
    note = _get_note(data, note_id)
    return {'note': note}


def UpdateNote(note_id: str, title: str = None, content: str = None, attachments: List[str] = None) -> Dict[str, Any]:
    """Update an existing note with new title, content, or attachments.

    Args:
        note_id (str): The ID of the note to update.
        title (str): Optional new title for the note.
        content (str): Optional new content for the note.
        attachments (List[str]): Optional new list of attachments for the note.
    """
    updated = False
    data = _load_data()
    note = _get_note(data, note_id)
    if title is not None:
        if not title.strip():
            raise InvalidRequestException("The 'title' parameter cannot be empty when provided.")
        note['title'] = title.strip()
        updated = True
    if content is not None:
        if not content.strip():
            raise InvalidRequestException("The 'content' parameter cannot be empty when provided.")
        note['content'] = content.strip()
        updated = True
    if attachments is not None:
        if isinstance(attachments, str):
            attachments = [attachments]
        elif not isinstance(attachments, list):
            raise InvalidRequestException("The 'attachments' parameter must be a list of file paths or a single string.")
        note['attachments'] = attachments
        updated = True
    if not updated:
        raise InvalidRequestException("At least one updatable field must be provided.")
    note['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    _save_data(data)
    return {'success': True}


def DeleteNote(note_id: str) -> Dict[str, Any]:
    """Delete a note by its ID.

    Args:
        note_id (str): The ID of the note to delete.
    """
    data = _load_data()
    note = next((n for n in data.get('notes', []) if n.get('note_id') == note_id), None)
    if not note:
        return {'success': False, 'message': 'Note not found.'}
    data['notes'] = [n for n in data.get('notes', []) if n.get('note_id') != note_id]
    for notebook in data.get('notebooks', []):
        note_ids = notebook.get('note_ids', [])
        if note_id in note_ids:
            note_ids.remove(note_id)
    data.get('sharing', {}).pop(note_id, None)
    _save_data(data)
    return {'success': True}


def CreateNotebook(name: str) -> Dict[str, Any]:
    """Create a new notebook with the specified name.

    Args:
        name (str): The name of the notebook to create.
    """
    if not name or not name.strip():
        raise InvalidRequestException("The 'name' parameter cannot be empty.")
    data = _load_data()
    notebook_id = _increment(data, 'next_notebook_id', 'notebook')
    notebook = {
        'notebook_id': notebook_id,
        'name': name.strip(),
        'note_ids': [],
        'created_at': datetime.utcnow().isoformat() + 'Z'
    }
    data.setdefault('notebooks', []).append(notebook)
    _save_data(data)
    return {'notebook_id': notebook_id}


def ReadNotebook(notebook_id: str) -> Dict[str, Any]:
    """Read a notebook and all its notes by notebook ID.

    Args:
        notebook_id (str): The ID of the notebook to read.
    """
    data = _load_data()
    notebook = _get_notebook(data, notebook_id)
    notes = [n for n in data.get('notes', []) if n.get('note_id') in notebook.get('note_ids', [])]
    result = notebook.copy()
    result['notes'] = notes
    return {'notebook': result}


def UpdateNotebook(notebook_id: str = None, notebook_name: str = None, name: str = None) -> Dict[str, Any]:
    """Update a notebook name by ID or name.

    Args:
        notebook_id (str): Optional notebook ID to identify the notebook.
        notebook_name (str): Optional notebook name to identify the notebook.
        name (str): The new name for the notebook.
    """
    if not name or not name.strip():
        raise InvalidRequestException("The 'name' parameter cannot be empty.")
    if not notebook_id and not notebook_name:
        raise InvalidRequestException("Either 'notebook_id' or 'notebook_name' must be provided.")
    data = _load_data()
    if notebook_id:
        try:
            notebook = _get_notebook(data, notebook_id)
        except NotFoundException:
            # try as name
            notebook = next((n for n in data.get('notebooks', []) if notebook_id == n.get('name') or n.get('name') == notebook_id or notebook_id.replace('nb-', '').replace('-', ' ').lower() == n.get('name', '').lower()), None)
            if not notebook:
                raise NotFoundException('Notebook not found.')
    elif notebook_name:
        notebook = next((n for n in data.get('notebooks', []) if n.get('name') == notebook_name), None)
        if not notebook:
            raise NotFoundException('Notebook not found.')
    notebook['name'] = name.strip()
    notebook['updated_at'] = datetime.utcnow().isoformat() + 'Z'
    _save_data(data)
    return {'success': True}


def DeleteNotebook(notebook_id: str = None, notebook_name: str = None) -> Dict[str, Any]:
    """Delete a notebook by ID or name.

    Args:
        notebook_id (str): Optional notebook ID to identify the notebook.
        notebook_name (str): Optional notebook name to identify the notebook.
    """
    if not notebook_id and not notebook_name:
        raise InvalidRequestException("Either 'notebook_id' or 'notebook_name' must be provided.")
    data = _load_data()
    if notebook_id:
        try:
            notebook = _get_notebook(data, notebook_id)
        except NotFoundException:
            # try as name
            notebook = next((n for n in data.get('notebooks', []) if notebook_id == n.get('name') or n.get('name') == notebook_id or notebook_id.replace('nb-', '').replace('-', ' ').lower() == n.get('name', '').lower()), None)
            if not notebook:
                return {'success': False, 'message': 'Notebook not found.'}
    elif notebook_name:
        notebook = next((n for n in data.get('notebooks', []) if n.get('name') == notebook_name), None)
        if not notebook:
            return {'success': False, 'message': 'Notebook not found.'}
    if notebook.get('note_ids'):
        for note_id in notebook.get('note_ids', []):
            data['notes'] = [n for n in data.get('notes', []) if n.get('note_id') != note_id]
            for nb in data.get('notebooks', []):
                nb_ids = nb.get('note_ids', [])
                if note_id in nb_ids:
                    nb_ids.remove(note_id)
    data['notebooks'] = [n for n in data.get('notebooks', []) if n.get('notebook_id') != notebook['notebook_id']]
    _save_data(data)
    return {'success': True}


def SearchNotes(
    keywords: List[str] = None,
    tags: List[str] = None,
    notebook_id: str = None,
    notebook_name: str = None,
    max_results: int = 3
) -> Dict[str, Any]:
    """Search for notes by keywords, tags, and notebook.

    Args:
        keywords (List[str]): Optional list of keywords to search for.
        tags (List[str]): Optional list of tags to filter by.
        notebook_id (str): Optional notebook ID to filter notes.
        notebook_name (str): Optional notebook name to filter notes.
        max_results (int): Maximum number of results to return.
    """
    if keywords is not None:
        if isinstance(keywords, str):
            keywords = [keywords]
        elif not isinstance(keywords, list):
            raise InvalidRequestException("The 'keywords' parameter must be a list of strings or a single string.")
    if tags is not None:
        if isinstance(tags, str):
            tags = [tags]
        elif not isinstance(tags, list):
            raise InvalidRequestException("The 'tags' parameter must be a list of strings or a single string.")
    if max_results is None:
        max_results = 3
    try:
        max_results = int(max_results)
    except Exception:
        raise InvalidRequestException("The 'max_results' parameter is not a valid integer.")
    if max_results <= 0:
        raise InvalidRequestException("The 'max_results' parameter must be positive.")
    data = _load_data()
    if notebook_name:
        notebook = next((n for n in data.get('notebooks', []) if n.get('name') == notebook_name), None)
        if notebook:
            notebook_id = notebook['notebook_id']
    results = []
    for note in data.get('notes', []):
        matched = True
        if notebook_id:
            if note.get('notebook_id') != notebook_id:
                matched = False
        if matched and keywords:
            lower_text = f"{note.get('title', '')} {note.get('content', '')} {' '.join(note.get('tags', []))}".lower()
            if not any(k.lower() in lower_text for k in keywords):
                matched = False
        if matched and tags:
            note_tags = [t.lower() for t in (note.get('tags') or [])]
            if not any(t.lower() in note_tags for t in tags):
                matched = False
        if matched:
            summary = note.copy()
            content = note.get('content', '')
            summary['snippet'] = content[:50]
            results.append(summary)
            if len(results) >= max_results:
                break
    return {'notes': results}


def ManageNoteSharingLevel(note_id: str, email: str, level: str) -> Dict[str, Any]:
    """Manage the sharing level of a note for a specific email.

    Args:
        note_id (str): The ID of the note to manage sharing for.
        email (str): The email address to share with.
        level (str): The sharing level (not_accessible, read_only, or can_edit).
    """
    if '@' not in email or not email.strip():
        raise InvalidRequestException('The email is invalid.')
    allowed = {'not_accessible', 'read_only', 'can_edit'}
    if level not in allowed:
        raise InvalidRequestException("The 'level' must be one of 'not_accessible', 'read_only', or 'can_edit'.")
    data = _load_data()
    _get_note(data, note_id)
    sharing = data.setdefault('sharing', {})
    sharing.setdefault(note_id, {})[email] = level
    _save_data(data)
    return {'success': True}


def SearchNotebooks(keywords: Iterable[str] = None, name: str = None, max_results: int = 10) -> Dict[str, Any]:
    """Search for notebooks by keywords and name.

    Args:
        keywords (Iterable[str]): Optional list of keywords to search for.
        name (str): Optional name to filter notebooks.
        max_results (int): Maximum number of results to return.
    """
    if keywords is not None:
        if isinstance(keywords, str):
            keywords = [keywords]
        elif hasattr(keywords, '__iter__'):
            keywords = list(keywords)
        else:
            raise InvalidRequestException("The 'keywords' parameter must be a list of strings or a single string.")
    if max_results is None:
        max_results = 10
    data = _load_data()
    results = []
    for notebook in data.get('notebooks', []):
        matched = True
        if name and name.lower() not in notebook.get('name', '').lower():
            matched = False
        if matched and keywords:
            lower_name = notebook.get('name', '').lower()
            if not any(k.lower() in lower_name for k in keywords):
                matched = False
        if matched:
            results.append(notebook)
            if len(results) >= max_results:
                break
    return {'notebooks': results}
