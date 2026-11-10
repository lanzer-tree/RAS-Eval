"""Output-directory workspace setup for the generation flywheel.

Reuses the refine workspace initializer (copies toolkits + environment into the
output directory so iterative LLM edits never touch the repository originals),
then additionally seeds the input dataset as a read-only ``base.jsonl`` used for
excluding already-existing tool combinations.
"""
from __future__ import annotations

import shutil
from pathlib import Path

from src.indra.refine.workspace import ensure_workspace as _ensure_refine_workspace


def ensure_workspace(output_dir: Path, input_path: Path) -> None:
    """Idempotently initialize the generation workspace under *output_dir*.

    Creates (only when missing):
      {output_dir}/toolkits/         -- copy of src/toolkits/ras_eval/
      {output_dir}/environment/      -- copy of data/ras_eval/environment/
      {output_dir}/dataset/base.jsonl -- copy of the input dataset (seed)
      {output_dir}/dataset/generated.jsonl is written incrementally by the runner.
    """
    output_dir = Path(output_dir)
    _ensure_refine_workspace(output_dir)

    base_path = output_dir / "dataset" / "base.jsonl"
    if not base_path.exists():
        shutil.copyfile(input_path, base_path)
