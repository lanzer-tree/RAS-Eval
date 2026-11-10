"""Python equivalents of the harness's native computer-use tools.

The first seven tools cover the computer-use capabilities an agent harness
exposes on its own (bash / edit / write / read / grep / glob / webfetch). They
are plain functions -- exactly like every other toolkit here -- and all file I/O
is relative to the current working directory (the mounted ``/workspace`` sandbox
inside the container), so it can never touch the host.

``skill`` / ``todowrite`` / ``task`` are the harness-private tools that show up in
opencode trajectories. They are *not* exposed to agents; they exist so the trace
program modeling (``src/defense/sast/modeling``) can resolve those calls to real
code instead of uninterpreted functions -- ``skill`` in particular carries the
SKILL.md instruction file into the agent context, which is where skill-injection
attacks live.
"""
from __future__ import annotations

import glob as _glob
import json
import os
import re
import subprocess
import urllib.request


def bash(command: str = "", timeout: int = 120) -> dict:
    """Run a shell command in the current working directory and capture its output.

    Args:
        command (str): The shell command to execute.
        timeout (int): Maximum seconds to wait before killing the command.

    Returns:
        dict: success status, stdout, stderr and the process return code.
    """
    if not command:
        return {"success": False, "description": "command is required."}
    try:
        completed = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return {"success": False, "description": f"Command timed out after {timeout}s."}
    except Exception as error:
        return {"success": False, "description": f"Error: {error}"}
    return {
        "success": completed.returncode == 0,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
    }


def read(file_path: str = "", offset: int = 0, limit: int = 2000) -> dict:
    """Read a text file and return its lines.

    Args:
        file_path (str): Path of the file to read.
        offset (int): Zero-based line index to start reading from.
        limit (int): Maximum number of lines to return.

    Returns:
        dict: success status and the file content (or an error description).
    """
    if not file_path:
        return {"success": False, "description": "file_path is required."}
    if offset is None:
        offset = 0
    if limit is None:
        limit = 2000
    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            lines = file.readlines()
    except Exception as error:
        return {"success": False, "description": f"Error: {error}"}
    selected = lines[offset : offset + limit]
    return {"success": True, "content": "".join(selected), "num_lines": len(lines)}


def write(file_path: str = "", content: str = "") -> dict:
    """Write text to a file, creating parent directories and overwriting any existing content.

    Args:
        file_path (str): Path of the file to write.
        content (str): The full text content to write.

    Returns:
        dict: success status and description.
    """
    if not file_path:
        return {"success": False, "description": "file_path is required."}
    try:
        parent = os.path.dirname(file_path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
    except Exception as error:
        return {"success": False, "description": f"Error: {error}"}
    return {"success": True, "description": f"Wrote {len(content)} characters to {file_path}."}


def edit(file_path: str = "", old_string: str = "", new_string: str = "", replace_all: bool = False) -> dict:
    """Replace an exact string in a file with a new string.

    Args:
        file_path (str): Path of the file to edit.
        old_string (str): The exact text to replace.
        new_string (str): The replacement text.
        replace_all (bool): Replace every occurrence instead of requiring a unique match.

    Returns:
        dict: success status and description.
    """
    if not file_path:
        return {"success": False, "description": "file_path is required."}
    if old_string == "":
        return {"success": False, "description": "old_string is required."}
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()
    except Exception as error:
        return {"success": False, "description": f"Error: {error}"}
    count = text.count(old_string)
    if count == 0:
        return {"success": False, "description": "old_string not found in file."}
    if count > 1 and not replace_all:
        return {"success": False, "description": f"old_string is not unique ({count} matches); set replace_all=True."}
    text = text.replace(old_string, new_string) if replace_all else text.replace(old_string, new_string, 1)
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(text)
    except Exception as error:
        return {"success": False, "description": f"Error: {error}"}
    return {"success": True, "description": f"Replaced {count if replace_all else 1} occurrence(s)."}


def grep(pattern: str = "", path: str = ".", glob: str = "*", include: str = "") -> dict:
    """Search file contents for a regular expression.

    Args:
        pattern (str): The regular expression to search for.
        path (str): Directory (searched recursively) or single file to search.
        glob (str): Filename glob used to filter files when path is a directory.
        include (str): Alias for glob (filename glob used to filter files).

    Returns:
        dict: success status and the list of matching "file:line: text" strings.
    """
    if not pattern:
        return {"success": False, "description": "pattern is required."}
    if path is None:
        path = "."
    if include:
        glob = include
    if glob is None:
        glob = "*"
    try:
        regex = re.compile(pattern)
    except re.error as error:
        return {"success": False, "description": f"Invalid pattern: {error}"}
    if os.path.isfile(path):
        candidates = [path]
    else:
        candidates = set()
        for g in _expand_braces(glob):
            candidates.update(p for p in _glob.glob(os.path.join(path, "**", g), recursive=True) if os.path.isfile(p))
        candidates = sorted(candidates)
    matches = []
    for candidate in candidates:
        try:
            with open(candidate, "r", encoding="utf-8", errors="replace") as file:
                for number, line in enumerate(file, 1):
                    if regex.search(line):
                        matches.append(f"{candidate}:{number}: {line.rstrip()}")
        except Exception:
            continue
    return {"success": True, "matches": matches, "count": len(matches)}


def _expand_braces(pattern: str) -> list:
    """Expand brace patterns like ``{a,b,c}`` into multiple patterns."""
    brace = re.compile(r"\{([^{}]+)\}")
    results = [pattern]
    while True:
        expanded = []
        for cur in results:
            m = brace.search(cur)
            if m:
                options = m.group(1).split(",")
                for opt in options:
                    expanded.append(cur[: m.start()] + opt + cur[m.end() :])
            else:
                expanded.append(cur)
        if expanded == results:
            break
        results = expanded
    return results


def glob(pattern: str = "**/*", path: str = ".") -> dict:
    """Find files whose paths match a glob pattern.

    Args:
        pattern (str): The glob pattern (e.g. "**/*.py").
        path (str): The base directory to search from.

    Returns:
        dict: success status and the list of matching file paths.
    """
    if pattern is None:
        pattern = "**/*"
    if path is None:
        path = "."
    try:
        results = set()
        for pat in _expand_braces(pattern):
            results.update(p for p in _glob.glob(os.path.join(path, pat), recursive=True))
        results = sorted(results)
    except Exception as error:
        return {"success": False, "description": f"Error: {error}"}
    return {"success": True, "files": results, "count": len(results)}


def webfetch(url: str = "", timeout: int = 30, max_chars: int = 8000) -> dict:
    """Fetch a URL over HTTP(S) and return its (truncated) text content.

    Args:
        url (str): The URL to fetch.
        timeout (int): Maximum seconds to wait for the response.
        max_chars (int): Maximum number of characters of the body to return.

    Returns:
        dict: success status, HTTP status code and the response body text.
    """
    if not url:
        return {"success": False, "description": "url is required."}
    try:
        max_chars = int(max_chars)
    except (TypeError, ValueError):
        max_chars = 8000
    try:
        timeout = int(timeout)
    except (TypeError, ValueError):
        timeout = 30
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={"User-Agent": "ras-eval-agent"})
            current_timeout = timeout * (2 ** attempt)
            with urllib.request.urlopen(request, timeout=current_timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
                status = response.status
            return {"success": True, "status": status, "content": body[:max_chars]}
        except Exception as error:
            if attempt == 2:
                return {"success": False, "description": f"Error: {error}"}
    return {"success": False, "description": "Error: unexpected"}


# --------------------------------------------------------------------------- #
# Harness-private tools (not exposed to agents; used by the trace modeling)   #
# --------------------------------------------------------------------------- #
SKILLS_DIR = os.path.join(".agents", "skills")

_TODOS: list = []


def skill(name: str = "") -> dict:
    """Load a skill: return the SKILL.md instructions of ``.agents/skills/<name>``.

    The returned instructions go straight into the agent's context, so this file
    is untrusted input for everything the agent does afterwards.

    Args:
        name (str): The skill name, i.e. its directory under .agents/skills.

    Returns:
        dict: success status, the skill directory and its SKILL.md instructions.
    """
    if not name:
        return {"success": False, "description": "name is required."}
    directory = os.path.join(SKILLS_DIR, name)
    manifest = os.path.join(directory, "SKILL.md")
    try:
        with open(manifest, "r", encoding="utf-8", errors="replace") as file:
            instructions = file.read()
    except Exception as error:
        return {"success": False, "description": f"Error: {error}"}
    scripts = sorted(_glob.glob(os.path.join(directory, "**", "*"), recursive=True))
    return {"success": True, "directory": directory, "instructions": instructions, "files": scripts}


def todowrite(todos: list = None) -> dict:
    """Replace the session's todo list with ``todos`` (pure agent bookkeeping).

    Args:
        todos (list): The new todo list; every item carries content and status.

    Returns:
        dict: success status and the stored todo list.
    """
    global _TODOS
    if todos is None:
        return {"success": True, "todos": list(_TODOS)}
    _TODOS = json.loads(todos) if isinstance(todos, str) else list(todos)
    return {"success": True, "todos": list(_TODOS)}


def task(description: str = "", prompt: str = "", subagent_type: str = "general") -> dict:
    """Hand ``prompt`` to a nested agent and return its final report.

    Only the argument data flow is modeled: the nested agent runs its own
    trajectory, which is not part of this one, so from this program's point of
    view the call may perform any tool call the parent agent could perform. Treat
    the return value as untrusted and the side effects as unbounded.

    Args:
        description (str): Short description of the delegated task.
        prompt (str): The full instruction handed to the nested agent.
        subagent_type (str): Which subagent runs the task.

    Returns:
        dict: success status and the nested agent's report text.
    """
    if not prompt:
        return {"success": False, "description": "prompt is required."}
    return {"success": True, "subagent_type": subagent_type, "description": description, "report": prompt}
