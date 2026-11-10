"""Single-sample inference execution for the flywheel refine pipeline.

Runs one sample inside a sandbox using opencode + MCP server, with toolkits
and environment loaded from the flywheel workspace (output_dir) rather than
the repository originals.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.runner.opencode_runner import parse_opencode_response, _load_env
from src.runner.sandbox import SandboxSpec, cleanup_sandbox_artifacts
from src.adapter.ras_eval_next import common as ras_eval_next_common

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class RefineConfig:
    input_path: Path
    output_dir: Path
    model: str
    sandbox: str
    os: str
    parallel: int = 1
    qps: float = 1.0
    traceid: int | None = None
    timeout: int = 900
    skip_exist_traceid: bool = False
    apptainer_path: str | None = None
    image: str | None = None
    api_key: str | None = None
    base_url: str | None = None
    # The base pipeline checks whether a task is solvable through its MCP tools
    # alone, so it denies opencode's native tools; attack refinement keeps them
    # enabled to match how ras-eval-next trajectories were annotated.
    disable_native_tools: bool = False


def _get_inference_config(sample: dict[str, Any], cfg: RefineConfig) -> str:
    """Build the opencode JSON config for running one refine sample."""
    _load_env()
    base_url = getattr(cfg, "base_url", None) or os.environ["OPENAI_BASE_URL"]
    api_key = getattr(cfg, "api_key", None) or os.environ["OPENAI_API_KEY"]
    model_provider, model = cfg.model.split("/", 1)
    source = sample["source"]
    if source != "ras-eval-next":
        raise NotImplementedError(f"refine inference is not supported for source={source}")

    server_path = "/app/src/adapter/ras_eval_next/ras_eval_mcp.py"
    mcp_name = "ras_eval_next"
    sample_json = json.dumps(ras_eval_next_common.clean_sample(sample), ensure_ascii=False)
    if cfg.disable_native_tools:
        permission = {
            "bash": "deny", "edit": "deny", "write": "deny", "read": "deny",
            "grep": "deny", "glob": "deny", "lsp": "deny", "patch": "deny",
            "skill": "deny", "todowrite": "deny", "webfetch": "deny",
            "websearch": "deny", "question": "deny", "task": "deny",
        }
    else:
        permission = {
            "bash": "allow", "edit": "allow", "write": "allow", "read": "allow",
            "grep": "allow", "glob": "allow", "patch": "allow", "todowrite": "allow",
            "lsp": "deny", "skill": "deny", "webfetch": "deny",
            "websearch": "deny", "question": "deny", "task": "deny",
        }
    # Unmatched permissions default to "ask" in opencode, and this run has no
    # ``--auto``: an ask is auto-rejected and aborts the session. ``doom_loop``
    # (same tool call three times) and ``external_directory`` match no entry
    # above, so allow them explicitly.
    permission.update({"external_directory": {"*": "allow"}, "doom_loop": "allow"})

    config = {
        "provider": {
            model_provider: {
                "npm": "@ai-sdk/openai-compatible",
                "name": model_provider,
                "options": {"baseURL": base_url, "apiKey": api_key},
                "models": {model: {}},
            }
        },
        "mcp": {
            mcp_name: {
                "type": "local",
                "command": ["python", server_path],
                "environment": {
                    "RAS_EVAL_SAMPLE_JSON": sample_json,
                    "PYTHONPATH": "/app",
                },
                "timeout": 300000,
                "enabled": True,
            }
        },
        "permission": permission,
    }
    return json.dumps(config, ensure_ascii=False)


def _get_api_keys() -> dict[str, str]:
    """Collect API keys from environment for forwarding into the sandbox."""
    _load_env()
    return {
        name: os.environ[name]
        for name in ras_eval_next_common.API_KEY_NAMES
        if os.environ.get(name)
    }


def run_inference(
    sample: dict[str, Any],
    output_dir: Path,
    cfg: RefineConfig,
    keep_sandbox: bool = False,
) -> tuple[list[dict[str, Any]], str, str] | tuple[list[dict[str, Any]], str, str, Path]:
    """Run one sample and return messages/stdout/stderr.

    When ``keep_sandbox`` is true, the per-task sandbox is left on disk and
    returned as the fourth item so the caller can run environment-aware LTL
    verification before deleting it.
    """
    output_dir = Path(output_dir)
    traceid = sample["traceid"]
    source = sample["source"]

    sandbox_root = output_dir / "sandboxes"
    sandbox_root.mkdir(parents=True, exist_ok=True)
    sandbox_dir = sandbox_root / f"TASK-{traceid}"
    if sandbox_dir.exists():
        shutil.rmtree(sandbox_dir)
    sandbox_dir.mkdir(parents=True)
    shutil.copytree(output_dir / "environment", sandbox_dir / "environment")

    system_prompt = sample["meta"].get("system_prompt", "")
    if system_prompt:
        (sandbox_dir / "AGENTS.md").write_text(system_prompt + "\n", encoding="utf-8")

    spec = SandboxSpec(cfg.sandbox, cfg.image, cfg.os, cfg.apptainer_path)
    config_content = _get_inference_config(sample, cfg)
    api_keys = _get_api_keys()

    if source == "ras-eval-next":
        try:
            from src.indra.generate.redteam_server import ensure_started as ensure_redteam_server

            ensure_redteam_server()
            toolkit_root = output_dir / "toolkits"
            check_command = ras_eval_next_common.build_mcp_check_command(
                spec,
                sandbox_dir,
                sample,
                api_keys,
                toolkit_root=toolkit_root,
            )
            check = subprocess.run(
                check_command,
                cwd=REPO_ROOT,
                env=os.environ.copy(),
                input="",
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=min(cfg.timeout, 300),
                check=False,
            )
            if check.returncode != 0:
                raise RuntimeError(
                    "ras-eval-next MCP server failed to start for traceid "
                    f"{traceid} (exit={check.returncode}).\n"
                    f"--- stderr ---\n{check.stderr}\n--- stdout ---\n{check.stdout}"
                )
            command = ras_eval_next_common.build_agent_command(
                spec,
                sandbox_dir,
                config_content,
                cfg.model,
                api_keys,
                toolkit_root=toolkit_root,
            )
            tool_providers = ["ras_eval_next"]
        except Exception:
            cleanup_sandbox_artifacts(sandbox_dir)
            shutil.rmtree(sandbox_dir, ignore_errors=True)
            raise
    else:
        cleanup_sandbox_artifacts(sandbox_dir)
        shutil.rmtree(sandbox_dir, ignore_errors=True)
        raise NotImplementedError(f"refine inference is not supported for source={source}")

    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=os.environ.copy(),
            input=sample["prompt"],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=cfg.timeout,
            check=False,
        )
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        stderr = f"Timed out after {cfg.timeout} seconds.\n{stderr}"
    finally:
        cleanup_sandbox_artifacts(sandbox_dir)
        if not keep_sandbox:
            shutil.rmtree(sandbox_dir, ignore_errors=True)

    try:
        messages = parse_opencode_response(sample, tool_providers, stdout, stderr, 0)
        if source == "ras-eval-next":
            messages = ras_eval_next_common.normalize_messages(sample["meta"], messages)
    except Exception:
        messages = [{"role": "user", "content": sample["prompt"]}]

    if keep_sandbox:
        return messages, stdout, stderr, sandbox_dir
    return messages, stdout, stderr
