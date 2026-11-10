import os
import json
import shutil
import shlex
from typing import Any, Dict, List

DATA_PATH = 'environment/reports/terminal.json'
INIT_PATH = 'environment/initial/terminal_init.json'

INIT = False


class InvalidRequestException(Exception):
    pass


class NotFoundException(Exception):
    pass


def _ensure_work_env():
    # Ensure working environment file exists by copying from init if necessary.
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
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_data(data: Dict[str, Any]):
    if not os.path.exists(os.path.dirname(DATA_PATH)):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)


def _new_history_entry(command: str, exit_code: int, output: str) -> Dict[str, Any]:
    return {'command': command, 'exit_code': exit_code, 'output': output}


def Execute(command: str) -> Dict[str, Any]:
    """Execute a terminal command and return the output.
    
    Args:
        command (str): The command string to execute in the terminal.
    """
    if not isinstance(command, str) or not command.strip():
        raise InvalidRequestException("The 'command' parameter is not valid.")
    cmd = command.strip()
    data = _load_data()
    cwd = data.get('cwd', '/')
    files: Dict[str, str] = data.get('files', {})
    history: List[Dict[str, Any]] = data.setdefault('history', [])

    try:
        parts = shlex.split(cmd)
    except Exception as exc:
        history.append(_new_history_entry(cmd, 1, f'Failed to parse command: {exc}'))
        _save_data(data)
        return {'output': f'Failed to parse command: {exc}', 'exit_code': 1}

    if not parts:
        raise InvalidRequestException("The 'command' parameter is not valid.")

    output = ''
    exit_code = 0
    base_cmd = parts[0]

    if base_cmd == 'pwd':
        output = cwd

    elif base_cmd == 'ls':
        path = parts[1] if len(parts) > 1 else '.'
        if path not in ['.', '']:
            output = f'ls: cannot access {path}: Not supported'
            exit_code = 1
        else:
            output = '\n'.join(sorted(files.keys()))

    elif base_cmd == 'cat':
        if len(parts) < 2:
            output = 'cat: missing file operand'
            exit_code = 1
        else:
            name = parts[1]
            if name not in files:
                output = f'cat: {name}: No such file'
                exit_code = 1
            else:
                output = files[name]

    elif base_cmd == 'touch':
        if len(parts) < 2:
            output = 'touch: missing file operand'
            exit_code = 1
        else:
            name = parts[1]
            files.setdefault(name, '')
            data['files'] = files
            _save_data(data)
            history.append(_new_history_entry(cmd, exit_code, output))
            return {'output': output, 'exit_code': exit_code}

    elif base_cmd == 'echo':
        if len(parts) < 2:
            output = ''
        else:
            if '>>' in parts or '>' in parts:
                if '>>' in parts:
                    idx = parts.index('>>')
                    append_mode = True
                else:
                    idx = parts.index('>')
                    append_mode = False
                if idx == len(parts) - 1:
                    output = 'echo: missing file operand'
                    exit_code = 1
                else:
                    text = ' '.join(parts[1:idx])
                    name = parts[idx + 1]
                    existing = files.get(name, '')
                    files[name] = existing + text if append_mode else text
                    data['files'] = files
                    _save_data(data)
                    output = text
                    history.append(_new_history_entry(cmd, exit_code, output))
                    return {'output': output, 'exit_code': exit_code}
            else:
                output = ' '.join(parts[1:])

    elif base_cmd == 'history':
        lines = [f"{i + 1} {item['command']}" for i, item in enumerate(history)]
        output = '\n'.join(lines)

    else:
        output = f"Unsupported command: {base_cmd}"
        exit_code = 1

    history.append(_new_history_entry(cmd, exit_code, output))
    data['files'] = files
    data['history'] = history
    _save_data(data)
    return {'output': output, 'exit_code': exit_code}
