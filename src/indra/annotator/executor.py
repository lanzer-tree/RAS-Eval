"""Per-sample execution for the flywheel annotate (SpecAgent) pipeline.

Two sandboxed phases per sample, both isolated under the output directory:

1. ``run_inference`` -- replay the ras-eval-next sample with opencode + MCP server
   (native tools denied) and keep the parsed trajectory plus the post-run
   environment snapshot as a checkpoint under ``traces/TASK-{tid}/``.
2. ``run_spec_agent`` -- a single self-driven opencode session that reads the
   tool sources and trajectory, drafts LTL specifications, runs the nuXmv
   verifier inside the sandbox and iterates until it believes the annotation
   is correct, then writes ``specs.json``.

``collect_result`` validates the specs, re-runs the verifier on the host (mac
nuXmv) for the record, and builds the final ras-eval-next dataset row.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.adapter.agentdojo import annotate as agentdojo_annotate
from src.adapter.skill_inject import annotate as skill_inject_annotate
from src.runner.opencode_runner import parse_opencode_response, _load_env
from src.runner.sandbox import SandboxSpec, build_command, opencode_config_bind, opencode_home_path, cleanup_sandbox_artifacts

REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPTS_DIR = REPO_ROOT / "src" / "indra" / "prompts"
NUXMV_LINUX_DIR = REPO_ROOT / "bin" / "nuXmv-2.2.0-linux64"
# Self-contained launcher (bundled x86-64 loader + libs): usable both inside
# sandboxes of any base image and on x86-64 Linux hosts, no /lib64 bind needed.
NUXMV_LINUX_BIN = NUXMV_LINUX_DIR / "usr" / "local" / "bin" / "nuXmv-portable.sh"
NUXMV_MAC_BIN = REPO_ROOT / "bin" / "nuXmv" / "bin" / "nuXmv"
NUXMV_SANDBOX_BIN = "/opt/nuXmv/usr/local/bin/nuXmv-portable.sh"


def _host_nuxmv_bin() -> Path:
    """nuXmv binary for host-side verification, selected by the host platform
    (mac uses the Mach-O build, Linux the bundled portable launcher)."""
    return NUXMV_MAC_BIN if sys.platform == "darwin" else NUXMV_LINUX_BIN

# Serializes copy-back of an updated verifier.py into the shared workspace.
_verifier_sync_lock = threading.Lock()


@dataclass(frozen=True)
class AnnotateConfig:
    input_path: Path
    output_dir: Path
    model: str
    sandbox: str
    os: str
    benchmark: str = "ras-eval-next"
    # base annotates completion + safety specs, attack annotates the security spec.
    mode: str = "base"
    parallel: int = 1
    qps: float = 1.0
    traceid: int | None = None
    timeout: int = 900
    skip_exist_traceid: bool = False
    apptainer_path: str | None = None
    image: str | None = None
    max_iterations: int = 8
    limit: int | None = None
    disable_native_tools: bool = False


SPEC_KEYS = ("specifications", "completion_specifications", "safety_specifications", "security_specifications")


def _clean_sample(sample: dict[str, Any]) -> dict[str, Any]:
    """Strip any existing spec annotations so old ones never leak into the
    inference run or the SpecAgent context."""
    meta = {k: v for k, v in sample["meta"].items() if k not in SPEC_KEYS}
    return {**sample, "meta": meta}


def _tool_providers(sample: dict[str, Any], cfg: AnnotateConfig) -> list[str]:
    """MCP provider names used to strip the tool-name prefix from the trajectory."""
    if cfg.benchmark == "agentdojo":
        return [sample["meta"]["suite_name"]]
    if cfg.benchmark == "skill_inject":
        # No MCP server: the agent only calls opencode's native tools.
        return []
    return ["ras_eval_next"]


def _get_inference_config(sample: dict[str, Any], cfg: AnnotateConfig) -> str:
    """opencode config for the trajectory replay -- MCP toolkit tools plus (by
    default) opencode's native tools, so trajectories reflect what a real agent
    run may do and specs can reference native-tool events."""
    _load_env()
    base_url = os.environ["OPENAI_BASE_URL"]
    api_key = os.environ["OPENAI_API_KEY"]
    model_provider, model = cfg.model.split("/", 1)
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
    # The replay runs without ``--auto``, so any permission that falls through to
    # opencode's "ask" default is auto-rejected and aborts the session. Neither
    # ``doom_loop`` (same tool call three times) nor ``external_directory``
    # matches an entry above, so allow them explicitly.
    permission.update({"external_directory": {"*": "allow"}, "doom_loop": "allow"})
    if cfg.benchmark == "agentdojo":
        mcp = agentdojo_annotate.mcp_config(_clean_sample(sample))
    elif cfg.benchmark == "skill_inject":
        # No MCP server; the task skill is the only one the agent may load.
        mcp = {}
        permission = skill_inject_annotate.permission(sample)
    else:
        mcp = {
            "ras_eval_next": {
                "type": "local",
                "command": ["python", "/app/src/adapter/ras_eval_next/ras_eval_mcp.py"],
                "environment": {
                    "RAS_EVAL_SAMPLE_JSON": json.dumps(_clean_sample(sample), ensure_ascii=False),
                    "PYTHONPATH": "/app",
                },
                "timeout": 300000,
                "enabled": True,
            }
        }
    config = {
        "provider": {
            model_provider: {
                "npm": "@ai-sdk/openai-compatible",
                "name": model_provider,
                "options": {"baseURL": base_url, "apiKey": api_key},
                "models": {model: {}},
            }
        },
        "mcp": mcp,
        "permission": permission,
    }
    return json.dumps(config, ensure_ascii=False)


def _get_agent_config(cfg: AnnotateConfig) -> str:
    """opencode config for the SpecAgent session -- native tools, no MCP."""
    _load_env()
    base_url = os.environ["OPENAI_BASE_URL"]
    api_key = os.environ["OPENAI_API_KEY"]
    model_provider, model = cfg.model.split("/", 1)
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
            "bash": "allow", "edit": "allow", "write": "allow", "read": "allow",
            "grep": "allow", "glob": "allow", "patch": "allow", "todowrite": "allow",
            "lsp": "deny", "skill": "deny", "webfetch": "deny",
            "websearch": "deny", "question": "deny", "task": "deny",
        },
    }
    return json.dumps(config, ensure_ascii=False)


def _get_api_keys() -> dict[str, str]:
    """Collect toolkit API keys from environment for forwarding into the sandbox."""
    from src.adapter.ras_eval_next.common import API_KEY_NAMES
    _load_env()
    return {name: os.environ[name] for name in API_KEY_NAMES if os.environ.get(name)}


def _normalize_messages(meta: dict[str, Any], messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Align the cached trajectory with the LTL spec protocol: tool_calls
    arguments and tool contents must be strings, and the system prompt is kept
    as the leading message."""
    normalized: list[dict[str, Any]] = []
    if meta.get("system_prompt"):
        normalized.append({"role": "system", "content": meta["system_prompt"]})
    for message in messages:
        message = dict(message)
        if message.get("tool_calls"):
            calls = []
            for call in message["tool_calls"]:
                function = dict(call["function"])
                if not isinstance(function.get("arguments"), str):
                    function["arguments"] = json.dumps(function.get("arguments", {}), ensure_ascii=False)
                calls.append({**call, "function": function})
            message["tool_calls"] = calls
        if message.get("role") == "tool" and not isinstance(message.get("content"), str):
            message["content"] = json.dumps(message.get("content"), ensure_ascii=False)
        normalized.append(message)
    return normalized


def _run_sandboxed(cfg: AnnotateConfig, sandbox_dir: Path, binds: list, env: dict[str, str],
                   prompt: str, auto: bool = False) -> tuple[str, str]:
    """Launch one opencode run in the sandbox and return (stdout, stderr)."""
    spec = SandboxSpec(cfg.sandbox, cfg.image, cfg.os, cfg.apptainer_path)
    args = ["opencode", "run", "--model", cfg.model, "--format", "json"]
    if auto:
        args.append("--auto")
    command = build_command(spec, binds, env, args, writable_home=opencode_home_path(sandbox_dir))
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=os.environ.copy(),
            input=prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=cfg.timeout,
            check=False,
        )
        stdout, stderr = completed.stdout, completed.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        stderr = exc.stderr or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        stderr = f"Timed out after {cfg.timeout} seconds.\n{stderr}"
    return stdout, stderr


def trace_dir_for(cfg: AnnotateConfig, traceid: int) -> Path:
    return Path(cfg.output_dir) / "traces" / f"TASK-{traceid}"


def _preflight_mcp(sample: dict[str, Any], cfg: AnnotateConfig, trace_dir: Path, binds: list, env: dict[str, str]) -> None:
    """Start the MCP server in --check mode inside the sandbox before running
    opencode. opencode silently falls back to zero tools when the MCP server
    dies at startup (e.g. an environment-replay crash), which would masquerade
    as a legitimate no-tool trajectory -- fail fast with the traceback instead."""
    spec = SandboxSpec(cfg.sandbox, cfg.image, cfg.os, cfg.apptainer_path)
    # The sample JSON travels through a file in the bind-mounted workspace, not
    # the environment: apptainer sources env vars from a generated shell script
    # that shreds JSON quotes/backslashes (opencode's own MCP launch is exempt
    # because it spawns the server directly from the file-bound config).
    sample_file = trace_dir / ".sample.json"
    sample_file.write_text(json.dumps(_clean_sample(sample), ensure_ascii=False), encoding="utf-8")
    report_file = trace_dir / ".env_replay_warnings.json"
    report_file.unlink(missing_ok=True)
    if cfg.benchmark == "agentdojo":
        args, extra_env = agentdojo_annotate.preflight(_clean_sample(sample), "/workspace/.sample.json")
    else:
        args = ["python", "/app/src/adapter/ras_eval_next/ras_eval_mcp.py", "--check"]
        extra_env = {
            "RAS_EVAL_SAMPLE_PATH": "/workspace/.sample.json",
            "RAS_EVAL_ENV_REPLAY_REPORT": "/workspace/.env_replay_warnings.json",
        }
    command = build_command(spec, binds, {**env, **extra_env}, args, writable_home=opencode_home_path(trace_dir))
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=os.environ.copy(),
            input="",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=180,
            check=False,
        )
    finally:
        sample_file.unlink(missing_ok=True)
    # Keep the environment-replay warnings (if any) next to the trajectory so
    # degraded samples can be spotted and the dataset repaired later.
    if report_file.exists():
        report_file.replace(trace_dir / "env_replay_warnings.json")
    if completed.returncode != 0:
        raise RuntimeError(
            f"MCP preflight failed (exit={completed.returncode}):\n{completed.stderr.strip()[-1500:]}"
        )


def run_inference(sample: dict[str, Any], cfg: AnnotateConfig) -> list[dict[str, Any]]:
    """Replay the sample once and checkpoint trajectory + final environment.

    Resume-aware: if ``traces/TASK-{tid}/response.json`` already exists the
    cached trajectory is returned without re-running.
    """
    trace_dir = trace_dir_for(cfg, sample["traceid"])
    response_path = trace_dir / "response.json"
    if response_path.exists():
        return json.loads(response_path.read_text(encoding="utf-8"))

    # Fresh per-task dir; the environment is (re)seeded per attempt below.
    if trace_dir.exists():
        shutil.rmtree(trace_dir)
    trace_dir.mkdir(parents=True)

    system_prompt = sample["meta"].get("system_prompt", "")
    if system_prompt:
        (trace_dir / "AGENTS.md").write_text(system_prompt + "\n", encoding="utf-8")

    # An empty response means a transient API/runtime failure, so retry once on
    # a freshly seeded environment (a trajectory with an assistant reply but no
    # tool calls is legitimate -- empty event sequences are verifiable).
    for attempt in (1, 2):
        shutil.rmtree(trace_dir / "environment", ignore_errors=True)
        if cfg.benchmark == "agentdojo":
            # AgentDojo keeps its environment in the MCP process; the server
            # dumps the state into this dir after every tool call.
            (trace_dir / "environment").mkdir()
        elif cfg.benchmark == "skill_inject":
            # The skill-inject sandbox (task files + skills) is the environment.
            skill_inject_annotate.build_environment(sample, trace_dir / "environment")
        else:
            shutil.copytree(Path(cfg.output_dir) / "environment", trace_dir / "environment")

        # Config and binds are built per attempt: the cleanup below removes the
        # run's config file, and the skill-inject binds are derived from the
        # freshly seeded sandbox.
        config_bind, config_env = opencode_config_bind(trace_dir, _get_inference_config(sample, cfg))
        if cfg.benchmark == "agentdojo":
            binds = agentdojo_annotate.inference_binds(trace_dir, cfg.output_dir) + [config_bind]
        elif cfg.benchmark == "skill_inject":
            binds = skill_inject_annotate.inference_binds(trace_dir) + [config_bind]
        else:
            binds = [
                (str(trace_dir.absolute()), "/workspace", False),
                # Toolkits that anchor the environment root to their own __file__ resolve
                # it to /app; bind the same host dir there so they share state with the
                # cwd-relative ones instead of missing the mounted environment.
                (str((trace_dir / "environment").absolute()), "/app/environment", False),
                (str((Path(cfg.output_dir) / "toolkits").absolute()), "/app/src/toolkits/ras_eval", True),
                (str((REPO_ROOT / "src" / "adapter").absolute()), "/app/src/adapter", True),
                (str((REPO_ROOT / "src" / "runner").absolute()), "/app/src/runner", True),
                (str((REPO_ROOT / "src" / "__init__.py").absolute()), "/app/src/__init__.py", True),
                config_bind,
            ]
        env = {
            **config_env,
            "OPENCODE_DISABLE_AUTOUPDATE": "1",
            "PYTHONPATH": "/app",
            "NODE_TLS_REJECT_UNAUTHORIZED": "0",
            **_get_api_keys(),
        }
        if cfg.benchmark == "skill_inject":
            env.update(skill_inject_annotate.INFERENCE_ENV)

        try:
            if cfg.benchmark != "skill_inject":
                _preflight_mcp(sample, cfg, trace_dir, binds, env)
            stdout, stderr = _run_sandboxed(cfg, trace_dir, binds, env, sample["prompt"])
        finally:
            # Drop the per-run config + writable home, keep the trace dir itself.
            cleanup_sandbox_artifacts(trace_dir)

        try:
            messages = parse_opencode_response(sample, _tool_providers(sample, cfg), stdout, stderr, 0)
        except Exception:
            messages = [{"role": "user", "content": sample["prompt"]}]
        messages = _normalize_messages(sample["meta"], messages)

        if any(m.get("role") == "assistant" for m in messages):
            response_path.write_text(json.dumps(messages, ensure_ascii=False, indent=2), encoding="utf-8")
            return messages
        print(f"[WARN] traceid={sample['traceid']}: empty inference output (attempt {attempt})")

    # Keep the dir for inspection but do not checkpoint, so a later resumed run
    # retries the inference.
    (trace_dir / "inference_stderr.txt").write_text(stderr or "", encoding="utf-8")
    raise RuntimeError("inference produced no assistant output")


def _build_agent_prompt(sample: dict[str, Any], response: list[dict[str, Any]], cfg: AnnotateConfig) -> str:
    # Old spec annotations must never reach the agent, so the cleaned sample is
    # what the per-benchmark prompt builders see.
    if cfg.benchmark == "agentdojo":
        return agentdojo_annotate.agent_prompt(_clean_sample(sample), response, cfg.mode, cfg.max_iterations)
    if cfg.benchmark == "skill_inject":
        return skill_inject_annotate.agent_prompt(_clean_sample(sample), cfg.mode, cfg.max_iterations)
    template = (PROMPTS_DIR / "annotate_base.md").read_text(encoding="utf-8")
    meta = sample["meta"]
    toolkit_paths = "\n".join(
        f"- `/workspace/toolkits/{tk}/function/{tk}.py`" for tk in meta["toolkits"]
    )
    prompt = template.replace("{{TASK_PROMPT}}", sample["prompt"])
    prompt = prompt.replace("{{SYSTEM_PROMPT}}", meta.get("system_prompt", ""))
    prompt = prompt.replace("{{TOOLS}}", json.dumps(meta["tools"], ensure_ascii=False))
    prompt = prompt.replace("{{TOOLKIT_PATHS}}", toolkit_paths)
    prompt = prompt.replace("{{MAX_ITERATIONS}}", str(cfg.max_iterations))
    return prompt


def _agents_md(cfg: AnnotateConfig) -> str:
    """SpecAgent instructions: ras-eval-next keeps the original prompt, the
    official-annotation-aware v2 prompts serve agentdojo / skill_inject."""
    if cfg.benchmark == "ras-eval-next":
        return "spec_agent.md"
    return "security_spec_agent_v2.md" if cfg.mode == "attack" else "spec_agent_v2.md"


def run_spec_agent(sample: dict[str, Any], cfg: AnnotateConfig) -> None:
    """Run the self-driven SpecAgent session that produces ``agent/specs.json``."""
    trace_dir = trace_dir_for(cfg, sample["traceid"])
    agent_dir = trace_dir / "agent"
    if agent_dir.exists():
        shutil.rmtree(agent_dir)
    agent_dir.mkdir(parents=True)

    # Per-trace verifier copy (rw): the agent may fix it; accepted fixes are
    # synced back to the shared workspace copy in collect_result.
    shutil.copytree(Path(cfg.output_dir) / "verifier", agent_dir / "verifier")
    shutil.copy(PROMPTS_DIR / _agents_md(cfg), agent_dir / "AGENTS.md")

    config_bind, config_env = opencode_config_bind(agent_dir, _get_agent_config(cfg))
    binds = [
        # agent_dir is the only writable mount; everything else is read-only.
        (str(agent_dir.absolute()), "/workspace", False),
        (str((trace_dir / "response.json").absolute()), "/workspace/response.json", True),
        (str((trace_dir / "environment").absolute()), "/workspace/environment", True),
        (str(NUXMV_LINUX_DIR.absolute()), "/opt/nuXmv", True),
        config_bind,
    ]
    # Toolkit sources (absent for skill_inject) and the official evaluation code
    # (only agentdojo) are mounted when the workspace provides them.
    for name in ("toolkits", "official"):
        source = Path(cfg.output_dir) / name
        if source.exists():
            binds.append((str(source.absolute()), f"/workspace/{name}", True))
    env = {
        **config_env,
        "OPENCODE_DISABLE_AUTOUPDATE": "1",
        "NODE_TLS_REJECT_UNAUTHORIZED": "0",
    }

    prompt = _build_agent_prompt(sample, json.loads((trace_dir / "response.json").read_text(encoding="utf-8")), cfg)
    try:
        stdout, stderr = _run_sandboxed(cfg, agent_dir, binds, env, prompt, auto=True)
    finally:
        cleanup_sandbox_artifacts(agent_dir)

    (trace_dir / "agent_stdout.jsonl").write_text(stdout or "", encoding="utf-8")
    if stderr:
        (trace_dir / "agent_stderr.txt").write_text(stderr, encoding="utf-8")


def _validate_specs(specs: Any, mode: str) -> dict[str, list[dict[str, str]]]:
    """Validate the specs.json schema, returning the normalized spec lists.

    mode=base expects completion + safety specs; mode=attack expects exactly one
    security spec (the official attack-success criterion has a single condition).
    """
    if not isinstance(specs, dict):
        raise ValueError("specs.json must be a JSON object")
    keys = ("security_specifications",) if mode == "attack" else ("completion_specifications", "safety_specifications")
    result = {}
    for key in keys:
        items = specs.get(key)
        if not isinstance(items, list):
            raise ValueError(f"specs.json missing list field {key!r}")
        normalized = []
        for item in items:
            if not isinstance(item, dict) or not item.get("formal_spec") or not item.get("language_spec"):
                raise ValueError(f"every item in {key!r} needs non-empty formal_spec and language_spec")
            normalized.append({"formal_spec": item["formal_spec"], "language_spec": item["language_spec"]})
        result[key] = normalized
    if mode == "attack":
        if len(result["security_specifications"]) != 1:
            raise ValueError("security_specifications must contain exactly one spec")
    elif not result["completion_specifications"]:
        raise ValueError("completion_specifications must not be empty")
    return result


def collect_result(sample: dict[str, Any], cfg: AnnotateConfig) -> dict[str, Any]:
    """Collect the SpecAgent output into a ras-eval-next dataset row.

    Acceptance gate: specs.json exists, schema is valid and every spec parses
    in the verifier (no "error:" result). sat/unsat values are recorded for
    review but not gated -- the trajectory itself may be imperfect and the
    agent's own judgement is trusted.
    """
    trace_dir = trace_dir_for(cfg, sample["traceid"])
    agent_dir = trace_dir / "agent"
    specs_path = agent_dir / "specs.json"
    if not specs_path.exists():
        raise RuntimeError("SpecAgent did not produce specs.json")
    specs = _validate_specs(json.loads(specs_path.read_text(encoding="utf-8")), cfg.mode)

    # Host-side re-verification with the (possibly agent-patched) verifier copy
    # and the mac nuXmv binary; results are archived for manual review.
    completed = subprocess.run(
        [
            sys.executable, str(agent_dir / "verifier" / "verify.py"),
            "--response", str(trace_dir / "response.json"),
            "--specs", str(specs_path),
            "--env_dir", str(trace_dir / "environment"),
            "--nuxmv", str(_host_nuxmv_bin()),
        ],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=300,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"host verification failed: {completed.stderr.strip()[-1500:]}")
    report = json.loads(completed.stdout)
    (trace_dir / "verify_result.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    unparsable = [
        item["formal_spec"]
        for items in report.values()
        for item in items
        if str(item["result"]).startswith("error")
    ]
    if unparsable:
        raise RuntimeError(f"specs not parsable by verifier: {unparsable}")

    # Promote an agent-patched verifier so later samples use the fixed version.
    patched = (agent_dir / "verifier" / "verifier.py").read_text(encoding="utf-8")
    shared_path = Path(cfg.output_dir) / "verifier" / "verifier.py"
    with _verifier_sync_lock:
        if patched != shared_path.read_text(encoding="utf-8"):
            shared_path.write_text(patched, encoding="utf-8")

    if cfg.benchmark == "agentdojo":
        return agentdojo_annotate.result_row(sample, specs, cfg.mode)
    if cfg.benchmark == "skill_inject":
        return skill_inject_annotate.result_row(sample, specs)

    meta = {
        key: sample["meta"][key]
        for key in ("agent", "system_prompt", "tools", "toolkits", "environment", "docker_image")
        if key in sample["meta"]
    }
    meta["completion_specifications"] = specs["completion_specifications"]
    meta["safety_specifications"] = specs["safety_specifications"]
    meta["security_specifications"] = []
    return {
        "traceid": sample["traceid"],
        "prompt": sample["prompt"],
        "source": "ras-eval-next",
        "meta": meta,
    }
