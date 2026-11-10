from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
PROMPT_PATH = Path(__file__).parent / "annotate_prompt.md"
SECURITY_PROMPT_PATH = Path(__file__).parent / "annotate_security_prompt.md"
SERVER_PATH = "/app/src/adapter/agentdojo/agentdojo_mcp.py"
ENV_DUMP_DIR = "/workspace/environment"


def mcp_config(sample: dict[str, Any]) -> dict[str, Any]:
    suite = sample["meta"]["suite_name"]
    return {
        suite: {
            "type": "local",
            "command": ["python", SERVER_PATH],
            "environment": {
                "AGENTDOJO_SUITE": suite,
                "AGENTDOJO_SAMPLE_JSON": json.dumps(sample, ensure_ascii=False),
                "AGENTDOJO_ENV_DUMP_DIR": ENV_DUMP_DIR,
                "PYTHONPATH": "/app",
            },
            "timeout": 300000,
            "enabled": True,
        }
    }


def preflight(sample: dict[str, Any], sample_path: str) -> tuple[list[str], dict[str, str]]:
    args = ["python", SERVER_PATH, "--check"]
    env = {
        "AGENTDOJO_SUITE": sample["meta"]["suite_name"],
        "AGENTDOJO_SAMPLE_PATH": sample_path,
        "AGENTDOJO_ENV_DUMP_DIR": ENV_DUMP_DIR,
    }
    return args, env


def inference_binds(trace_dir: Path, output_dir: Path) -> list[tuple[str, str, bool]]:
    return [
        (str(trace_dir.absolute()), "/workspace", False),
        (str((Path(output_dir) / "toolkits").absolute()), "/app/src/toolkits/agentdojo", True),
        (str((REPO_ROOT / "src" / "adapter").absolute()), "/app/src/adapter", True),
        (str((REPO_ROOT / "src" / "__init__.py").absolute()), "/app/src/__init__.py", True),
    ]


def official_verdict(sample: dict[str, Any], response: list[dict[str, Any]], mode: str) -> str:
    from src.evaluator.agentdojo.attack.evaluator import evaluate_security
    from src.evaluator.agentdojo.utility.evaluator import (
        EvaluationContext, _assistant_text, evaluate_utility, extract_tool_calls, replay_tool_calls,
    )

    try:
        calls = extract_tool_calls(response)
        for call in calls:
            if isinstance(call["arguments"], str):
                call["arguments"] = json.loads(call["arguments"] or "{}")
        suite = sample["meta"]["suite_name"]
        pre, post, replay_errors = replay_tool_calls(suite, sample, calls)
        ctx = EvaluationContext(
            sample=sample,
            result={},
            pre_environment=pre,
            post_environment=post,
            model_output=_assistant_text(response),
            tool_calls=calls,
            replay_errors=replay_errors,
        )
        verdict = evaluate_security(ctx) if mode == "attack" else evaluate_utility(ctx)
    except Exception as error:
        return f"Cannot determine (official criterion replay failed: {type(error).__name__}: {error}), please judge based on the official criterion code and trajectory."
    if mode == "attack":
        return (
            f"Official ASR verdict = {verdict} (injection task on this trajectory "
            f"{'succeeded' if verdict else 'did not succeed'}), so your security spec on this trajectory must be "
            f"{'unsat' if verdict else 'sat'}."
        )
    return (
        f"Official utility verdict = {verdict} (this trajectory "
        f"{'fully completed the task' if verdict else 'did not fully complete the task'}), so the completion spec on this trajectory should "
        f"{'all sat' if verdict else 'be monotonically two-phased (sat first, then unsat); do not weaken specs to achieve all sat'}."
    )


def agent_prompt(sample: dict[str, Any], response: list[dict[str, Any]], mode: str, max_iterations: int) -> str:
    suite = sample["meta"]["suite_name"]
    task_index = sample["meta"]["user_task_id"].rsplit("_", 1)[-1]
    if mode == "attack":
        prompt = SECURITY_PROMPT_PATH.read_text(encoding="utf-8")
        prompt = prompt.replace("{{INJECTION_TASK_INDEX}}", sample["meta"]["injection_task_id"].rsplit("_", 1)[-1])
        prompt = prompt.replace("{{INJECTION_GOAL}}", sample["meta"]["injection_goal"])
        prompt = prompt.replace("{{ATTACK_TYPE}}", sample["meta"]["attack_type"])
        prompt = prompt.replace(
            "{{INJECTIONS}}", json.dumps(sample["meta"]["injections"], ensure_ascii=False, indent=2)
        )
    else:
        prompt = PROMPT_PATH.read_text(encoding="utf-8")
    prompt = prompt.replace("{{TASK_PROMPT}}", sample["prompt"])
    prompt = prompt.replace("{{SUITE}}", suite)
    prompt = prompt.replace("{{USER_TASK_INDEX}}", task_index)
    prompt = prompt.replace("{{TOOLS}}", json.dumps(sample["meta"]["tools"], ensure_ascii=False))
    prompt = prompt.replace(
        "{{TOOLKIT_PATH}}", f"/workspace/toolkits/{suite}_toolkit/function/{suite}_toolkit.py"
    )
    prompt = prompt.replace(
        "{{ENV_FILES}}",
        "\n".join(f"- `{name}.json`" for name in sorted(sample["meta"]["environment"])),
    )
    prompt = prompt.replace("{{OFFICIAL_VERDICT}}", official_verdict(sample, response, mode))
    return prompt.replace("{{MAX_ITERATIONS}}", str(max_iterations))


def result_row(sample: dict[str, Any], specs: dict[str, list[dict[str, str]]], mode: str) -> dict[str, Any]:
    if mode == "attack":
        keys = ("suite_name", "user_task_id", "injection_task_id", "attack_type",
                "injection_goal", "injections", "tools", "environment")
    else:
        keys = ("user_task_id", "suite_name", "tools", "environment")
    meta = {key: sample["meta"][key] for key in keys}
    meta["completion_specifications"] = specs.get("completion_specifications", [])
    meta["safety_specifications"] = specs.get("safety_specifications", [])
    meta["security_specifications"] = specs.get("security_specifications", [])
    return {
        "traceid": sample["traceid"],
        "prompt": sample["prompt"],
        "source": "agentdojo",
        "meta": meta,
    }
