from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.adapter.openclaw.common import (
    TRACE_FILENAME,
    append_assistant,
    cleanup_openclaw_state,
    initialize_trace,
    prepare_openclaw_state,
    read_trace,
    split_model,
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
    return [(str(path.absolute()), f"/{path.name}", True) for path in root.iterdir() if path.is_file()]


def _build_command(
    sample: dict[str, Any],
    config: RunnerConfig,
    sandbox_dir: Path,
    toolkit_root: Path | None,
    container_name: str,
    state_dir: Path,
) -> list[str]:
    sample_file = mcp_sample_path(sandbox_dir)
    sample_file.write_text(json.dumps(_clean_sample(sample), ensure_ascii=False), encoding="utf-8")
    binds = [
        (str(sandbox_dir.absolute()), "/workspace", False),
        (str((REPO_ROOT / "src").absolute()), "/app/src", True),
        (str(sample_file.absolute()), "/sample.json", True),
        (str(state_dir.absolute()), "/openclaw-state", False),
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
        "RAS_EVAL_SAMPLE_PATH": "/sample.json",
        "RAS_EVAL_WORKDIR": "/workspace",
        "RAS_EVAL_ENV_REPLAY_REPORT": "/workspace/.env_replay_warnings.json",
        "DAEDALUS_TRACE_PATH": f"/workspace/{TRACE_FILENAME}",
        "OPENCLAW_HOME": "/openclaw-state/home",
        "OPENCLAW_STATE_DIR": "/openclaw-state/state",
        "OPENCLAW_CONFIG_PATH": "/openclaw-state/openclaw.json",
        "OPENCLAW_WORKSPACE_DIR": "/workspace",
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
    provider, model_id = split_model(config.model)
    args = [
        "openclaw",
        "agent",
        "--local",
        "--agent",
        "main",
        "--model",
        f"{provider}/{model_id}",
        "--timeout",
        str(max(1, config.timeout - 30)),
        "--json",
        "--message-file",
        "/openclaw-state/prompt.txt",
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


def _json_envelope(stdout: str) -> dict[str, Any] | None:
    candidates = [stdout.strip(), *reversed(stdout.splitlines())]
    for text in candidates:
        if not text.strip():
            continue
        try:
            value = json.loads(text)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None


def _final_text(envelope: dict[str, Any] | None) -> str:
    if not envelope:
        return ""
    if envelope.get("final"):
        return str(envelope["final"])
    texts = [
        str(payload.get("text"))
        for payload in (envelope.get("payloads") or [])
        if isinstance(payload, dict) and payload.get("text") and not payload.get("isReasoning")
    ]
    return "\n".join(texts)


def _envelope_timed_out(envelope: dict[str, Any] | None) -> bool:
    """Detect OpenClaw's successful-process envelope for an agent timeout."""
    if not envelope:
        return False
    meta = envelope.get("meta")
    if isinstance(meta, dict):
        if meta.get("timeoutPhase"):
            return True
        error = meta.get("error")
        if isinstance(error, dict) and error.get("kind") == "incomplete_turn":
            return "timed out" in str(error.get("message", "")).lower()
    return any(
        isinstance(payload, dict)
        and payload.get("isError") is True
        and "timed out before a response was generated" in str(payload.get("text", "")).lower()
        for payload in (envelope.get("payloads") or [])
    )


def run_sample(sample: dict[str, Any], config: RunnerConfig, limiter: RateLimiter) -> dict[str, Any]:
    """Run one isolated embedded OpenClaw turn and preserve partial trace artifacts."""
    _load_env()
    traceid = sample["traceid"]
    source = sample["source"]
    meta = sample.get("meta") or {}
    sandbox_dir: Path | None = None
    state_dir: Path | None = None
    stdout = ""
    stderr = ""
    returncode = 1
    timed_out = False
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
        trace_path = sandbox_dir / TRACE_FILENAME
        initialize_trace(trace_path, sample)
        state_dir = prepare_openclaw_state(sample, sandbox_dir, config.model)

        if source == "ras-eval-next":
            spec = SandboxSpec(config.sandbox, config.image, config.os, config.apptainer_path)
            check = ras_eval_next_common.build_mcp_check_command(
                spec,
                sandbox_dir,
                sample,
                api_keys(),
                toolkit_root=toolkit_root,
            )
            check_stdout, check_stderr, check_code, check_timeout = _run_agent_command(
                check,
                os.environ.copy(),
                "",
                min(config.timeout, 300),
            )
            if check_timeout or check_code != 0:
                stderr = (
                    f"ras-eval-next MCP preflight failed (exit={check_code}, timeout={check_timeout}).\n"
                    f"{check_stderr[-4000:]}\n{check_stdout[-4000:]}"
                )
                returncode = check_code or 1
            else:
                container_name = f"daedalus-openclaw-{os.getpid()}-{traceid}"
                command = _build_command(sample, config, sandbox_dir, toolkit_root, container_name, state_dir)
                limiter.wait()
                stdout, stderr, returncode, timed_out = _run_agent_command(
                    command,
                    os.environ.copy(),
                    None,
                    config.timeout,
                    container_name if config.sandbox == "docker" else None,
                )
        else:
            container_name = f"daedalus-openclaw-{os.getpid()}-{traceid}"
            command = _build_command(sample, config, sandbox_dir, toolkit_root, container_name, state_dir)
            limiter.wait()
            stdout, stderr, returncode, timed_out = _run_agent_command(
                command,
                os.environ.copy(),
                None,
                config.timeout,
                container_name if config.sandbox == "docker" else None,
            )

        envelope = _json_envelope(stdout)
        timed_out = timed_out or _envelope_timed_out(envelope)
        append_assistant(trace_path, _final_text(envelope))
        messages = read_trace(trace_path)
        if source == "ras-eval-next":
            messages = ras_eval_next_common.normalize_messages({**meta, "system_prompt": ""}, messages)
        else:
            (sandbox_dir / "agent_stdout.txt").write_text(
                skill_inject_common.render_transcript([message for message in messages if message.get("role") != "system"]),
                encoding="utf-8",
            )
            if stderr:
                (sandbox_dir / "agent_stderr.txt").write_text(stderr, encoding="utf-8")

        row: dict[str, Any] = {"traceid": traceid, "framework": "openclaw", "response": messages}
        if timed_out:
            row["timeout"] = True
            row["timeout_seconds"] = config.timeout
            print(
                f"[WARN] traceid={traceid}: OpenClaw timed out after {config.timeout}s; "
                "keeping the partial trajectory and runtime verification history."
            )
        elif returncode != 0:
            row["agent_exit_code"] = returncode
            print(
                f"[WARN] traceid={traceid}: OpenClaw exited with code {returncode}; "
                "keeping the partial trajectory and runtime verification history."
            )
        if stderr:
            row["stderr_tail"] = stderr[-4000:]
        return row
    finally:
        if sandbox_dir is not None:
            cleanup_openclaw_state(sandbox_dir)
