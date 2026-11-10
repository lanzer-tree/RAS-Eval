"""ClawGuard CLI invoked by the opencode plugin.

``check``    gate a tool call: reads ``{"tool", "args"}`` JSON from stdin and the
             task scope from ``$CLAWGUARD_SCOPE_PATH``; exits 0 to allow, exits 2
             and prints the block reason to stdout to deny.
``sanitize`` redact secrets: reads text from stdin, writes the sanitized text to
             stdout.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.defense.clawguard.engine import decide, sanitize


def _load_scope() -> dict | None:
    path = os.environ.get("CLAWGUARD_SCOPE_PATH")
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as file:
        return json.load(file)


def main() -> None:
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "check":
        payload = json.loads(sys.stdin.read() or "{}")
        allowed, reason = decide(payload.get("tool", ""), payload.get("args") or {}, _load_scope())
        if allowed:
            sys.exit(0)
        sys.stdout.write(reason)
        sys.exit(2)
    if command == "sanitize":
        sys.stdout.write(sanitize(sys.stdin.read()))
        sys.exit(0)
    sys.stderr.write(f"unknown command: {command!r}\n")
    sys.exit(1)


if __name__ == "__main__":
    main()
