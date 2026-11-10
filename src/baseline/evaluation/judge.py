"""Judge one prepared material folder, as an LLM call or as an opencode agent run.

Both judges answer with the same JSON object, so their rows are directly
comparable. ``security_judge`` is ``True`` when the run is safe, matching the
polarity of a satisfied LTL security spec.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from src.baseline.evaluation import materials
from src.runner.opencode_runner import _load_env, _run_agent_command
from src.runner.sandbox import SandboxSpec, build_command, opencode_config_bind, opencode_home_path

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"
REASON_KEYS = ("utility_reason", "risk_source", "failure_mode", "risk_consequence", "security_reason")
UTILITY_VERDICTS = {"complete": True, "incomplete": False}
SECURITY_VERDICTS = {"safe": True, "unsafe": False}


def client():
    """One shared OpenAI-compatible client for the LLM judge and for the
    compaction call."""
    from openai import OpenAI

    _load_env()
    return OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["OPENAI_BASE_URL"],
        max_retries=5,
        timeout=600,
    )


def api_model(model: str) -> str:
    """The opencode provider prefix does not resolve against the raw endpoint."""
    return model.split("/", 1)[1] if "/" in model else model


def output_format(perturbation: str) -> str:
    name = "output_binary.md" if perturbation == "remove_reason" else "output_full.md"
    return (PROMPTS_DIR / name).read_text(encoding="utf-8")


def parse(text: str, detailed: bool = True) -> dict[str, Any]:
    """Pull the verdict object out of the judge reply. Anything we cannot read as
    two binary verdicts is an error row. ``detailed`` is off for the
    ``remove_reason`` perturbation, whose verdict carries no attribution."""
    decoder = json.JSONDecoder()
    payload: dict[str, Any] | None = None
    index = 0
    while True:
        start = text.find("{", index)
        if start == -1:
            break
        try:
            candidate, index = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            index = start + 1
            continue
        if isinstance(candidate, dict) and "utility" in candidate and "security" in candidate:
            payload = candidate
    if payload is None:
        return {"utility_judge": "error", "security_judge": "error", "reason": {"raw": text[-2000:]}}
    utility = UTILITY_VERDICTS.get(str(payload["utility"]).strip().lower())
    security = SECURITY_VERDICTS.get(str(payload["security"]).strip().lower())
    if utility is None or security is None:
        return {"utility_judge": "error", "security_judge": "error", "reason": {"raw": json.dumps(payload, ensure_ascii=False)}}
    return {
        "utility_judge": utility,
        "security_judge": security,
        "reason": {key: payload[key] for key in REASON_KEYS if key in payload} if detailed else {},
    }


def build_llm_prompt(judge_dir: Path, perturbation: str) -> str:
    """Render the exact user message sent to the LLM judge."""
    prompt = (PROMPTS_DIR / "judge_llm.md").read_text(encoding="utf-8")
    prompt = prompt.replace("{{OUTPUT}}", output_format(perturbation))
    return prompt.replace("{{MATERIALS}}", materials.render(judge_dir))


def judge_llm(judge_dir: Path, perturbation: str, llm, model: str) -> dict[str, Any]:
    prompt = build_llm_prompt(judge_dir, perturbation)
    completion = llm.chat.completions.create(
        model=api_model(model), messages=[{"role": "user", "content": prompt}], temperature=0.0,
    )
    return parse(completion.choices[0].message.content or "", perturbation != "remove_reason")


def opencode_config(model: str) -> str:
    """opencode config for the judge: the repo provider, all skills denied (the
    judge inspects the skill package as text, it must never load it)."""
    _load_env()
    provider_id, _, model_id = model.partition("/")
    config = {
        "provider": {
            provider_id: {
                "npm": "@ai-sdk/openai-compatible",
                "name": provider_id,
                "options": {"baseURL": os.environ["OPENAI_BASE_URL"], "apiKey": os.environ["OPENAI_API_KEY"]},
                "models": {model_id: {}},
            }
        },
        "permission": {
            "*": "allow",
            "question": "deny",
            "external_directory": {"*": "allow"},
            "doom_loop": "allow",
            "skill": {"*": "deny"},
        },
    }
    return json.dumps(config, ensure_ascii=False)


def judge_agent(
    judge_dir: Path,
    sample: dict[str, Any],
    perturbation: str,
    model: str,
    spec: SandboxSpec,
    timeout: int,
) -> dict[str, Any]:
    prompt = (PROMPTS_DIR / "judge_agent.md").read_text(encoding="utf-8").replace("{{OUTPUT}}", output_format(perturbation))
    config_bind, config_env = opencode_config_bind(judge_dir, opencode_config(model))
    binds = [(str(judge_dir.absolute()), "/workspace", False), config_bind]
    if sample["source"] == "ras-eval-next":
        binds.append((str(materials.ENV_SEED.absolute()), "/environment_seed", True))
    env = {**config_env, "OPENCODE_DISABLE_AUTOUPDATE": "1", "NODE_TLS_REJECT_UNAUTHORIZED": "0"}
    name = f"judge-{judge_dir.name}"
    command = build_command(
        spec,
        binds,
        env,
        ["opencode", "run", "--model", model, "--format", "json"],
        writable_home=opencode_home_path(judge_dir),
        name=name,
    )
    _, stderr, returncode, timed_out = _run_agent_command(command, os.environ.copy(), prompt, timeout, name)
    result_path = judge_dir / "judge_result.json"
    if not result_path.exists():
        return {
            "utility_judge": "error",
            "security_judge": "error",
            "reason": {"error": f"judge_result.json missing (exit={returncode}, timed_out={timed_out})", "raw": stderr[-2000:]},
        }
    return parse(result_path.read_text(encoding="utf-8", errors="replace"), perturbation != "remove_reason")
