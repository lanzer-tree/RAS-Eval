from __future__ import annotations

import json
import os
import shutil
from pathlib import Path
from typing import Any

from src.adapter.ras_eval_next import common as ras_eval_next_common
from src.adapter.skill_inject import common as skill_inject_common
from src.runner.opencode_runner import REPO_ROOT, RateLimiter, RunnerConfig, _load_env, _run_agent_command
from src.runner.sandbox import SandboxSpec, build_command, cleanup_sandbox_artifacts, mcp_sample_path, opencode_home_path


SPEC_KEYS = ("completion_specifications", "safety_specifications", "security_specifications")
REQUEST_CONTROLLED_FRAMEWORKS = frozenset({"autogen", "mcp", "langchain"})


def _clean_sample(sample: dict[str, Any]) -> dict[str, Any]:
    meta = {key: value for key, value in sample.get("meta", {}).items() if key not in SPEC_KEYS}
    return {**sample, "meta": meta}


def _request_control_env(config: RunnerConfig) -> dict[str, str]:
    if config.framework not in REQUEST_CONTROLLED_FRAMEWORKS:
        return {}
    env: dict[str, str] = {}
    if config.request_qps is not None:
        env["RAS_EVAL_REQUEST_QPS"] = str(config.request_qps / max(1, config.parallel))
    if config.request_max_retries is not None:
        env["RAS_EVAL_REQUEST_MAX_RETRIES"] = str(config.request_max_retries)
    return env


def api_keys() -> dict[str, str]:
    names = ("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_API_BASE", *ras_eval_next_common.API_KEY_NAMES)
    return {name: os.environ[name] for name in names if os.environ.get(name)}


def _trace_messages(trace_path: Path) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = []
    if not trace_path.exists():
        return messages
    for line in trace_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            messages.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"[WARN] skipping unparsable framework trace line: {line[:200]}")
    return messages


def _build_command(
    sample: dict[str, Any],
    config: RunnerConfig,
    sandbox_dir: Path,
    toolkit_root: Path | None,
    container_name: str,
) -> list[str]:
    sample_file = mcp_sample_path(sandbox_dir)
    sample_file.write_text(json.dumps(_clean_sample(sample), ensure_ascii=False), encoding="utf-8")
    binds = [
        (str(sandbox_dir.absolute()), "/workspace", False),
        (str((REPO_ROOT / "src").absolute()), "/app/src", True),
        (str(sample_file.absolute()), "/sample.json", True),
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
        "RAS_EVAL_FRAMEWORK": config.framework,
        "RAS_EVAL_SAMPLE_PATH": "/sample.json",
        "RAS_EVAL_WORKDIR": "/workspace",
        "RAS_EVAL_MODEL": config.model,
        "RAS_EVAL_ENV_REPLAY_REPORT": "/workspace/.env_replay_warnings.json",
        "NODE_TLS_REJECT_UNAUTHORIZED": "0",
        **({
            "DAEDALUS_RUNTIME_REQUEST": "/runtime_verification/request.json",
            "DAEDALUS_RUNTIME_STATE": "/runtime_verification/state.json",
            "DAEDALUS_RUNTIME_LOCK": "/runtime_verification/lock",
        } if config.runtime_verification else {}),
        **_request_control_env(config),
        **api_keys(),
    }
    if env.get("OPENAI_BASE_URL") and not env.get("OPENAI_API_BASE"):
        env["OPENAI_API_BASE"] = env["OPENAI_BASE_URL"]
    spec = SandboxSpec(config.sandbox, config.image, config.os, config.apptainer_path)
    return build_command(
        spec,
        binds,
        env,
        ["python", "/app/src/adapter/ras_eval_next/framework_entry.py"],
        writable_home=opencode_home_path(sandbox_dir),
        name=container_name,
    )


def prepare_sandbox(sample: dict[str, Any], config: RunnerConfig) -> tuple[Path, Path | None]:
    source = sample["source"]
    if source == "ras-eval-next":
        sandbox_root = ras_eval_next_common.sandbox_root_for(config.output_path)
        sandbox_dir = ras_eval_next_common.sandbox_dir_for(sandbox_root, sample)
        ras_eval_next_common.build_sandbox(sample, sandbox_dir)
        toolkit_root = ras_eval_next_common.materialize_toolkit_root(sample, config.input_path, sandbox_dir)
        if toolkit_root is not None:
            computer_src = REPO_ROOT / "src" / "toolkits" / "ras_eval" / "computer_toolkit"
            computer_dst = Path(toolkit_root) / "computer_toolkit"
            if not computer_dst.exists():
                shutil.copytree(computer_src, computer_dst)
        return sandbox_dir, toolkit_root
    if source == "skill_inject" and sample.get("meta", {}).get("attack_type") == "cia":
        sandbox_root = skill_inject_common.sandbox_root_for(config.output_path)
        sandbox_dir = skill_inject_common.sandbox_dir_for(sandbox_root, sample)
        skill_inject_common.build_sandbox(sample, sandbox_dir)
        return sandbox_dir, None
    raise NotImplementedError(f"framework={config.framework} is not supported for source={source}")


def run_sample(sample: dict[str, Any], config: RunnerConfig, limiter: RateLimiter) -> dict[str, Any]:
    _load_env()
    traceid = sample["traceid"]
    source = sample["source"]
    meta = sample.get("meta", {})
    sandbox_dir: Path | None = None
    toolkit_root: Path | None = None
    timed_out = False
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
        if config.runtime_verification:
            from src.evaluator.spec.runtime import prepare_runtime_dir

            prepare_runtime_dir(sample, sandbox_dir)
        container_name = f"daedalus-{config.framework.replace('-', '')}-{os.getpid()}-{traceid}"
        command = _build_command(sample, config, sandbox_dir, toolkit_root, container_name)
        limiter.wait()
        stdout, stderr, returncode, timed_out = _run_agent_command(
            command,
            os.environ.copy(),
            None,
            config.timeout,
            container_name if config.sandbox == "docker" else None,
        )
        trace_path = sandbox_dir / ".daedalus_trace.jsonl"
        messages = _trace_messages(trace_path)
        if not messages:
            raise RuntimeError(
                f"{config.framework} produced no trace for traceid {traceid}.\n"
                f"--- stderr ---\n{stderr[-4000:]}\n--- stdout ---\n{stdout[-4000:]}"
            )
        has_progress = any(message.get("role") in {"assistant", "tool"} for message in messages)
        if returncode != 0 and not timed_out:
            if not has_progress:
                raise RuntimeError(
                    f"{config.framework} run failed for traceid {traceid} with exit code {returncode}.\n"
                    f"--- stderr ---\n{stderr[-4000:]}\n--- stdout ---\n{stdout[-4000:]}"
                )
            print(
                f"[WARN] traceid={traceid}: {config.framework} exited with code {returncode}; "
                "keeping the partial trajectory for evaluation."
            )
        if timed_out:
            print(
                f"[WARN] traceid={traceid}: {config.framework} timed out after {config.timeout}s; "
                "keeping the partial trajectory for evaluation."
            )
        if source == "ras-eval-next":
            messages = ras_eval_next_common.normalize_messages({**meta, "system_prompt": ""}, messages)
        elif source == "skill_inject":
            (sandbox_dir / "agent_stdout.txt").write_text(
                skill_inject_common.render_transcript([m for m in messages if m.get("role") != "system"]),
                encoding="utf-8",
            )
            if stderr:
                (sandbox_dir / "agent_stderr.txt").write_text(stderr, encoding="utf-8")
        row: dict[str, Any] = {"traceid": traceid, "framework": config.framework, "response": messages}
        if timed_out:
            row["timeout"] = True
            row["timeout_seconds"] = config.timeout
        elif returncode != 0:
            row["incomplete"] = True
            row["agent_exit_code"] = returncode
            if stdout:
                row["stdout_tail"] = stdout[-4000:]
        if stderr:
            row["stderr_tail"] = stderr[-4000:]
        return row
    except Exception:
        if sandbox_dir is not None:
            cleanup_sandbox_artifacts(sandbox_dir)
            if config.runtime_verification:
                from src.evaluator.spec.runtime import cleanup_runtime_dir

                cleanup_runtime_dir(sandbox_dir)
            if source == "ras-eval-next":
                ras_eval_next_common.cleanup_materialized_toolkit(sandbox_dir)
            shutil.rmtree(sandbox_dir, ignore_errors=True)
            try:
                sandbox_dir.parent.rmdir()
            except OSError:
                pass
        raise
    finally:
        if sandbox_dir is not None:
            cleanup_sandbox_artifacts(sandbox_dir)
            if source == "ras-eval-next":
                ras_eval_next_common.cleanup_materialized_toolkit(sandbox_dir)
