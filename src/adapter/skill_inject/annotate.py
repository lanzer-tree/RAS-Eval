from __future__ import annotations

from pathlib import Path
from typing import Any

from src.adapter.skill_inject.common import build_sandbox
from src.adapter.skill_inject.judge import build_injection_prompt, build_task_prompt

PROMPT_PATH = Path(__file__).parent / "annotate_prompt.md"
SECURITY_PROMPT_PATH = Path(__file__).parent / "annotate_security_prompt.md"
COMMAND_LOGGER = "trap 'echo \"$BASH_COMMAND\" >> /workspace/.command_history' DEBUG\n"
INFERENCE_ENV = {"BASH_ENV": "/workspace/.bash_command_logger.sh"}


def permission(sample: dict[str, Any]) -> dict[str, Any]:
    return {
        "*": "allow",
        "question": "deny",
        "external_directory": {"*": "allow"},
        "doom_loop": "allow",
        "skill": {"*": "deny", sample["meta"]["skill"]: "allow"},
    }


def build_environment(sample: dict[str, Any], env_dir: Path) -> None:
    build_sandbox(sample, env_dir)
    (env_dir / ".bash_command_logger.sh").write_text(COMMAND_LOGGER, encoding="utf-8")


def inference_binds(trace_dir: Path) -> list[tuple[str, str, bool]]:
    env_dir = Path(trace_dir) / "environment"
    binds = [(str(env_dir.absolute()), "/workspace", False)]
    root_dir = env_dir / "_root_files"
    if root_dir.exists():
        for item in root_dir.iterdir():
            binds.append((str(item.absolute()), f"/{item.name}", True))
    return binds


def agent_prompt(sample: dict[str, Any], mode: str, max_iterations: int) -> str:
    meta = sample["meta"]
    if mode == "attack":
        prompt = SECURITY_PROMPT_PATH.read_text(encoding="utf-8")
        prompt = prompt.replace("{{INJECTION_TEXT}}", meta["injection_text"])
        prompt = prompt.replace("{{LINE_INJECTION}}", meta["line_injection"])
        prompt = prompt.replace("{{ATTACK_TYPE}}", meta["attack_type"])
        prompt = prompt.replace(
            "{{OFFICIAL_JUDGE_PROMPT}}", build_injection_prompt(meta["injection_text"], meta.get("judge_prompt"))
        )
    else:
        prompt = PROMPT_PATH.read_text(encoding="utf-8")
        prompt = prompt.replace("{{OFFICIAL_JUDGE_PROMPT}}", build_task_prompt(meta["task_prompt"]))
    prompt = prompt.replace("{{TASK_PROMPT}}", sample["prompt"])
    prompt = prompt.replace("{{USER_TASK}}", meta["task_prompt"])
    prompt = prompt.replace("{{SKILL}}", meta["skill_name"])
    prompt = prompt.replace("{{TASK_FILES}}", "\n".join(f"- `{name}`" for name in meta.get("task_files", {})))
    return prompt.replace("{{MAX_ITERATIONS}}", str(max_iterations))


def result_row(sample: dict[str, Any], specs: dict[str, list[dict[str, str]]]) -> dict[str, Any]:
    meta = dict(sample["meta"])
    meta["completion_specifications"] = specs.get("completion_specifications", [])
    meta["safety_specifications"] = specs.get("safety_specifications", [])
    meta["security_specifications"] = specs.get("security_specifications", [])
    return {
        "traceid": sample["traceid"],
        "prompt": sample["prompt"],
        "source": "skill_inject",
        "meta": meta,
    }
