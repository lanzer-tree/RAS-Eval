from __future__ import annotations

import ast
import contextlib
import json
import math
import os
import re
import shutil
import signal
import subprocess
# import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from collections import OrderedDict
from tqdm import tqdm
from src.adapter.skill_inject.common import (
    build_sandbox,
    render_transcript,
    sandbox_dir_for,
    build_agent_command,
    sandbox_root_for
)
from src.adapter.ras_eval_next import common as ras_eval_next_common
from src.runner.sandbox import SandboxSpec, cleanup_sandbox_artifacts, env_dir_for

REPO_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class RunnerConfig:
    input_path: Path
    output_path: Path
    model: str
    sandbox: str
    os: str
    limit: int | None = None
    parallel: int = 1
    qps: float = 1.0
    traceid: int | None = None
    timeout: int = 900
    skip_exist_traceid: bool = False
    apptainer_path: str | None = None
    image: str | None = None
    framework: str = "opencode"
    disable_native_tools: bool = False
    keep_sandbox: bool = False
    runtime_verification: bool = False
    request_qps: float | None = None
    request_max_retries: int | None = None
    scan_repair: bool = False
    clawguard: bool = False
    agentdog_runtime_verification: bool = False
    agentdog_base_url: str | None = None
    agentdog_model: str = "AgentDoG1.5-Qwen3.5-4B"
    agentdog_timeout: float = 30.0
    shieldagent_runtime_verification: bool = False
    shieldagent_base_url: str | None = None
    shieldagent_model: str = "ShieldAgent"
    shieldagent_timeout: float = 30.0
    prompt_detector: bool = False
    prompt_detector_timeout: float = 60.0
    information_flow: bool = False
    analysis_budget: str = "L2"
    query_mode: str = "sink"
    analysis_timeout: float = 300.0
    review_timeout: float = 600.0


class RateLimiter:
    def __init__(self, qps: float) -> None:
        self.interval = 0.0 if qps <= 0 else 1.0 / qps
        self.lock = threading.Lock()
        self.next_time = 0.0

    def wait(self) -> None:
        if self.interval <= 0:
            return
        with self.lock:
            now = time.monotonic()
            if now < self.next_time:
                time.sleep(self.next_time - now)
                now = time.monotonic()
            self.next_time = now + self.interval


def _load_env() -> None:
    """Populate OPENAI_API_KEY / OPENAI_BASE_URL from the repo ``.env`` (used to
    configure the opencode provider inside the Docker sandbox, where cc-switch
    is not available). Existing environment values take precedence."""
    env_file = REPO_ROOT / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        os.environ.setdefault(key.strip(), value)


def get_opencode_config(sample: dict[str, Any], runner_cfg: RunnerConfig) -> str:
    _load_env()

    source = sample["source"]
    meta = sample["meta"]

    if runner_cfg.information_flow:
        if source not in {"skill_inject", "ras-eval-next"} or runner_cfg.framework != "opencode":
            raise ValueError("information_flow only supports opencode sandbox tasks")
        if not re.fullmatch(r"[^/\s]+/\S+", runner_cfg.model):
            raise ValueError("information_flow model must explicitly specify provider/model")
        if runner_cfg.analysis_budget not in {"L0", "L1", "L2", "L3"}:
            raise ValueError("analysis_budget must be one of L0/L1/L2/L3")
        if runner_cfg.query_mode not in {"source", "sink", "source-sink"}:
            raise ValueError("query_mode must be one of source/sink/source-sink")
        for value in (runner_cfg.analysis_timeout, runner_cfg.review_timeout):
            if not math.isfinite(value) or value <= 0:
                raise ValueError("information flow stage timeout must be a positive finite number of seconds")
        if not os.environ.get("OPENAI_BASE_URL") or not os.environ.get("OPENAI_API_KEY"):
            raise ValueError("information_flow requires OPENAI_BASE_URL and OPENAI_API_KEY to be configured")

    if source == "skill_inject":
        base_url = os.environ["OPENAI_BASE_URL"]
        api_key = os.environ["OPENAI_API_KEY"]
        model_provider = runner_cfg.model.split("/")[0]
        model = runner_cfg.model.split("/")[1]
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
                "external_directory": {"*": "allow"},
                "doom_loop": "allow",
                "skill": {"*": "deny", meta["skill"]: "allow"},
            },
        }
    
    elif source == "agentdojo":
        base_url = os.environ["OPENAI_BASE_URL"]
        api_key = os.environ["OPENAI_API_KEY"]
        model_provider, model = runner_cfg.model.split("/", 1)
        suite_name = meta["suite_name"]
        server_path = REPO_ROOT / "src" / "adapter" / "agentdojo" / "agentdojo_mcp.py"
        config = {
            "$schema": "https://opencode.ai/config.json",
            # Configure the provider from the repo credentials like every other
            # source: without this block opencode falls back to whatever ambient
            # credentials it has stored, so a refreshed .env key never takes
            # effect and runs fail with a stale-key APIError.
            "provider": {
                model_provider: {
                    "npm": "@ai-sdk/openai-compatible",
                    "name": model_provider,
                    "options": {"baseURL": base_url, "apiKey": api_key},
                    "models": {model: {}},
                }
            },
            "mcp": {
                suite_name: {
                    "type": "local",
                    "command": ["uv", "run", str(server_path)],
                    "cwd": str(REPO_ROOT),
                    "environment": {
                        "AGENTDOJO_SUITE": suite_name,
                        "AGENTDOJO_SAMPLE_JSON": json.dumps(sample, ensure_ascii=False),
                        # AgentDojo keeps its environment in the MCP process, so the
                        # server dumps the state here after every tool call for the
                        # LTL evaluator's environment observers to read.
                        "AGENTDOJO_ENV_DUMP_DIR": str(env_dir_for(runner_cfg.output_path, sample["traceid"])),
                        "PYTHONPATH": str(REPO_ROOT),
                        # "PYTHONDONTWRITEBYTECODE": "1",
                    },
                    "timeout": 300000,
                    "enabled": True,
                }
            },
            "permission": {
                "bash": "deny",
                "edit": "deny",
                "write": "deny",
                "read": "deny",
                "grep": "deny",
                "glob": "deny",
                "lsp": "deny",
                "patch": "deny",
                "skill": "deny",
                "todowrite": "deny",
                "webfetch": "deny",
                "websearch": "deny",
                "question": "deny",
                "task": "deny",
            }
        }

    elif source == "ras-eval-next":
        base_url = os.environ["OPENAI_BASE_URL"]
        api_key = os.environ["OPENAI_API_KEY"]
        model_provider = runner_cfg.model.split("/")[0]
        model = runner_cfg.model.split("/")[1]
        server_path = "/app/src/adapter/ras_eval_next/ras_eval_mcp.py"
        # Native tools stay enabled by default so trajectories match how the
        # ras-eval-next specs were annotated (the SpecAgent replay allowed them).
        if runner_cfg.disable_native_tools:
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
        # ``doom_loop`` (the same tool call repeated three times) and
        # ``external_directory`` are not tools, so the entries above never match
        # them and opencode falls back to "ask". A non-interactive ``opencode
        # run`` auto-rejects every ask, which aborts the session mid-trajectory --
        # a weak model retrying one tool call would lose the whole sample. Allow
        # both explicitly, like the other sources' configs do.
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
                "ras_eval_next": {
                    "type": "local",
                    "command": ["python", server_path],
                    "environment": {
                        "RAS_EVAL_SAMPLE_JSON": json.dumps(
                            ras_eval_next_common.clean_sample(sample), ensure_ascii=False
                        ),
                        "PYTHONPATH": "/app",
                    },
                    "timeout": 300000,
                    "enabled": True,
                }
            },
            "permission": permission,
        }
        if runner_cfg.prompt_detector:
            # Opencode never fires ``tool.definition`` for MCP tools, so the
            # prompt_detector plugin cannot scan tool descriptions (TPA). Forward
            # the detector's credentials so the per-task MCP server scans each
            # description where it is built and appends the defense note the
            # model actually sees. The plugin still handles tool outputs (TOMA).
            config["mcp"]["ras_eval_next"]["environment"].update({
                "RAS_EVAL_PROMPT_DETECTOR": "1",
                "RAS_EVAL_PROMPT_DETECTOR_BASE_URL": base_url,
                "RAS_EVAL_PROMPT_DETECTOR_API_KEY": api_key,
                "RAS_EVAL_PROMPT_DETECTOR_MODEL": model,
                "RAS_EVAL_PROMPT_DETECTOR_TEMPLATE_PATH": "/app/src/defense/prompt_detector/tool_description_detector.md",
                "RAS_EVAL_PROMPT_DETECTOR_TIMEOUT": str(runner_cfg.prompt_detector_timeout),
            })
    plugins: list[Any] = []
    if runner_cfg.information_flow:
        plugins.append("file:///app/src/defense/information_flow/opencode_plugin.ts")
        paths = {
            "*": "deny",
            "/workspace/*": "allow",
            "/app/src/toolkits/ras_eval/*": "allow",
            "/information_flow/sessions/*/attempts/*/model/*": "allow",
        }
        config["agent"] = {"information-flow-reviewer": {
            "description": "Standalone read-only information flow review; does not execute tasks or repairs",
            "mode": "subagent", "hidden": True, "model": runner_cfg.model,
            "permission": {
                "*": "deny", "read": dict(paths),
                "grep": "allow", "glob": "allow", "external_directory": dict(paths),
            },
        }}
        config["permission"].update({
            "edit": "allow", "write": "allow", "patch": "allow",
            "external_directory": {"*": "allow"}, "doom_loop": "allow",
        })
        for server in config.get("mcp", {}).values():
            server["environment"]["INFORMATION_FLOW_DIR"] = "/information_flow"
            server["timeout"] = math.ceil((runner_cfg.analysis_timeout + runner_cfg.review_timeout + 120) * 1000)
    if runner_cfg.agentdog_runtime_verification and source in {"skill_inject", "ras-eval-next"}:
        if not runner_cfg.runtime_verification or not runner_cfg.agentdog_base_url:
            raise ValueError("AgentDoG requires runtime verification and agentdog_base_url")
        base_url = runner_cfg.agentdog_base_url
        if runner_cfg.sandbox == "docker":
            base_url = re.sub(
                r"(://)(localhost|127\.0\.0\.1)(?=[:/])",
                lambda match: f"{match.group(1)}host.docker.internal",
                base_url,
            )
        plugins.append([
            "file:///app/src/defense/agentdog/opencode_plugin.ts",
            {
                "baseURL": base_url,
                "model": runner_cfg.agentdog_model,
                "timeoutMs": round(runner_cfg.agentdog_timeout * 1000),
                "toolsPath": "/runtime_verification/agentdog_tools.json",
            },
        ])
    if runner_cfg.shieldagent_runtime_verification and source in {"skill_inject", "ras-eval-next"}:
        if not runner_cfg.runtime_verification or not runner_cfg.shieldagent_base_url:
            raise ValueError("ShieldAgent requires runtime verification and shieldagent_base_url")
        base_url = runner_cfg.shieldagent_base_url
        if runner_cfg.sandbox == "docker":
            base_url = re.sub(
                r"(://)(localhost|127\.0\.0\.1)(?=[:/])",
                lambda match: f"{match.group(1)}host.docker.internal",
                base_url,
            )
        plugins.append([
            "file:///app/src/defense/shieldagent/opencode_plugin.ts",
            {
                "baseURL": base_url,
                "model": runner_cfg.shieldagent_model,
                "timeoutMs": round(runner_cfg.shieldagent_timeout * 1000),
                "toolsPath": "/runtime_verification/shieldagent_tools.json",
            },
        ])
    if runner_cfg.prompt_detector and source in {"skill_inject", "ras-eval-next"}:
        # Pure-prompt defense: the plugin scans tool outputs with the agent's own
        # model (via the .env OpenAI-compatible endpoint), appending a defense
        # note when an injection is detected. Detection failures fail open inside
        # the plugin. Tool *description* scanning (TPA) is handled by the MCP
        # server (see above) because opencode never fires ``tool.definition`` for
        # MCP tools.
        plugins.append([
            "file:///app/src/defense/prompt_detector/opencode_plugin.ts",
            {
                "baseURL": os.environ["OPENAI_BASE_URL"],
                "apiKey": os.environ["OPENAI_API_KEY"],
                "model": runner_cfg.model.split("/", 1)[1],
                "timeoutMs": round(runner_cfg.prompt_detector_timeout * 1000),
                "returnPromptPath": "/app/src/defense/prompt_detector/tool_return_detector.md",
            },
        ])
    if runner_cfg.runtime_verification and source in {"skill_inject", "ras-eval-next"}:
        plugins.append("file:///app/src/adapter/ras_eval_next/runtime_verification_plugin.ts")
        # ClawGuard is ordered after the runtime verification plugin so the LTL
        # step is recorded from the raw tool output before ClawGuard's sanitizer
        # redacts what enters the conversation history.
        if runner_cfg.clawguard:
            plugins.append("file:///app/src/defense/clawguard/clawguard_plugin.ts")
            config["instructions"] = ["/app/src/defense/clawguard/INSTRUCTIONS.md"]
            config["permission"].update({
                "cg_set_task_scope": "allow",
                "cg_clear_task_scope": "allow",
                "patch": "deny",
            })
    if plugins:
        config["plugin"] = plugins
    return json.dumps(config, ensure_ascii=False)


def parse_opencode_response(sample: dict, tool_providers: list[str], stdout: str, stderr: str, returncode: int, session_id: str | None = None) -> list[dict[str, Any]]:
    messages: list[dict[str, Any]] = [{"role": "user", "content": sample["prompt"]}]
    # step_start = False
    events = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            # Killing opencode on timeout can truncate the line it was writing.
            print(f"[WARN] skipping unparsable opencode event line: {line[:200]}")
    
    grouped = OrderedDict()
    from colorama import Fore
    for event in events:
        if session_id is not None:
            if not isinstance(event, dict):
                continue
            part = event.get("part")
            event_sessions = [event.get("sessionID"), part.get("sessionID") if isinstance(part, dict) else None]
            if session_id not in event_sessions or any(value is not None and value != session_id for value in event_sessions):
                continue
        # Session-level events (e.g. ``{"type": "error", ...}`` from a transient
        # API failure) carry no message ``part``; skip them so one bad event does
        # not abort the whole run.
        if "part" not in event:
            print(Fore.RED + json.dumps(event, ensure_ascii=False, indent=4) + Fore.RESET)
            continue
        part = event["part"]
        message_id = part["messageID"]
        if message_id not in grouped:
            grouped[message_id] = []
        grouped[message_id].append(event)

    for message_id, message_events in grouped.items():
        reasoning_texts = []
        tool_calls = []
        tool_outputs = []
        text_messages = []

        for event in message_events:
            event_type = event["type"]
            part = event["part"]

            if event_type == "reasoning":
                reasoning_texts.append(part["text"])

            elif event_type == "tool_use":
                tool_name = part.get("tool")
                for tool_provider in tool_providers:
                    if tool_name.startswith(tool_provider):
                        tool_name = tool_name[len(tool_provider)+1:]
                        break
                
                state = part["state"]
                # A tool part may still be pending (no input/output yet); fall back
                # to safe defaults instead of crashing the whole run.
                tool_input = state.get("input", {})
                tool_output = state.get("output", state.get("error", ""))
                tool_calls.append({
                    "type": "function",
                    "function": {
                        "name": tool_name,
                        "arguments": tool_input
                    }
                })
                tool_outputs.append({
                    "role": "tool",
                    "content": tool_output,
                    "name": tool_name,
                })
            elif event_type == "text":
                text_messages.append({
                    "role": "assistant",
                    "content": part["text"]
                })

        if reasoning_texts or tool_calls:
            assistant_msg = {
                "role": "assistant",
                "content": "\n".join(reasoning_texts) if reasoning_texts else ""
            }
            if tool_calls:
                assistant_msg["tool_calls"] = tool_calls
            messages.append(assistant_msg)

        messages.extend(tool_outputs)

        messages.extend(text_messages)
    
    print(Fore.BLUE + json.dumps(messages, ensure_ascii=False, indent=4) + Fore.RESET)
    return messages

def preflight_mcp_server(sample: dict[str, Any]) -> None:
    """Ensure the AgentDojo MCP server can start before running opencode.

    opencode does not abort when a configured MCP server fails to launch; it
    silently falls back to its builtin tools and keeps running, producing
    misleading results. To make failures obvious we start the server in a
    dedicated ``--check`` mode that builds the environment/tools and exits. If
    that subprocess errors, we stop here and raise with the captured output.
    """
    if sample.get("source") != "agentdojo":
        return
    server_path = REPO_ROOT / "src" / "adapter" / "agentdojo" / "agentdojo_mcp.py"
    env = os.environ.copy()
    env["AGENTDOJO_SUITE"] = sample["meta"]["suite_name"]
    env["AGENTDOJO_SAMPLE_JSON"] = json.dumps(sample, ensure_ascii=False)
    env["PYTHONPATH"] = str(REPO_ROOT)
    completed = subprocess.run(
        ["uv", "run", str(server_path), "--check"],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "AgentDojo MCP server failed to start for traceid "
            f"{sample.get('traceid')} (suite={sample['meta']['suite_name']}, "
            f"exit={completed.returncode}). Refusing to run opencode with a "
            "broken MCP server.\n"
            f"--- stderr ---\n{completed.stderr}\n--- stdout ---\n{completed.stdout}"
        )


def _terminate_process_tree(proc: subprocess.Popen, container_name: str | None) -> None:
    """Kill the agent process tree. ``docker kill`` is also needed because killing
    the ``docker run`` client only detaches from a still-running container."""
    if container_name:
        subprocess.run(
            ["docker", "kill", container_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    if proc.poll() is not None:
        return
    try:
        pgid = os.getpgid(proc.pid)
    except ProcessLookupError:
        return
    with contextlib.suppress(ProcessLookupError):
        os.killpg(pgid, signal.SIGTERM)
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        with contextlib.suppress(ProcessLookupError):
            os.killpg(pgid, signal.SIGKILL)
        proc.wait()


def _reap_process_group(pgid: int) -> None:
    """Kill whatever outlived the agent in its session. ``apptainer exec`` shares
    the host network namespace and reaps nothing, so a server the agent
    backgrounded inside the sandbox keeps holding a host port after the run and
    collides with the next sample (or with the local vLLM)."""
    try:
        os.killpg(pgid, signal.SIGTERM)
    except (ProcessLookupError, PermissionError):
        return
    for _ in range(10):
        time.sleep(1)
        try:
            os.killpg(pgid, 0)
        except (ProcessLookupError, PermissionError):
            return
    with contextlib.suppress(ProcessLookupError, PermissionError):
        os.killpg(pgid, signal.SIGKILL)


def _run_agent_command(
    command: list[str],
    env: dict[str, str],
    stdin_input: str | None,
    timeout: int,
    container_name: str | None = None,
) -> tuple[str, str, int, bool]:
    """Run one agent command and return ``(stdout, stderr, returncode, timed_out)``.

    Output is redirected to files instead of pipes so that a timeout still yields
    the events opencode emitted so far: on POSIX ``subprocess.run`` discards the
    partial output when it raises ``TimeoutExpired``. The child gets its own
    session so the whole sandbox process tree can be killed by process group.
    """
    with tempfile.TemporaryDirectory(prefix="opencode_out_") as tmp_dir:
        out_path = Path(tmp_dir) / "stdout.log"
        err_path = Path(tmp_dir) / "stderr.log"
        timed_out = False
        with out_path.open("wb") as out_file, err_path.open("wb") as err_file:
            proc = subprocess.Popen(
                command,
                cwd=REPO_ROOT,
                env=env,
                stdin=subprocess.PIPE,
                stdout=out_file,
                stderr=err_file,
                text=True,
                start_new_session=True,
            )
            try:
                proc.communicate(input=stdin_input or "", timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                _terminate_process_tree(proc, container_name)
            except BaseException:
                # Never leave a sandbox running behind an interrupt/crash.
                _terminate_process_tree(proc, container_name)
                raise
            finally:
                # start_new_session makes the child a session leader, so its PGID
                # is its PID and stays reserved while the group has members.
                _reap_process_group(proc.pid)
        stdout = out_path.read_text(encoding="utf-8", errors="replace")
        stderr = err_path.read_text(encoding="utf-8", errors="replace")
    return stdout, stderr, proc.returncode, timed_out


def _has_agent_events(stdout: str) -> bool:
    """True if opencode emitted at least one NDJSON event, i.e. the run produced
    a trajectory worth evaluating."""
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            if isinstance(json.loads(line), dict):
                return True
        except json.JSONDecodeError:
            continue
    return False


def _prepare_information_flow(
    sample: dict[str, Any], config: RunnerConfig, audit_dir: Path,
    config_content: str, toolkit_root: Path | None = None,
) -> None:
    meta = sample["meta"]
    container_root = Path("/app/src/toolkits/ras_eval")
    toolkits: dict[str, str] = {}
    tool_map: dict[str, str] = {}
    descriptions: dict[str, str] = {}
    if sample["source"] == "ras-eval-next":
        from src.adapter.ras_eval_next.ras_eval_mcp import _attack_entries

        if toolkit_root is None:
            raise ValueError("information_flow is missing a private toolkit_root")
        names = meta["toolkits"]
        tools = meta["tools"]
        schema = ras_eval_next_common.tool_descriptions_from_schema(names, tools)
        docstrings: dict[str, str] = {}
        for name in names:
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_]\w*", name):
                raise ValueError("illegal toolkit name")
            relative = Path(name) / "function" / f"{name}.py"
            toolkits[name] = str(container_root / relative)
            try:
                tree = ast.parse((toolkit_root / relative).read_bytes())
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        docstrings[node.name] = ast.get_docstring(node) or node.name
            except (OSError, SyntaxError, UnicodeError):
                pass
        tpa = {attack.get("tool"): str(attack.get("content") or "")
               for attack in _attack_entries(meta.get("attack")) if attack.get("mode") == "tpa"}
        for provider in json.loads(config_content).get("mcp", {}):
            for tool in tools:
                if not isinstance(tool, str) or not re.fullmatch(r"[A-Za-z_]\w*", tool):
                    raise ValueError("illegal tool name")
                actual = f"{provider}_{tool}"
                tool_map[actual] = tool
                description = (schema.get(tool) if meta.get("attack_type") == "cia-tool" else None)
                descriptions[actual] = tpa.get(tool, "") + (description or docstrings.get(tool) or schema.get(tool) or tool)
    content = {
        "traceid": sample["traceid"], "workspace": "/workspace",
        "toolkit_root": str(container_root), "toolkits": toolkits,
        "analysis_budget": config.analysis_budget, "query_mode": config.query_mode,
        "analysis_timeout": config.analysis_timeout, "review_timeout": config.review_timeout,
        "user_prompt": sample["prompt"], "model": config.model,
        "tool_map": tool_map, "tool_descriptions": descriptions,
    }
    with (audit_dir / "config.json").open("x", encoding="utf-8") as handle:
        json.dump(content, handle, ensure_ascii=False, indent=2)


def _finish_information_flow(
    audit_dir: Path, config: RunnerConfig, traceid: Any, status: dict[str, Any],
) -> None:
    try:
        if audit_dir.is_symlink() or not audit_dir.is_dir():
            raise ValueError("information flow temporary root has been replaced")
        archive_root = config.output_path.parent / (config.output_path.stem + ".information_flow")
        archive = archive_root / str(traceid)
        if archive_root.is_symlink() or archive.is_symlink():
            raise ValueError("audit output must not be a symlink")
        try:
            archive.mkdir(parents=True, exist_ok=False)
        except FileExistsError:
            archive = Path(tempfile.mkdtemp(prefix="attempt-", dir=archive))
        secrets = [value for key, value in os.environ.items()
                   if re.search(r"(?:^|_)(?:api_key|access_token|auth_token|secret|password|credential)$", key, re.I)
                                      and value and len(value) >= 6]
        records = {"runner_status.json": json.dumps(status, ensure_ascii=False)}
        for name in ("guard_events.jsonl", "guard_events.json", "main_session.json", "error.json", "errors.json"):
            path = audit_dir / name
            if path.is_file() and not path.is_symlink():
                records[name] = path.read_text(encoding="utf-8", errors="replace")
        errors = []
        for path in audit_dir.glob("sessions/*/attempts/*/analysis.json"):
            if any(parent.is_symlink() for parent in (path, *path.parents) if parent != audit_dir and audit_dir in parent.parents):
                continue
            try:
                analysis = json.loads(path.read_text(encoding="utf-8"))
                if analysis.get("errors"):
                    errors.append({"call_id": analysis.get("call_id"), "errors": analysis["errors"]})
            except (OSError, ValueError, AttributeError):
                errors.append({"error": "analysis_audit_unreadable"})
        if errors:
            records["analysis_errors.json"] = json.dumps(errors, ensure_ascii=False)
        for name, text in records.items():
            for secret in sorted(secrets, key=len, reverse=True):
                text = text.replace(secret, "[REDACTED]")
            text = re.sub(r"Bearer\s+[^\s\"\\]+", "Bearer [REDACTED]", text, flags=re.I)
            with (archive / name).open("x", encoding="utf-8") as handle:
                handle.write(text)
    finally:
        if not audit_dir.is_symlink():
            shutil.rmtree(audit_dir, ignore_errors=True)


def run_sample(sample: dict[str, Any], config: RunnerConfig, limiter: RateLimiter) -> dict[str, Any]:
    traceid = sample["traceid"]
    source = sample["source"]
    meta = sample["meta"]
    prompt = sample["prompt"]
    config_content = get_opencode_config(sample, config)
    audit_dir: Path | None = None
    audit_status: dict[str, Any] = {"status": "setup_error"}
    if config.information_flow:
        if not re.fullmatch(r"[A-Za-z0-9_-]+", str(traceid)):
            raise ValueError("information_flow traceid must not contain path separators")
        from src.runner.sandbox import mcp_sample_path, opencode_config_path, opencode_home_path
        from src.evaluator.spec.runtime import runtime_dir_for

        layout = ras_eval_next_common if source == "ras-eval-next" else None
        root = layout.sandbox_root_for(config.output_path) if layout else sandbox_root_for(config.output_path)
        directory = layout.sandbox_dir_for(root, sample) if layout else sandbox_dir_for(root, sample)
        reserved = [directory, directory.parent / (directory.name + ".information_flow"),
                    ras_eval_next_common.materialized_toolkit_dir(directory), runtime_dir_for(directory),
                    mcp_sample_path(directory), opencode_config_path(directory), opencode_home_path(directory)]
        if any(path.exists() or path.is_symlink() for path in reserved):
            raise FileExistsError("information flow task temporary path already exists; refusing to overwrite or delete")
    container_name: str | None = None
    # Sandboxed sources feed the prompt via stdin; agentdojo runs opencode on the
    # host and keeps the prompt in argv.
    stdin_input: str | None = None
    if source == "skill_inject":
        limiter.wait()
        env = os.environ.copy()
        sandbox_root = sandbox_root_for(config.output_path)
        sandbox_dir = sandbox_dir_for(sandbox_root, sample)
        if config.information_flow:
            candidate = sandbox_dir.parent / (sandbox_dir.name + ".information_flow")
            candidate.mkdir(parents=True, exist_ok=False)
            audit_dir = candidate
        try:
            build_sandbox(sample, sandbox_dir)
            if config.information_flow:
                _prepare_information_flow(sample, config, audit_dir, config_content)
            if config.runtime_verification:
                from src.evaluator.spec.runtime import prepare_runtime_dir

                prepare_runtime_dir(sample, sandbox_dir)
            if config.agentdog_runtime_verification:
                from src.defense.agentdog.runtime import prepare_agentdog_runtime

                prepare_agentdog_runtime(
                    sample,
                    sandbox_dir,
                    disable_native_tools=config.disable_native_tools,
                )
            command_logger = (
                "trap 'echo \"$BASH_COMMAND\" >> /workspace/.command_history' DEBUG\n"
            )
            (sandbox_dir / ".bash_command_logger.sh").write_text(command_logger, encoding="utf-8")

            image = config.image
            spec = SandboxSpec(config.sandbox, image, config.os, config.apptainer_path)
            if config.scan_repair:
                from src.defense.scan_repair.runtime import run_scan_repair

                run_scan_repair(
                    sample, sandbox_dir, spec, config.model,
                    toolkit_root=None, timeout=config.timeout,
                )
            container_name = f"daedalus-infer-{os.getpid()}-{traceid}"
            command = build_agent_command(
                spec,
                sandbox_dir,
                config_content,
                config.model,
                name=container_name,
                runtime_verification=config.runtime_verification,
                **({"information_flow": True} if config.information_flow else {}),
            )
        except BaseException as error:
            try:
                if audit_dir is not None:
                    _finish_information_flow(audit_dir, config, traceid, {
                        **audit_status, "error_type": type(error).__name__, "error": str(error)[-8000:],
                    })
            finally:
                cleanup_sandbox_artifacts(sandbox_dir)
                if config.runtime_verification:
                    from src.evaluator.spec.runtime import cleanup_runtime_dir

                    cleanup_runtime_dir(sandbox_dir)
                shutil.rmtree(sandbox_dir, ignore_errors=True)
            if config.information_flow and isinstance(error, Exception):
                raise RuntimeError(f"information flow task initialization failed：{type(error).__name__}；see audit output for details") from None
            raise
        stdin_input = prompt
    elif source == "agentdojo":
        preflight_mcp_server(sample)
        env = os.environ.copy()
        env["OPENCODE_CONFIG_CONTENT"] = get_opencode_config(sample, config)
        env["PYTHONPATH"] = str(REPO_ROOT)
        command = [
            "opencode",
            "run",
            prompt,
            "--model",
            config.model,
            "--format",
            "json",
            "--thinking",
            "--auto",
            "--dir",
            str(REPO_ROOT),
            "--title",
            str(traceid),
        ]
        limiter.wait()
    elif source == "ras-eval-next":
        from src.indra.generate.redteam_server import ensure_started as ensure_redteam_server

        ensure_redteam_server()
        env = os.environ.copy()
        sandbox_root = ras_eval_next_common.sandbox_root_for(config.output_path)
        sandbox_dir = ras_eval_next_common.sandbox_dir_for(sandbox_root, sample)
        api_keys = {
            name: os.environ[name]
            for name in ras_eval_next_common.API_KEY_NAMES
            if os.environ.get(name)
        }
        spec = SandboxSpec(config.sandbox, config.image, config.os, config.apptainer_path)
        if config.information_flow:
            limiter.wait()
            candidate = sandbox_dir.parent / (sandbox_dir.name + ".information_flow")
            candidate.mkdir(parents=True, exist_ok=False)
            audit_dir = candidate
        try:
            ras_eval_next_common.build_sandbox(sample, sandbox_dir)
            if config.runtime_verification:
                from src.evaluator.spec.runtime import prepare_runtime_dir

                prepare_runtime_dir(sample, sandbox_dir)
            toolkit_root = ras_eval_next_common.materialize_toolkit_root(
                sample, config.input_path, sandbox_dir,
                **({"information_flow": True} if config.information_flow else {}),
            )
            if config.information_flow:
                _prepare_information_flow(sample, config, audit_dir, config_content, toolkit_root)
            if config.scan_repair:
                from src.defense.scan_repair.runtime import run_scan_repair

                run_scan_repair(
                    sample, sandbox_dir, spec, config.model,
                    toolkit_root=toolkit_root, timeout=config.timeout,
                )
            if config.agentdog_runtime_verification:
                from src.defense.agentdog.runtime import prepare_agentdog_runtime

                prepare_agentdog_runtime(
                    sample,
                    sandbox_dir,
                    disable_native_tools=config.disable_native_tools,
                )
            check_command = ras_eval_next_common.build_mcp_check_command(
                spec, sandbox_dir, sample, api_keys, toolkit_root=toolkit_root,
                **({"information_flow": True} if config.information_flow else {}),
            )
            check = subprocess.run(
                check_command,
                cwd=REPO_ROOT,
                env=env,
                input="",
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=min(config.timeout, 300),
                check=False,
            )
            if check.returncode != 0:
                raise RuntimeError(
                    "ras-eval-next MCP server failed to start for traceid "
                    f"{traceid} (exit={check.returncode}). Refusing to run opencode with missing task tools.\n"
                    f"--- stderr ---\n{check.stderr}\n--- stdout ---\n{check.stdout}"
                )
            container_name = f"daedalus-infer-{os.getpid()}-{traceid}"
            command = ras_eval_next_common.build_agent_command(
                spec,
                sandbox_dir,
                config_content,
                config.model,
                api_keys,
                toolkit_root=toolkit_root,
                name=container_name,
                runtime_verification=config.runtime_verification,
                **({"information_flow": True} if config.information_flow else {}),
            )
        except BaseException as error:
            try:
                if audit_dir is not None:
                    _finish_information_flow(audit_dir, config, traceid, {
                        **audit_status, "error_type": type(error).__name__, "error": str(error)[-8000:],
                    })
            finally:
                cleanup_sandbox_artifacts(sandbox_dir)
                if config.runtime_verification:
                    from src.evaluator.spec.runtime import cleanup_runtime_dir

                    cleanup_runtime_dir(sandbox_dir)
                ras_eval_next_common.cleanup_materialized_toolkit(sandbox_dir)
                shutil.rmtree(sandbox_dir, ignore_errors=True)
                try:
                    sandbox_dir.parent.rmdir()
                except OSError:
                    pass
            if config.information_flow and isinstance(error, Exception):
                raise RuntimeError(f"information flow task initialization failed：{type(error).__name__}；see audit output for details") from None
            raise
        stdin_input = prompt
        if not config.information_flow:
            limiter.wait()
    try:
        audit_status = {"status": "agent_error"}
        stdout, stderr, returncode, timed_out = _run_agent_command(
            command,
            env,
            stdin_input,
            config.timeout,
            container_name if config.sandbox == "docker" else None,
        )
        if config.information_flow:
            secrets = [value for key, value in env.items()
                       if re.search(r"(?:^|_)(?:api_key|access_token|auth_token|secret|password|credential)$", key, re.I)
                                          and value and len(value) >= 6]
            for secret in sorted(secrets, key=len, reverse=True):
                stdout, stderr = stdout.replace(secret, "[REDACTED]"), stderr.replace(secret, "[REDACTED]")
            audit_status.update({"returncode": returncode, "timed_out": timed_out, "timeout_seconds": config.timeout})
            if stderr:
                audit_status["stderr_tail"] = stderr[-4000:]
        if timed_out:
            stderr = f"Timed out after {config.timeout} seconds.\n{stderr}"
            print(
                f"[WARN] traceid={traceid}: opencode timed out after {config.timeout}s; "
                "keeping the partial trajectory for evaluation."
            )
        elif returncode != 0:
            # opencode exits 1 as soon as *any* session error was observed, even
            # when the session recovered and finished normally afterwards (an
            # auto-rejected permission, a transient provider error, an
            # auto-compaction). Failing the sample here would discard a complete
            # trajectory, so only a run that emitted no events at all (broken
            # sandbox / config / MCP server / missing binary) stays fatal.
            if not _has_agent_events(stdout):
                raise RuntimeError(
                    f"opencode run failed for traceid {traceid} with exit code "
                    f"{returncode} without emitting any event.\n"
                    f"--- stderr ---\n{stderr[-4000:]}\n--- stdout ---\n{stdout[-4000:]}"
                )
            print(
                f"[WARN] traceid={traceid}: opencode exited with code {returncode} "
                "after a session error; keeping the trajectory for evaluation."
            )

        response_options: dict[str, Any] = {}
        if audit_dir is not None:
            registry = audit_dir / "main_session.json"
            if registry.is_file() and not registry.is_symlink():
                session_id = json.loads(registry.read_text(encoding="utf-8"))["session_id"]
                if not isinstance(session_id, str) or not session_id:
                    raise ValueError("main session registration is invalid")
                response_options["session_id"] = session_id
            else:
                audit_status["session_registry"] = "missing"

        if source == "agentdojo":
            tool_providers = list(json.loads(env["OPENCODE_CONFIG_CONTENT"])["mcp"].keys())
            messages = parse_opencode_response(sample, tool_providers, stdout, stderr, returncode)
        elif source == "skill_inject":
            messages = parse_opencode_response(sample, [], stdout, stderr, returncode, **response_options)
            (sandbox_dir / "agent_stdout.txt").write_text(
                render_transcript([m for m in messages if m["role"] != "system"]),
                encoding="utf-8",
            )
            if stderr:
                (sandbox_dir / "agent_stderr.txt").write_text(stderr, encoding="utf-8")
        elif source == "ras-eval-next":
            messages = parse_opencode_response(sample, ["ras_eval_next"], stdout, stderr, returncode, **response_options)
            messages = ras_eval_next_common.normalize_messages(meta, messages)
        row: dict[str, Any] = {"traceid": traceid, "response": messages}
        if timed_out:
            row["timeout"] = True
            row["timeout_seconds"] = config.timeout
            row["stderr_tail"] = stderr[-4000:]
        elif returncode != 0:
            row["agent_exit_code"] = returncode
            row["stderr_tail"] = stderr[-4000:]
        audit_status["status"] = "timeout" if timed_out else "completed" if returncode == 0 else "agent_error"
        if config.information_flow and stderr:
            audit_status["stderr_tail"] = stderr[-4000:]
        return row
    except BaseException as error:
        audit_status.update({"error_type": type(error).__name__, "error": str(error)[-8000:]})
        if config.information_flow and isinstance(error, Exception):
            raise RuntimeError(f"information flow task execution failed：{type(error).__name__}；see audit output for details") from None
        raise
    finally:
        try:
            if audit_dir is not None:
                _finish_information_flow(audit_dir, config, traceid, audit_status)
        finally:
            if source in {"skill_inject", "ras-eval-next"}:
                cleanup_sandbox_artifacts(sandbox_dir)
            if source == "ras-eval-next":
                ras_eval_next_common.cleanup_materialized_toolkit(sandbox_dir)
            if (
                source == "ras-eval-next" and not config.keep_sandbox
            ) or (
                source == "skill_inject"
                and meta.get("attack_type") == "cia"
                and not config.keep_sandbox
            ):
                shutil.rmtree(sandbox_dir, ignore_errors=True)
                try:
                    sandbox_dir.parent.rmdir()
                except OSError:
                    pass



def traceid_filter(samples: Iterable[dict[str, Any]], config: RunnerConfig, exist_traceids: list[int]) -> list[dict[str, Any]]:
    if config.traceid is None:
        if config.skip_exist_traceid:
            samples = [sample for sample in samples if int(sample["traceid"]) not in exist_traceids]
            return samples
        else:
            return samples
    else:
        for sample in samples:
            if sample["traceid"] == config.traceid:
                return [sample]
    return []


def run(config: RunnerConfig) -> list[dict[str, Any]]:
    with open(config.input_path, "r", encoding="utf-8") as file:
        samples = [json.loads(line) for line in file]
    if config.limit is not None:
        samples = samples[:config.limit]
    if config.output_path.exists():
        with open(config.output_path, "r", encoding="utf-8") as file:
            exist_outputs = [json.loads(line) for line in file]
            exist_traceids = [int(output["traceid"]) for output in exist_outputs]
    else:
        config.output_path.parent.mkdir(parents=True, exist_ok=True)
        exist_traceids = []
    samples = traceid_filter(samples, config, exist_traceids)

    limiter = RateLimiter(config.qps)
    results: list[dict[str, Any]] = []
    write_lock = threading.Lock()
    # Keep the output file open for the whole run and force flush + fsync after
    # every result so each finished sample is persisted to disk immediately,
    # instead of lingering in Python/OS buffers with an unknown update delay.
    with config.output_path.open("a", encoding="utf-8") as out_file:
        with ThreadPoolExecutor(max_workers=max(1, config.parallel)) as executor:
            futures = [executor.submit(run_sample, sample, config, limiter) for sample in samples]
            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Inference",
                unit="sample",
            ):
                result = future.result()
                results.append(result)
                with write_lock:
                    out_file.write(json.dumps(result, ensure_ascii=False) + "\n")
                    out_file.flush()
                    os.fsync(out_file.fileno())
    results.sort(key=lambda item: int(item["traceid"]))
    try:
        (config.output_path.parent / f"{config.output_path.stem}_sandboxes").rmdir()
    except OSError:
        pass
    return results
