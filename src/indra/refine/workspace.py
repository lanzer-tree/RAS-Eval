"""Resource workspace management for the flywheel refine pipeline.

Copies toolkits and environment data from the repository into an isolated
output directory so that iterative LLM fixes never touch the original sources.
"""
from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLKITS_SRC = REPO_ROOT / "src" / "toolkits" / "ras_eval"
ENVIRONMENT_SRC = REPO_ROOT / "data" / "ras_eval" / "environment"


def ensure_workspace(output_dir: Path) -> None:
    """Idempotently initialize the workspace under *output_dir*.

    Creates:
      {output_dir}/toolkits/   -- full copy of src/toolkits/ras_eval/
      {output_dir}/environment/ -- full copy of data/ras_eval/environment/
      {output_dir}/dataset/    -- directory for refined output JSONL
    """
    output_dir = Path(output_dir)
    toolkits_dst = output_dir / "toolkits"
    environment_dst = output_dir / "environment"
    dataset_dst = output_dir / "dataset"

    if not toolkits_dst.exists():
        shutil.copytree(TOOLKITS_SRC, toolkits_dst)

    if not environment_dst.exists():
        shutil.copytree(ENVIRONMENT_SRC, environment_dst)

    dataset_dst.mkdir(parents=True, exist_ok=True)
