"""Error detection from inference response traces.

Scans tool output messages for keywords indicating Python exceptions or errors,
which signal that the benchmark sample quality is poor and needs refinement.
"""
from __future__ import annotations

import re
from typing import Any

# Patterns that indicate a tool call failure (case-sensitive to avoid false
# positives like "Error handling" in normal text).
_ERROR_PATTERNS = [
    re.compile(r"\w*Exception\s*[:(\[]"),   # e.g. InvalidRequestException: ...
    re.compile(r"\w*Error\s*[:(\[]"),        # e.g. TypeError: ...
    re.compile(r"Traceback \(most recent"),  # Python traceback header
]


def check_errors(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return a list of detected errors from tool output messages.

    Each entry: {"tool_name": str, "content": str, "index": int}
    Empty list means no errors detected -- sample does not need refinement.
    """
    errors: list[dict[str, Any]] = []
    for idx, msg in enumerate(messages):
        if msg.get("role") != "tool":
            continue
        content = msg.get("content", "")
        if not isinstance(content, str):
            content = str(content)
        for pattern in _ERROR_PATTERNS:
            if pattern.search(content):
                errors.append({
                    "tool_name": msg.get("name", "unknown"),
                    "content": content,
                    "index": idx,
                })
                break  # one match per message is enough
    return errors
