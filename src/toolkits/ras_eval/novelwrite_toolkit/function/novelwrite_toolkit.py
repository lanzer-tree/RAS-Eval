import json
import os
import shutil
import uuid
from datetime import datetime, timedelta
from typing import Optional


DATA_PATH = os.path.join('environment', 'reports', 'novelwrite.json')
INIT_PATH = os.path.join('environment', 'initial', 'novelwrite_init.json')


class InvalidRequestException(Exception):
    pass

class NotFoundException(Exception):
    pass

def _ensure_work_env():
    """Ensure working environment file exists by copying from init if necessary."""
    if not os.path.exists(INIT_PATH):
        raise InvalidRequestException(f'Init file not found: {INIT_PATH}')
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    if not os.path.exists(DATA_PATH):
        shutil.copyfile(INIT_PATH, DATA_PATH)

def _read_env():
    """Read environment data from JSON file."""
    _ensure_work_env()
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)
    
def _write_env(data):
    """Write environment data to JSON file."""
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def _find_project_by_id(projects, project_id):
    """Find a project by its ID."""
    for project in projects:
        if project.get('project_id') == project_id:
            return project
    return None

def _find_project_by_name(projects, project_name):
    """Find a project by its name."""
    for project in projects:
        if project.get('project_name').lower() == project_name.lower():
            return project
    return None

def _call_llm_for_text_check(text, check_type):
    """Simulate LLM call for text checking."""
    issues = []
    if check_type == 'grammar':
        issues.append({'line': 1, 'issue': 'Example grammar issue', 'suggestion': 'Corrected version'})
    elif check_type == 'spelling':
        issues.append({'word': 'exmaple', 'suggestion': 'example', 'position': 10})
    elif check_type == 'punctuation':
        issues.append({'line': 2, 'issue': 'Missing comma', 'suggestion': 'Add comma after clause'})
    elif check_type == 'redundancy':
        issues.append({'text': 'very very', 'suggestion': 'very', 'line': 1})
    elif check_type == 'style':
        issues.append({'issue': 'Sentence too long', 'suggestion': 'Split into two sentences', 'line': 3})
    return {'check_type': check_type, 'issues_found': len(issues), 'issues': issues, 'overall_assessment': f'{check_type.capitalize()} check completed. Found {len(issues)} issue(s).'}

def _call_llm_for_expansion(content, requirements):
    """Simulate LLM call for content expansion."""
    expanded_text = f'{content}\n\n[Expanded content based on requirements: {requirements}]\n\nThe story continues with rich details and vivid descriptions that bring the scene to life...'
    return {'original_length': len(content), 'expanded_length': len(expanded_text), 'expanded_content': expanded_text, 'expansion_ratio': round(len(expanded_text) / len(content), 2) if len(content) > 0 else 0}

def _call_llm_for_scoring(content):
    """Simulate LLM call for content scoring."""
    import random
    readability = round(random.uniform(7.0, 9.5), 1)
    plot_tension = round(random.uniform(7.0, 9.5), 1)
    character_development = round(random.uniform(7.0, 9.5), 1)
    writing_quality = round(random.uniform(7.0, 9.5), 1)
    overall = round((readability + plot_tension + character_development + writing_quality) / 4, 1)
    return {'readability_score': readability, 'plot_tension_score': plot_tension, 'character_development_score': character_development, 'writing_quality_score': writing_quality, 'overall_score': overall, 'detailed_feedback': {'strengths': ['Engaging dialogue', 'Vivid descriptions', 'Strong character voice'], 'areas_for_improvement': ['Pacing could be tighter', 'More sensory details needed']}}

def _call_llm_for_suggestions(content):
    """Simulate LLM call for writing suggestions."""
    suggestions = ['Consider adding more dialogue to break up narrative passages', "The character's motivation could be clearer in this section", 'Strong opening hook, but consider varying sentence structure for better rhythm', 'The setting description is vivid - consider using similar techniques in other scenes']
    return {'suggestions_count': len(suggestions), 'suggestions': suggestions, 'overall_recommendation': 'The piece shows strong potential. Focus on pacing and character motivation to elevate the narrative.'}

def _CreateProject(project_name: str, genre: str=None, description: str=None):
    """
    Create a new novel project.
    
    Args:
        project_name: The name of the novel project
        genre: Optional genre of the novel (e.g., fantasy, romance, thriller)
        description: Optional description or synopsis of the project
    """
    if not project_name or not project_name.strip():
        raise InvalidRequestException('project_name cannot be empty')
    env = _read_env()
    projects = env.setdefault('projects', [])
    if _find_project_by_name(projects, project_name):
        raise InvalidRequestException(f'Project with name "{project_name}" already exists')
    project_id = uuid.uuid4().hex
    project = {'project_id': project_id, 'project_name': project_name, 'genre': genre or '', 'description': description or '', 'created_at': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'last_modified': datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'), 'content': '', 'word_count': 0, 'writing_time_minutes': 0, 'status': 'active'}
    projects.append(project)
    env['current_project_id'] = project_id
    _write_env(env)
    return json.dumps({'success': True, 'project_id': project_id, 'project_name': project_name, 'message': f'Project "{project_name}" created successfully'})


def CreateProject(project_name: str, genre: str=None, description: str=None) -> str:
    """
    Create a new novel project.
    
    Args:
        project_name: The name of the novel project
        genre: Optional genre of the novel (e.g., fantasy, romance, thriller)
        description: Optional description or synopsis of the project
    """
    return _CreateProject(project_name=project_name, genre=genre, description=description)


def _SwitchProject(project_name: str):
    """
    Switch to a different project.
    
    Args:
        project_name: The name of the project to switch to
    """
    if not project_name or not project_name.strip():
        raise InvalidRequestException('project_name cannot be empty')
    env = _read_env()
    projects = env.get('projects', [])
    project = _find_project_by_name(projects, project_name)
    if not project:
        raise NotFoundException(f'Project "{project_name}" not found')
    env['current_project_id'] = project['project_id']
    _write_env(env)
    return json.dumps({'success': True, 'project_id': project['project_id'], 'project_name': project['project_name'], 'message': f'Switched to project "{project_name}"'})


def SwitchProject(project_name: str) -> str:
    """
    Switch to a different project.
    
    Args:
        project_name: The name of the project to switch to
    """
    return _SwitchProject(project_name=project_name)


def _ListProjects():
    """
    List all novel projects.
    """
    env = _read_env()
    projects = env.get('projects', [])
    current_project_id = env.get('current_project_id')
    project_list = []
    for project in projects:
        project_list.append({'project_id': project['project_id'], 'project_name': project['project_name'], 'genre': project['genre'], 'word_count': project['word_count'], 'status': project['status'], 'is_current': project['project_id'] == current_project_id, 'last_modified': project['last_modified']})
    return json.dumps({'success': True, 'total_projects': len(project_list), 'projects': project_list})


def ListProjects() -> str:
    """
    List all novel projects.
    """
    return _ListProjects()


def _WriteContent(content: str, append: bool=True):
    """
    Write or append content to the current project.
    
    Args:
        content: The content to write
        append: If True, append to existing content; if False, replace existing content
    """
    if not content:
        raise InvalidRequestException('content cannot be empty')
    env = _read_env()
    current_project_id = env.get('current_project_id')
    if not current_project_id:
        raise InvalidRequestException('No current project selected. Please create or switch to a project first.')
    projects = env.get('projects', [])
    project = _find_project_by_id(projects, current_project_id)
    if not project:
        raise NotFoundException('Current project not found')
    if append:
        project['content'] = project['content'] + '\n' + content if project['content'] else content
    else:
        project['content'] = content
    project['word_count'] = len(project['content'].split())
    project['last_modified'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    _write_env(env)
    return json.dumps({'success': True, 'message': 'Content written successfully', 'word_count': project['word_count'], 'project_name': project['project_name']})


def WriteContent(content: str, append: bool=True) -> str:
    """
    Write or append content to the current project.
    
    Args:
        content: The content to write
        append: If True, append to existing content; if False, replace existing content
    """
    return _WriteContent(content=content, append=append)


def _GetContent(project_name: str=None):
    """
    Get content from a project.
    
    Args:
        project_name: Optional project name. If not provided, uses current project
    """
    env = _read_env()
    projects = env.get('projects', [])
    if project_name:
        project = _find_project_by_name(projects, project_name)
        if not project:
            raise NotFoundException(f'Project "{project_name}" not found')
    else:
        current_project_id = env.get('current_project_id')
        if not current_project_id:
            raise InvalidRequestException('No current project selected')
        project = _find_project_by_id(projects, current_project_id)
        if not project:
            raise NotFoundException('Current project not found')
    return json.dumps({'success': True, 'project_name': project['project_name'], 'content': project['content'], 'word_count': project['word_count'], 'last_modified': project['last_modified']})


def GetContent(project_name: str=None) -> str:
    """
    Get content from a project.
    
    Args:
        project_name: Optional project name. If not provided, uses current project
    """
    return _GetContent(project_name=project_name)


def _ImportDocument(file_path: str, project_name: str=None):
    """
    Import a document into a project.
    
    Args:
        file_path: Path to the document file to import
        project_name: Optional project name. If not provided, uses current project
    """
    if not file_path:
        raise InvalidRequestException('file_path cannot be empty')
    if not os.path.exists(file_path):
        raise InvalidRequestException(f'File not found: {file_path}')
    with open(file_path, 'r', encoding='utf-8') as f:
        imported_content = f.read()
    env = _read_env()
    projects = env.get('projects', [])
    if project_name:
        project = _find_project_by_name(projects, project_name)
        if not project:
            raise NotFoundException(f'Project "{project_name}" not found')
    else:
        current_project_id = env.get('current_project_id')
        if not current_project_id:
            raise InvalidRequestException('No current project selected')
        project = _find_project_by_id(projects, current_project_id)
        if not project:
            raise NotFoundException('Current project not found')
    project['content'] = project['content'] + '\n' + imported_content if project['content'] else imported_content
    project['word_count'] = len(project['content'].split())
    project['last_modified'] = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
    _write_env(env)
    return json.dumps({'success': True, 'message': f'Document imported from {file_path}', 'project_name': project['project_name'], 'word_count': project['word_count']})


def ImportDocument(file_path: str, project_name: str=None) -> str:
    """
    Import a document into a project.
    
    Args:
        file_path: Path to the document file to import
        project_name: Optional project name. If not provided, uses current project
    """
    return _ImportDocument(file_path=file_path, project_name=project_name)


def _ExportDocument(file_path: str, project_name: str=None):
    """
    Export a project to a document file.
    
    Args:
        file_path: Path where the document should be exported
        project_name: Optional project name. If not provided, uses current project
    """
    if not file_path:
        raise InvalidRequestException('file_path cannot be empty')
    env = _read_env()
    projects = env.get('projects', [])
    if project_name:
        project = _find_project_by_name(projects, project_name)
        if not project:
            raise NotFoundException(f'Project "{project_name}" not found')
    else:
        current_project_id = env.get('current_project_id')
        if not current_project_id:
            raise InvalidRequestException('No current project selected')
        project = _find_project_by_id(projects, current_project_id)
        if not project:
            raise NotFoundException('Current project not found')
    export_dir = os.path.dirname(file_path)
    if export_dir and not os.path.exists(export_dir):
        os.makedirs(export_dir, exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(project['content'])
    return json.dumps({'success': True, 'message': f'Project exported to {file_path}', 'project_name': project['project_name'], 'word_count': project['word_count'], 'file_path': file_path})


def ExportDocument(file_path: str, project_name: str=None) -> str:
    """
    Export a project to a document file.
    
    Args:
        file_path: Path where the document should be exported
        project_name: Optional project name. If not provided, uses current project
    """
    return _ExportDocument(file_path=file_path, project_name=project_name)


def _CheckGrammar(content: str=None):
    """
    Check grammar in content using AI.
    
    Args:
        content: Optional content to check. If not provided, checks current project content
    """
    env = _read_env()
    if content is None:
        current_project_id = env.get('current_project_id')
        if not current_project_id:
            raise InvalidRequestException('No current project selected and no content provided')
        projects = env.get('projects', [])
        project = _find_project_by_id(projects, current_project_id)
        if not project:
            raise NotFoundException('Current project not found')
        content = project['content']
    if not content:
        raise InvalidRequestException('No content to check')
    result = _call_llm_for_text_check(content, 'grammar')
    return json.dumps({'success': True, 'check_type': 'grammar', 'result': result})


def CheckGrammar(content: str=None) -> str:
    """
    Check grammar in content using AI.
    
    Args:
        content: Optional content to check. If not provided, checks current project content
    """
    return _CheckGrammar(content=content)


def _CheckSpelling(content: str=None):
    """
    Check spelling in content using AI.
    
    Args:
        content: Optional content to check. If not provided, checks current project content
    """
    env = _read_env()
    if content is None or content == "":
        current_project_id = env.get('current_project_id')
        if not current_project_id:
            raise InvalidRequestException('No current project selected and no content provided')
        projects = env.get('projects', [])
        project = _find_project_by_id(projects, current_project_id)
        if not project:
            raise NotFoundException('Current project not found')
        content = project['content']
    if not content:
        raise InvalidRequestException('No content to check')
    result = _call_llm_for_text_check(content, 'spelling')
    return json.dumps({'success': True, 'check_type': 'spelling', 'result': result})


def CheckSpelling(content: str=None) -> str:
    """
    Check spelling in content using AI.
    
    Args:
        content: Optional content to check. If not provided, checks current project content
    """
    return _CheckSpelling(content=content)


def _CheckPunctuation(content: str=None):
    """
    Check punctuation in content using AI.
    
    Args:
        content: Optional content to check. If not provided, checks current project content
    """
    env = _read_env()
    if content is None or content == "":
        current_project_id = env.get('current_project_id')
        if not current_project_id:
            raise InvalidRequestException('No current project selected and no content provided')
        projects = env.get('projects', [])
        project = _find_project_by_id(projects, current_project_id)
        if not project:
            raise NotFoundException('Current project not found')
        content = project['content']
    if not content:
        raise InvalidRequestException('No content to check')
    result = _call_llm_for_text_check(content, 'punctuation')
    return json.dumps({'success': True, 'check_type': 'punctuation', 'result': result})


def CheckPunctuation(content: str=None) -> str:
    """
    Check punctuation in content using AI.
    
    Args:
        content: Optional content to check. If not provided, checks current project content
    """
    return _CheckPunctuation(content=content)


def _OptimizeRedundancy(content: str=None):
    """
    Check and optimize redundant expressions in content using AI.
    
    Args:
        content: Optional content to check. If not provided, checks current project content
    """
    env = _read_env()
    if content is None:
        current_project_id = env.get('current_project_id')
        if not current_project_id:
            raise InvalidRequestException('No current project selected and no content provided')
        projects = env.get('projects', [])
        project = _find_project_by_id(projects, current_project_id)
        if not project:
            raise NotFoundException('Current project not found')
        content = project['content']
    if not content:
        raise InvalidRequestException('No content to check')
    result = _call_llm_for_text_check(content, 'redundancy')
    return json.dumps({'success': True, 'check_type': 'redundancy', 'result': result})


def OptimizeRedundancy(content: str=None) -> str:
    """
    Check and optimize redundant expressions in content using AI.
    
    Args:
        content: Optional content to check. If not provided, checks current project content
    """
    return _OptimizeRedundancy(content=content)


def _OptimizeStyle(content: str=None):
    """
    Analyze and optimize writing style using AI.
    
    Args:
        content: Optional content to check. If not provided, checks current project content
    """
    env = _read_env()
    if content is None:
        current_project_id = env.get('current_project_id')
        if not current_project_id:
            raise InvalidRequestException('No current project selected and no content provided')
        projects = env.get('projects', [])
        project = _find_project_by_id(projects, current_project_id)
        if not project:
            raise NotFoundException('Current project not found')
        content = project['content']
    if not content:
        raise InvalidRequestException('No content to check')
    result = _call_llm_for_text_check(content, 'style')
    return json.dumps({'success': True, 'check_type': 'style', 'result': result})


def OptimizeStyle(content: str=None) -> str:
    """
    Analyze and optimize writing style using AI.
    
    Args:
        content: Optional content to check. If not provided, checks current project content
    """
    return _OptimizeStyle(content=content)


def _ExpandContent(content: str, requirements: str):
    """
    Expand content based on specific requirements using AI.
    
    Args:
        content: The content to expand
        requirements: Description of how to expand the content
    """
    if not content:
        raise InvalidRequestException('content cannot be empty')
    if not requirements:
        raise InvalidRequestException('requirements cannot be empty')
    result = _call_llm_for_expansion(content, requirements)
    return json.dumps({'success': True, 'result': result})


def ExpandContent(content: str, requirements: str) -> str:
    """
    Expand content based on specific requirements using AI.
    
    Args:
        content: The content to expand
        requirements: Description of how to expand the content
    """
    return _ExpandContent(content=content, requirements=requirements)


def _ScoreContent(content: str=None):
    """
    Score content across multiple dimensions using AI (readability, plot tension, character development, writing quality).
    
    Args:
        content: Optional content to score. If not provided, scores current project content
    """
    env = _read_env()
    if content is None:
        current_project_id = env.get('current_project_id')
        if not current_project_id:
            raise InvalidRequestException('No current project selected and no content provided')
        projects = env.get('projects', [])
        project = _find_project_by_id(projects, current_project_id)
        if not project:
            raise NotFoundException('Current project not found')
        content = project['content']
    if not content:
        raise InvalidRequestException('No content to score')
    result = _call_llm_for_scoring(content)
    return json.dumps({'success': True, 'result': result})


def ScoreContent(content: str=None) -> str:
    """
    Score content across multiple dimensions using AI (readability, plot tension, character development, writing quality).
    
    Args:
        content: Optional content to score. If not provided, scores current project content
    """
    return _ScoreContent(content=content)


def _GetWritingSuggestions(content: str=None):
    """
    Get AI-powered writing suggestions for content.
    
    Args:
        content: Optional content to analyze. If not provided, analyzes current project content
    """
    env = _read_env()
    if content is None or content == "":
        current_project_id = env.get('current_project_id')
        if not current_project_id:
            raise InvalidRequestException('No current project selected and no content provided')
        projects = env.get('projects', [])
        project = _find_project_by_id(projects, current_project_id)
        if not project:
            raise NotFoundException('Current project not found')
        content = project['content']
    if not content:
        raise InvalidRequestException('No content to analyze')
    result = _call_llm_for_suggestions(content)
    return json.dumps({'success': True, 'result': result})


def GetWritingSuggestions(content: str=None) -> str:
    """
    Get AI-powered writing suggestions for content.
    
    Args:
        content: Optional content to analyze. If not provided, analyzes current project content
    """
    return _GetWritingSuggestions(content=content)


def _RecordWritingTime(minutes: str, project_name: str=None):
    """
    Record writing time for a project.
    
    Args:
        minutes: Number of minutes spent writing
        project_name: Optional project name. If not provided, uses current project
    """
    try:
        minutes = int(minutes)
        if minutes <= 0:
            raise ValueError
    except (ValueError, TypeError):
        raise InvalidRequestException('minutes must be a positive integer')
    env = _read_env()
    projects = env.get('projects', [])
    if project_name:
        project = _find_project_by_name(projects, project_name)
        if not project:
            raise NotFoundException(f'Project "{project_name}" not found')
    else:
        current_project_id = env.get('current_project_id')
        if not current_project_id:
            raise InvalidRequestException('No current project selected')
        project = _find_project_by_id(projects, current_project_id)
        if not project:
            raise NotFoundException('Current project not found')
    project['writing_time_minutes'] = project.get('writing_time_minutes', 0) + minutes
    _write_env(env)
    total_time = project['writing_time_minutes']
    hours = total_time // 60
    remaining_minutes = total_time % 60
    return json.dumps({'success': True, 'project_name': project['project_name'], 'session_minutes': minutes, 'total_minutes': total_time, 'total_time_formatted': f'{hours}h {remaining_minutes}m'})


def RecordWritingTime(minutes: str, project_name: str=None) -> str:
    """
    Record writing time for a project.
    
    Args:
        minutes: Number of minutes spent writing
        project_name: Optional project name. If not provided, uses current project
    """
    return _RecordWritingTime(minutes=minutes, project_name=project_name)


def _GetWritingStatistics(project_name: str=None):
    """
    Get writing statistics for a project.
    
    Args:
        project_name: Optional project name. If not provided, uses current project
    """
    env = _read_env()
    projects = env.get('projects', [])
    if project_name:
        project = _find_project_by_name(projects, project_name)
        if not project:
            raise NotFoundException(f'Project "{project_name}" not found')
    else:
        current_project_id = env.get('current_project_id')
        if not current_project_id:
            raise InvalidRequestException('No current project selected')
        project = _find_project_by_id(projects, current_project_id)
        if not project:
            raise NotFoundException('Current project not found')
    total_time = project.get('writing_time_minutes', 0)
    hours = total_time // 60
    remaining_minutes = total_time % 60
    word_count = project.get('word_count', 0)
    words_per_hour = round(word_count / (total_time / 60)) if total_time > 0 else 0
    return json.dumps({'success': True, 'project_name': project['project_name'], 'word_count': word_count, 'total_writing_time_minutes': total_time, 'total_writing_time_formatted': f'{hours}h {remaining_minutes}m', 'words_per_hour': words_per_hour, 'created_at': project['created_at'], 'last_modified': project['last_modified']})


def GetWritingStatistics(project_name: str=None) -> str:
    """
    Get writing statistics for a project.
    
    Args:
        project_name: Optional project name. If not provided, uses current project
    """
    return _GetWritingStatistics(project_name=project_name)


def _CountWords(content: str=None):
    """
    Count words in content.
    
    Args:
        content: Optional content to count. If not provided, counts current project content
    """
    env = _read_env()
    if content is None:
        current_project_id = env.get('current_project_id')
        if not current_project_id:
            raise InvalidRequestException('No current project selected and no content provided')
        projects = env.get('projects', [])
        project = _find_project_by_id(projects, current_project_id)
        if not project:
            raise NotFoundException('Current project not found')
        content = project['content']
        project_name = project['project_name']
    else:
        project_name = None
    if not content:
        word_count = 0
    else:
        word_count = len(content.split())
    result = {'success': True, 'word_count': word_count, 'character_count': len(content) if content else 0, 'character_count_no_spaces': len(content.replace(' ', '')) if content else 0}
    if project_name:
        result['project_name'] = project_name
    return json.dumps(result)


def CountWords(content: str=None) -> str:
    """
    Count words in content.
    
    Args:
        content: Optional content to count. If not provided, counts current project content
    """
    return _CountWords(content=content)


