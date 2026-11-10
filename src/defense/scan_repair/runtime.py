"""scan_repair defense: run a subagent to repair tool/skill code before the task.

Before the main opencode agent runs, a standalone ``opencode run`` subagent
(same model) inspects the task-local tool/skill source and repairs data-leakage
risks in place, so the main agent then executes with the repaired code. The
repair must happen host-side before launch: cia-tool toolkits are mounted
read-only and imported by the MCP server at startup, so an in-session plugin
could not fix them.
"""
from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from src.runner.sandbox import SandboxSpec, build_command, local_state_path

PROMPT_PATH = Path(__file__).parent / "scan_repair_prompt.md"


def _config(model: str, base_url: str, api_key: str) -> str:
    provider, name = model.split("/", 1)
    config = {
        "provider": {
            provider: {
                "npm": "@ai-sdk/openai-compatible",
                "name": provider,
                "options": {"baseURL": base_url, "apiKey": api_key},
                "models": {name: {}},
            }
        },
        "permission": {
            "bash": "allow", "read": "allow", "grep": "allow", "glob": "allow",
            "edit": "allow", "write": "allow", "todowrite": "allow",
            "lsp": "deny", "patch": "deny", "skill": "deny", "webfetch": "deny",
            "websearch": "deny", "question": "deny", "task": "deny",
            "external_directory": {"*": "allow"}, "doom_loop": "allow",
        },
    }
    return json.dumps(config, ensure_ascii=False)


def _code_dir(sample: dict[str, Any], sandbox_dir: Path, toolkit_root: Path | None) -> Path | None:
    if sample["source"] == "skill_inject":
        return sandbox_dir / ".agents" / "skills"
    if sample["source"] == "ras-eval-next" and toolkit_root is not None:
        return Path(toolkit_root)
    return None


def run_scan_repair(
    sample: dict[str, Any],
    sandbox_dir: Path,
    spec: SandboxSpec,
    model: str,
    *,
    toolkit_root: Path | None,
    timeout: int,
) -> None:
    """Scan and repair the sample's task-local tool/skill code in place.

    No-op when there is no task-local code (e.g. toma/tpa). Fails open: a subagent
    timeout or error only warns, leaving the (unrepaired) code for the main run.
    """
    from src.runner.opencode_runner import _run_agent_command

    sandbox_dir = Path(sandbox_dir)
    code_dir = _code_dir(sample, sandbox_dir, toolkit_root)
    if code_dir is None or not code_dir.exists():
        return

    config_path = sandbox_dir.parent / f".scan_repair_config_{sandbox_dir.name}.json"
    config_path.write_text(_config(model, os.environ["OPENAI_BASE_URL"], os.environ["OPENAI_API_KEY"]), encoding="utf-8")
    home = local_state_path(sandbox_dir, "scan_repair_home")
    container_name = f"daedalus-scanrepair-{os.getpid()}-{sample['traceid']}" if spec.sandbox == "docker" else None
    binds = [
        (str(code_dir.absolute()), "/workspace", False),
        (str(config_path.absolute()), "/opencode.json", True),
    ]
    env = {
        "OPENCODE_CONFIG": "/opencode.json",
        "OPENCODE_DISABLE_AUTOUPDATE": "1",
        "NODE_TLS_REJECT_UNAUTHORIZED": "0",
    }
    command = build_command(
        spec, binds, env, ["opencode", "run", "--model", model, "--format", "json"],
        writable_home=home, name=container_name,
    )
    try:
        _, stderr, returncode, timed_out = _run_agent_command(
            command, os.environ.copy(), PROMPT_PATH.read_text(encoding="utf-8"), timeout, container_name,
        )
        if timed_out or returncode != 0:
            print(
                f"[WARN] traceid={sample['traceid']}: scan_repair subagent "
                f"{'timed out' if timed_out else f'exited {returncode}'}; "
                f"proceeding with code as-is.\n{stderr[-1000:]}"
            )
    finally:
        config_path.unlink(missing_ok=True)
        shutil.rmtree(home, ignore_errors=True)
