from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.adapter.hermes.common import (
    TRACE_FILENAME,
    cleanup_hermes_home,
    prepare_hermes_home,
    read_trace,
)
from src.adapter.ras_eval_next import common as ras_eval_next_common
from src.adapter.skill_inject import common as skill_inject_common
from src.runner.framework_runner import api_keys, prepare_sandbox
from src.runner.opencode_runner import REPO_ROOT, RateLimiter, RunnerConfig, _load_env, _run_agent_command
from src.runner.sandbox import SandboxSpec, build_command, mcp_sample_path, opencode_home_path


SPEC_KEYS = ("completion_specifications", "safety_specifications", "security_specifications")


def _clean_sample(sample: dict[str, Any]) -> dict[str, Any]:
    meta = {key: value for key, value in (sample.get("meta") or {}).items() if key not in SPEC_KEYS}
    return {**sample, "meta": meta}


def _root_file_binds(sandbox_dir: Path) -> list[tuple[str, str, bool]]:
    root = sandbox_dir / "_root_files"
    if not root.exists():
        return []
    return [(str(path.absolute()), f"/{path.name}", True) for path in root.iterdir()]


def _build_command(
    sample: dict[str, Any],
    config: RunnerConfig,
    sandbox_dir: Path,
    toolkit_root: Path | None,
    container_name: str,
    hermes_home: Path,
    toolsets: list[str],
) -> list[str]:
    sample_file = mcp_sample_path(sandbox_dir)
    sample_file.write_text(json.dumps(_clean_sample(sample), ensure_ascii=False), encoding="utf-8")
    binds = [
        (str(sandbox_dir.absolute()), "/workspace", False),
        (str((REPO_ROOT / "src").absolute()), "/app/src", True),
        (str(sample_file.absolute()), "/sample.json", True),
        (str(hermes_home.absolute()), "/hermes-home", False),
        *_root_file_binds(sandbox_dir),
    ]
    if toolkit_root is not None:
        binds.append((str(Path(toolkit_root).absolute()), "/app/src/toolkits/ras_eval", True))
    if config.runtime_verification:
        from src.evaluator.spec.observe import NUXMV_LINUX_DIR
        from src.evaluator.spec.runtime import runtime_dir_for

        binds.extend([
            (str(runtime_dir_for(sandbox_dir).absolute()), "/runtime_verification", False),
            (str(NUXMV_LINUX_DIR.absolute()), "/opt/nuXmv", True),
        ])
    env = {
        "PYTHONPATH": "/app",
        "HERMES_HOME": "/hermes-home",
        "HERMES_YOLO_MODE": "1",
        "HERMES_ACCEPT_HOOKS": "1",
        "TMPDIR": "/hermes-home/tmp",
        "TMP": "/hermes-home/tmp",
        "TEMP": "/hermes-home/tmp",
        "RAS_EVAL_SAMPLE_PATH": "/sample.json",
        "RAS_EVAL_WORKDIR": "/workspace",
        "RAS_EVAL_ENV_REPLAY_REPORT": "/workspace/.env_replay_warnings.json",
        "DAEDALUS_TRACE_PATH": f"/workspace/{TRACE_FILENAME}",
        "NODE_TLS_REJECT_UNAUTHORIZED": "0",
        **({
            "DAEDALUS_RUNTIME_REQUEST": "/runtime_verification/request.json",
            "DAEDALUS_RUNTIME_STATE": "/runtime_verification/state.json",
            "DAEDALUS_RUNTIME_LOCK": "/runtime_verification/lock",
        } if config.runtime_verification else {}),
        **api_keys(),
    }
    if sample.get("source") == "skill_inject":
        env["BASH_ENV"] = "/workspace/.bash_command_logger.sh"
    args = [
        "/usr/local/lib/hermes-agent/venv/bin/python",
        "/app/src/adapter/hermes/entry.py",
        "chat",
        "--query-file",
        "-",
        "--model",
        config.model,
        "--provider",
        "custom",
        "--toolsets",
        ",".join(toolsets),
        "--quiet",
        "--yolo",
        "--source",
        "tool",
        "--in",
        "/workspace",
        "--max-turns",
        "90",
        "--run-budget",
        str(max(1, config.timeout - 30)),
    ]
    spec = SandboxSpec(config.sandbox, config.image, config.os, config.apptainer_path)
    return build_command(
        spec,
        binds,
        env,
        args,
        writable_home=opencode_home_path(sandbox_dir),
        name=container_name,
    )


def run_sample(sample: dict[str, Any], config: RunnerConfig, limiter: RateLimiter) -> dict[str, Any]:
    """Run one task through the native Hermes CLI and preserve partial artifacts."""
    _load_env()
    traceid = sample["traceid"]
    source = sample["source"]
    meta = sample.get("meta") or {}
    sandbox_dir: Path | None = None
    toolkit_root: Path | None = None
    hermes_home: Path | None = None
    stdout = ""
    stderr = ""
    try:
        try:
            from src.indra.generate.redteam_server import ensure_started as ensure_redteam_server

            if meta.get("attack_type") or meta.get("security_specifications"):
                ensure_redteam_server()
        except Exception as exc:
            print(f"[WARN] traceid={traceid}: redteam server startup skipped ({type(exc).__name__}: {exc})")

        sandbox_dir, toolkit_root = prepare_sandbox(sample, config)
        if source == "skill_inject":
            (sandbox_dir / ".bash_command_logger.sh").write_text(
                "trap 'echo \"$BASH_COMMAND\" >> /workspace/.command_history' DEBUG\n",
                encoding="utf-8",
            )
        if config.runtime_verification:
            from src.evaluator.spec.runtime import prepare_runtime_dir

            prepare_runtime_dir(sample, sandbox_dir)
        keys = api_keys()
        hermes_home, toolsets = prepare_hermes_home(sample, sandbox_dir, config.model, keys)

        if source == "ras-eval-next":
            spec = SandboxSpec(config.sandbox, config.image, config.os, config.apptainer_path)
            preflight = ras_eval_next_common.build_mcp_check_command(
                spec,
                sandbox_dir,
                sample,
                keys,
                toolkit_root=toolkit_root,
            )
            check_stdout, check_stderr, check_code, check_timeout = _run_agent_command(
                preflight,
                os.environ.copy(),
                "",
                min(config.timeout, 300),
            )
            if check_timeout or check_code != 0:
                raise RuntimeError(
                    f"ras-eval-next MCP server failed to start for Hermes traceid {traceid} "
                    f"(exit={check_code}, timeout={check_timeout}).\n"
                    f"--- stderr ---\n{check_stderr[-4000:]}\n--- stdout ---\n{check_stdout[-4000:]}"
                )

        container_name = f"daedalus-hermes-{os.getpid()}-{traceid}"
        command = _build_command(
            sample,
            config,
            sandbox_dir,
            toolkit_root,
            container_name,
            hermes_home,
            toolsets,
        )
        limiter.wait()
        stdout, stderr, returncode, timed_out = _run_agent_command(
            command,
            os.environ.copy(),
            str(sample.get("prompt") or ""),
            config.timeout,
            container_name if config.sandbox == "docker" else None,
        )
        messages = read_trace(sandbox_dir / TRACE_FILENAME)
        if not messages:
            raise RuntimeError(
                f"Hermes produced no trace for traceid {traceid}.\n"
                f"--- stderr ---\n{stderr[-4000:]}\n--- stdout ---\n{stdout[-4000:]}"
            )
        if timed_out:
            print(
                f"[WARN] traceid={traceid}: Hermes timed out after {config.timeout}s; "
                "keeping the partial trajectory and runtime verification history."
            )
        elif returncode != 0:
            print(
                f"[WARN] traceid={traceid}: Hermes exited with code {returncode}; "
                "keeping the partial trajectory and runtime verification history."
            )

        if source == "ras-eval-next":
            messages = ras_eval_next_common.normalize_messages({**meta, "system_prompt": ""}, messages)
        else:
            (sandbox_dir / "agent_stdout.txt").write_text(
                skill_inject_common.render_transcript([message for message in messages if message.get("role") != "system"]),
                encoding="utf-8",
            )
            if stderr:
                (sandbox_dir / "agent_stderr.txt").write_text(stderr, encoding="utf-8")

        row: dict[str, Any] = {"traceid": traceid, "framework": "hermes", "response": messages}
        if timed_out:
            row["timeout"] = True
            row["timeout_seconds"] = config.timeout
        elif returncode != 0:
            row["agent_exit_code"] = returncode
        if stderr:
            row["stderr_tail"] = stderr[-4000:]
        return row
    finally:
        if sandbox_dir is not None:
            cleanup_hermes_home(sandbox_dir)
