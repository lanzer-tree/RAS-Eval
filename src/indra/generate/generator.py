"""LLM-driven generation of a single ras-eval-next sample from a tool combination.

Runs opencode inside the sandbox as a pure text generator (no MCP, all tools
denied): it receives the target tools' schemas and returns a JSON test case
(prompt + environment setup) or a refusal. The parsed output is assembled into a
standard ras-eval-next sample (without LTL specifications).
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.indra.generate.combinations import Combination
from src.runner.opencode_runner import _load_env
from src.runner.sandbox import SandboxSpec, build_command, opencode_config_bind, opencode_home_path, cleanup_sandbox_artifacts

REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPT_PATH = REPO_ROOT / "src" / "indra" / "prompts" / "generate_base.md"


@dataclass(frozen=True)
class GenerateConfig:
    input_path: Path
    output_dir: Path
    model: str
    sandbox: str
    os: str
    depth: int
    limit: int | None = None
    max_per_toolkit: int | None = None
    disable_native_tools: bool = False
    seed: int = 0
    parallel: int = 1
    qps: float = 1.0
    timeout: int = 900
    apptainer_path: str | None = None
    image: str | None = None
    # Present so this config can be passed to refine.executor.run_inference.
    traceid: int | None = None
    skip_exist_traceid: bool = False


# Built-in opencode tools the agent may combine with toolkit tools when native
# tools are enabled (kept in sync with refine.executor inference permissions).
_NATIVE_TOOLS_NOTE = (
    "The agent will ALSO have opencode's built-in tools available: a bash shell "
    "and file read/write/edit plus grep/glob search. You MAY design a task that "
    "combines these with the target toolkit tools (for example, read a local "
    "file and then act on it through the toolkit). However the task MUST still "
    "genuinely require ALL of the target toolkit tools above -- it must NOT be "
    "solvable using built-in tools alone."
)
_NATIVE_TOOLS_DISABLED = (
    "The agent will only have this toolkit's tools; opencode's built-in tools are "
    "disabled. Design a task solvable with the target toolkit tools alone."
)


def _build_generate_prompt(combo: Combination, cfg: GenerateConfig, retry_feedback: str) -> str:
    template = PROMPT_PATH.read_text(encoding="utf-8")
    specs = json.dumps(list(combo.specs), ensure_ascii=False, indent=2)
    all_tools = ", ".join(f"`{name}`" for name in combo.all_tools)
    native = _NATIVE_TOOLS_DISABLED if cfg.disable_native_tools else _NATIVE_TOOLS_NOTE
    prompt = template.replace("{{TOOLKIT}}", combo.toolkit)
    prompt = prompt.replace("{{TOOL_SPECS}}", specs)
    prompt = prompt.replace("{{ALL_TOOLS}}", all_tools)
    prompt = prompt.replace("{{NATIVE_TOOLS}}", native)
    prompt = prompt.replace("{{RETRY_FEEDBACK}}", retry_feedback or "(none)")
    return prompt


def _get_generate_config(model: str) -> str:
    """opencode config for pure text generation: provider only, all tools denied."""
    _load_env()
    base_url = os.environ["OPENAI_BASE_URL"]
    api_key = os.environ["OPENAI_API_KEY"]
    model_provider = model.split("/")[0]
    model_name = model.split("/")[1]
    config = {
        "provider": {
            model_provider: {
                "npm": "@ai-sdk/openai-compatible",
                "name": model_provider,
                "options": {"baseURL": base_url, "apiKey": api_key},
                "models": {model_name: {}},
            }
        },
        "permission": {
            "bash": "deny", "edit": "deny", "write": "deny", "read": "deny",
            "grep": "deny", "glob": "deny", "lsp": "deny", "patch": "deny",
            "skill": "deny", "todowrite": "deny", "webfetch": "deny",
            "websearch": "deny", "question": "deny", "task": "deny",
        },
    }
    return json.dumps(config, ensure_ascii=False)


def _extract_text(stdout: str) -> str:
    """Concatenate all assistant ``text`` parts from the opencode json stream."""
    texts = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "text" and "part" in event:
            texts.append(event["part"].get("text", ""))
    return "\n".join(texts)


def _parse_json_object(text: str) -> dict[str, Any] | None:
    """Extract the JSON object from the model's reply (fenced or bare)."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else None
    if candidate is None:
        start = text.find("{")
        end = text.rfind("}")
        candidate = text[start:end + 1] if start != -1 and end > start else None
    if candidate is None:
        return None
    try:
        parsed = json.loads(candidate)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def generate_sample(combo: Combination, cfg: GenerateConfig, retry_feedback: str = "") -> dict[str, Any]:
    """Run the generator LLM once. Returns the parsed JSON dict.

    On success the dict has ``prompt``/``system_prompt``/``environment``; on
    refusal it has ``refuse: True`` and ``reason``. Unparseable output is
    reported as a refusal so the caller can skip cleanly.
    """
    gen_prompt = _build_generate_prompt(combo, cfg, retry_feedback)

    sandbox_root = Path(cfg.output_dir) / "sandboxes"
    sandbox_root.mkdir(parents=True, exist_ok=True)
    sandbox_dir = sandbox_root / f"GEN-{combo.traceid}"
    if sandbox_dir.exists():
        shutil.rmtree(sandbox_dir)
    sandbox_dir.mkdir(parents=True)

    config_bind, config_env = opencode_config_bind(sandbox_dir, _get_generate_config(cfg.model))
    binds = [
        (str(sandbox_dir.absolute()), "/workspace", False),
        config_bind,
    ]
    env = {
        **config_env,
        "OPENCODE_DISABLE_AUTOUPDATE": "1",
        "NODE_TLS_REJECT_UNAUTHORIZED": "0",
    }
    spec = SandboxSpec(cfg.sandbox, cfg.image, cfg.os, cfg.apptainer_path)
    args = ["opencode", "run", "--model", cfg.model, "--format", "json"]
    command = build_command(spec, binds, env, args, writable_home=opencode_home_path(sandbox_dir))

    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            env=os.environ.copy(),
            input=gen_prompt,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=cfg.timeout,
            check=False,
        )
        stdout = completed.stdout
    except subprocess.TimeoutExpired as exc:
        stdout = exc.stdout or ""
        if isinstance(stdout, bytes):
            stdout = stdout.decode("utf-8", errors="replace")
    finally:
        # Always drop the disposable sandbox + config + writable home so long
        # runs (or crashes mid-run) never accumulate per-task directories.
        cleanup_sandbox_artifacts(sandbox_dir)
        shutil.rmtree(sandbox_dir, ignore_errors=True)

    parsed = _parse_json_object(_extract_text(stdout))
    if parsed is None:
        return {"refuse": True, "reason": "generator produced no parseable JSON"}
    return parsed


def build_sample(combo: Combination, gen_output: dict[str, Any]) -> dict[str, Any]:
    """Assemble a standard ras-eval-next sample (no LTL specs) from generator output."""
    environment = gen_output.get("environment") or []
    return {
        "traceid": combo.traceid,
        "prompt": gen_output["prompt"],
        "source": "ras-eval-next",
        "meta": {
            "agent": "GeneralAgent",
            "system_prompt": gen_output.get("system_prompt", ""),
            "tools": list(combo.all_tools),
            "toolkits": [combo.toolkit],
            "environment": environment,
            "docker_image": "ras-eval-agent:latest",
            "combination": list(combo.tools),
        },
    }
