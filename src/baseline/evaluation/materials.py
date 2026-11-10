"""Assemble the judge material folder for one trajectory.

The same folder feeds both baselines: the LLM judge gets it rendered into one
text bundle (``render``), the agent judge gets it bind-mounted at ``/workspace``.

Only these sample fields may be read, so the judge never sees the LTL answer:
``prompt``, ``meta.system_prompt``, ``meta.tools``, ``meta.toolkits``,
``meta.toolkit_root``, ``meta.environment``, ``meta.skill``, ``meta.skill_name``,
``meta.task_files`` -- plus the recorded ``response`` messages. Everything that
encodes the ground truth is off limits: ``*_specifications``, ``meta.attack``,
``attack_type``, ``attack_category``, ``behavior_id``, ``security_success``,
``security_attempts``, ``security_attempt_history``, ``attack_target_*``,
``base_traceid``, ``condition`` and the response's ``ltl`` field.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.adapter.ras_eval_next.common import materialize_toolkit_root
from src.adapter.skill_inject import archive

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLKIT_ROOT = REPO_ROOT / "src" / "toolkits" / "ras_eval"
SKILL_DATA_ROOT = REPO_ROOT / "data" / "skill_inject"
ENV_SEED = REPO_ROOT / "data" / "ras_eval" / "environment"

# Rendered in this order for the LLM judge; the agent judge browses the same names.
SECTIONS = (
    ("TASK", "task.md"),
    ("AVAILABLE TOOLS (schemas and implementation source)", "tools"),
    ("SKILL PACKAGE AVAILABLE TO THE AGENT", "skill"),
    ("TASK FILES PRESENT IN THE WORKSPACE", "task_files"),
    ("INITIAL ENVIRONMENT SETUP", "environment_setup.json"),
    ("AGENT TRAJECTORY", "trajectory.md"),
)


def build(sample: dict[str, Any], transcript: str, judge_dir: Path, dataset_path: Path) -> None:
    """Write the material folder: task, trajectory, tool source, skill, env setup."""
    judge_dir.mkdir(parents=True, exist_ok=True)
    meta = sample["meta"]
    (judge_dir / "task.md").write_text(
        f"# User Request\n\n{sample['prompt']}\n\n"
        f"# Agent System Prompt\n\n{meta.get('system_prompt', '')}\n",
        encoding="utf-8",
    )
    (judge_dir / "trajectory.md").write_text(transcript, encoding="utf-8")
    (judge_dir / "environment_setup.json").write_text(
        json.dumps(meta.get("environment") or [], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if sample["source"] == "ras-eval-next":
        # cia-tool samples carry a task-local (attacked) copy of the toolkits.
        root = materialize_toolkit_root(sample, dataset_path, judge_dir) or TOOLKIT_ROOT
        for toolkit in meta["toolkits"]:
            dest = judge_dir / "tools" / toolkit
            dest.mkdir(parents=True, exist_ok=True)
            (dest / f"{toolkit}.json").write_bytes((root / toolkit / "json" / f"{toolkit}.json").read_bytes())
            (dest / f"{toolkit}.py").write_bytes((root / toolkit / "function" / f"{toolkit}.py").read_bytes())
    else:
        # skill-inject: the skill's instructions and scripts are what the agent
        # actually executed; the ooxml/ reference schemas are noise, so skip them.
        skill_name = meta["skill_name"]
        archive.copy_into(SKILL_DATA_ROOT, f"skills/{skill_name}/SKILL.md", judge_dir / "skill" / "SKILL.md")
        archive.copy_into(SKILL_DATA_ROOT, f"skills/{skill_name}/scripts", judge_dir / "skill" / "scripts")
        for filename, rel_path in meta.get("task_files", {}).items():
            archive.copy_into(SKILL_DATA_ROOT, rel_path, judge_dir / "task_files" / filename)


def _render_path(path: Path, judge_dir: Path) -> str:
    try:
        body = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        body = f"[binary file, {path.stat().st_size} bytes]"
    return f"### {path.relative_to(judge_dir)}\n\n{body}"


def render(judge_dir: Path) -> str:
    """Flatten the material folder into one text bundle for the LLM judge."""
    blocks: list[str] = []
    for title, name in SECTIONS:
        path = judge_dir / name
        if not path.exists():
            continue
        if path.is_dir():
            files = sorted(item for item in path.rglob("*") if item.is_file())
            body = "\n\n".join(_render_path(item, judge_dir) for item in files)
        else:
            body = path.read_text(encoding="utf-8")
        blocks.append(f"## {title}\n\n{body}")
    return "\n\n".join(blocks)
