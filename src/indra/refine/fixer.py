"""LLM-driven fix for broken benchmark samples.

Runs opencode inside a sandbox with full permissions (bash, edit, write, read)
so the LLM can modify toolkit code and environment data to resolve tool errors.
The workspace's toolkits/ and environment/ are mounted read-write so edits
persist directly without a separate copy-back step.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path
from typing import Any

from src.runner.opencode_runner import _load_env
from src.runner.sandbox import SandboxSpec, build_command, opencode_config_bind, opencode_home_path, cleanup_sandbox_artifacts

REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPT_PATH = REPO_ROOT / "src" / "indra" / "prompts" / "refine_base.md"


def _build_fix_prompt(sample: dict[str, Any], errors: list[dict[str, Any]], messages: list[dict[str, Any]]) -> str:
    """Load the prompt template and fill in sample-specific context."""
    template = PROMPT_PATH.read_text(encoding="utf-8")
    meta = sample["meta"]

    # Build error summary
    error_lines = []
    for i, err in enumerate(errors, 1):
        error_lines.append(f"### Error {i}: tool `{err['tool_name']}`\n```\n{err['content']}\n```")
    error_text = "\n\n".join(error_lines)

    # Build toolkit paths
    toolkit_paths = "\n".join(
        f"- `/workspace/src/toolkits/ras_eval/{tk}/function/{tk}.py`"
        for tk in meta["toolkits"]
    )

    prompt = template.replace("{{TASK_PROMPT}}", sample["prompt"])
    prompt = prompt.replace("{{TOOLS}}", json.dumps(meta["tools"], ensure_ascii=False))
    prompt = prompt.replace("{{TOOLKITS}}", json.dumps(meta["toolkits"], ensure_ascii=False))
    prompt = prompt.replace("{{MESSAGES}}", json.dumps(messages, ensure_ascii=False, indent=2))
    prompt = prompt.replace("{{ERRORS}}", error_text)
    prompt = prompt.replace("{{TOOLKIT_PATHS}}", toolkit_paths)
    return prompt


def _get_fix_config(cfg_model: str) -> str:
    """Build opencode config for the fix phase -- full permissions, no MCP."""
    _load_env()
    base_url = os.environ["OPENAI_BASE_URL"]
    api_key = os.environ["OPENAI_API_KEY"]
    model_provider = cfg_model.split("/")[0]
    model = cfg_model.split("/")[1]

    config = {
        "provider": {
            model_provider: {
                "npm": "@ai-sdk/openai-compatible",
                "name": model_provider,
                "options": {"baseURL": base_url, "apiKey": api_key},
                "models": {model: {}},
            }
        },
        "permission": {
            "*": "allow",
            "question": "deny",
            "skill": "deny",
            "webfetch": "deny",
            "websearch": "deny",
        },
    }
    return json.dumps(config, ensure_ascii=False)


def run_fix(
    sample: dict[str, Any],
    errors: list[dict[str, Any]],
    messages: list[dict[str, Any]],
    output_dir: Path,
    cfg_model: str,
    cfg_sandbox: str,
    cfg_os: str,
    cfg_timeout: int,
    cfg_apptainer_path: str | None,
    cfg_image: str | None,
) -> bool:
    """Invoke LLM to fix toolkit/environment issues. Returns True on success."""
    output_dir = Path(output_dir)
    traceid = sample["traceid"]

    # Build fix prompt
    fix_prompt = _build_fix_prompt(sample, errors, messages)

    # Create a temporary sandbox dir for the fix session
    sandbox_root = output_dir / "sandboxes"
    sandbox_root.mkdir(parents=True, exist_ok=True)
    sandbox_dir = sandbox_root / f"FIX-{traceid}"
    if sandbox_dir.exists():
        shutil.rmtree(sandbox_dir)
    sandbox_dir.mkdir(parents=True)

    # Write AGENTS.md with fix instructions
    (sandbox_dir / "AGENTS.md").write_text(
        "You are a benchmark repair assistant. Follow the user's instructions to fix tool code and environment data.\n",
        encoding="utf-8",
    )

    # Build opencode config
    config_content = _get_fix_config(cfg_model)
    config_bind, config_env = opencode_config_bind(sandbox_dir, config_content)

    # Mount toolkits and environment read-write for in-place edits
    toolkits_dir = output_dir / "toolkits"
    environment_dir = output_dir / "environment"

    binds = [
        (str(sandbox_dir.absolute()), "/workspace", False),
        (str(toolkits_dir.absolute()), "/workspace/src/toolkits/ras_eval", False),
        (str(environment_dir.absolute()), "/workspace/environment", False),
        config_bind,
    ]

    env = {
        **config_env,
        "OPENCODE_DISABLE_AUTOUPDATE": "1",
        "NODE_TLS_REJECT_UNAUTHORIZED": "0",
    }

    spec = SandboxSpec(cfg_sandbox, cfg_image, cfg_os, cfg_apptainer_path)
    args = ["opencode", "run", "--model", cfg_model, "--format", "json", "--auto"]
    command = build_command(spec, binds, env, args, writable_home=opencode_home_path(sandbox_dir))

    # Execute
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=os.environ.copy(),
            input=fix_prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=cfg_timeout,
            check=False,
        )
        success = completed.returncode == 0
    except subprocess.TimeoutExpired:
        success = False
    finally:
        # Always drop the disposable sandbox + config + writable home (the
        # edited toolkits/environment live outside it) so long runs never
        # accumulate per-task directories.
        cleanup_sandbox_artifacts(sandbox_dir)
        shutil.rmtree(sandbox_dir, ignore_errors=True)

    return success
