"""Merge a generated CIA-skill attack batch into the mainline dataset layout.

``flywheel_infer.py --attack_type cia --benchmark skill_inject`` writes a batch
under ``data/output/<batch>``::

    dataset/attack_generated.jsonl   # the attack samples
    skill_inject/{skills,task_files,task_scripts}/   # the assets they reference

Mainline inference/evaluation instead reads the dataset from ``data/input`` and
the assets from ``data/skill_inject`` as three zip archives (see
``src.adapter.skill_inject.archive``). This module performs that move:

* the samples are normalised through ``clean_cia_attack_sample`` and stripped of
  ``meta.data_root`` so they resolve against the canonical ``data/skill_inject``;
* a fixed-seed random subset is written as the ``*_small_*`` dataset;
* the three asset trees are packed into ``data/skill_inject/<tree>.zip`` after the
  archives already there are kept aside as ``<tree>_v1.zip``.

Usage::

    uv run python -m src.utils.dataset_utils.cia_skill_utils \
        --generated_dir data/output/cia-test-batch
"""
from __future__ import annotations

import argparse
import copy
import json
import random
import shutil
from pathlib import Path
from typing import Any

from src.adapter.skill_inject import archive
from src.indra.generate.cia_task import clean_cia_attack_sample

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = REPO_ROOT / "data" / "skill_inject"
DEFAULT_GENERATED_DIR = REPO_ROOT / "data" / "output" / "cia-test-batch"
DEFAULT_DATASET_OUT = REPO_ROOT / "data" / "input" / "ras_eval_next_cia_skill_attack_v2.jsonl"
DEFAULT_SMALL_OUT = REPO_ROOT / "data" / "input" / "ras_eval_next_cia_skill_small_attack_v2.jsonl"
DEFAULT_SMALL_SIZE = 200
DEFAULT_SEED = 42
DEFAULT_LEGACY_SUFFIX = "v1"


def _resolve(path: Path | str) -> Path:
    path = Path(path)
    return path if path.is_absolute() else REPO_ROOT / path


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"input file does not exist: {path}")
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON at {path}:{line_no}: {exc}") from exc
        if not isinstance(value, dict):
            raise ValueError(f"JSONL row must be an object at {path}:{line_no}")
        rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_sample(sample: dict[str, Any]) -> dict[str, Any]:
    """Bring one generated sample into the mainline inference schema.

    ``meta.data_root`` points at the generating batch directory, which no longer
    holds the assets once they are packed into ``data/skill_inject``; dropping it
    makes ``src.adapter.skill_inject.common`` fall back to the canonical root.
    """
    cleaned = clean_cia_attack_sample(copy.deepcopy(sample))
    cleaned["meta"].pop("data_root", None)
    return cleaned


def load_attack_samples(source: Path) -> list[dict[str, Any]]:
    """Normalised samples from ``dataset/attack_generated.jsonl``, traceid-unique."""
    by_traceid: dict[Any, dict[str, Any]] = {}
    for row in _read_jsonl(source):
        cleaned = normalize_sample(row)
        by_traceid[cleaned["traceid"]] = cleaned
    return [by_traceid[key] for key in sorted(by_traceid)]


def sample_subset(rows: list[dict[str, Any]], size: int, seed: int = DEFAULT_SEED) -> list[dict[str, Any]]:
    """A deterministic random subset, kept in traceid order like the full file."""
    if size >= len(rows):
        return list(rows)
    picked = random.Random(seed).sample(rows, size)
    return sorted(picked, key=lambda row: row["traceid"])


def install_assets(
    generated_dir: Path,
    data_root: Path = DATA_ROOT,
    legacy_suffix: str = DEFAULT_LEGACY_SUFFIX,
    force: bool = False,
) -> dict[str, Path]:
    """Pack the batch's asset trees into ``data_root``, keeping the old archives.

    Each existing ``<tree>.zip`` is renamed to ``<tree>_<legacy_suffix>.zip``
    before the freshly packed archive takes its place. Packing goes through
    ``archive.pack_tree``/``verify_tree``, so a tree that does not match its
    archive byte for byte aborts the merge before anything is overwritten.
    """
    asset_dir = _resolve(generated_dir) / "skill_inject"
    data_root = _resolve(data_root)
    for tree in archive.TREES:
        if not (asset_dir / tree).is_dir():
            raise FileNotFoundError(f"generated asset tree missing: {asset_dir / tree}")
        legacy = data_root / f"{tree}_{legacy_suffix}.zip"
        if legacy.exists() and not force:
            raise FileExistsError(f"legacy archive already exists, pass force=True to replace: {legacy}")

    installed: dict[str, Path] = {}
    for tree in archive.TREES:
        packed = archive.pack_tree(asset_dir, tree)
        problems = archive.verify_tree(asset_dir, tree)
        if problems:
            for problem in problems[:20]:
                print(f"[FAIL] {problem}")
            raise RuntimeError(f"{tree}: {len(problems)} mismatch(es); data/skill_inject was left untouched")
        current = data_root / f"{tree}.zip"
        if current.exists():
            legacy = data_root / f"{tree}_{legacy_suffix}.zip"
            legacy.unlink(missing_ok=True)
            current.replace(legacy)
            print(f"[keep] {current.name} -> {legacy.name}")
        data_root.mkdir(parents=True, exist_ok=True)
        shutil.move(str(packed), str(current))
        print(f"[install] {tree} -> {current} ({current.stat().st_size / 1e6:.1f} MB)")
        installed[tree] = current
    return installed


def verify_samples(rows: list[dict[str, Any]], data_root: Path = DATA_ROOT) -> None:
    """Fail loudly when a sample references an asset the archives do not carry."""
    data_root = _resolve(data_root)
    missing: list[str] = []
    for row in rows:
        meta = row["meta"]
        skill_name = str(meta.get("skill_name") or "")
        if not skill_name or not archive.exists(data_root, f"skills/{skill_name}"):
            missing.append(f"traceid={row['traceid']}: skills/{skill_name}")
        for rel_path in (meta.get("task_files") or {}).values():
            if not archive.exists(data_root, rel_path):
                missing.append(f"traceid={row['traceid']}: {rel_path}")
    if missing:
        for item in missing[:20]:
            print(f"[FAIL] {item}")
        raise RuntimeError(f"{len(missing)} sample asset(s) missing under {data_root}")


def merge_generated_batch(
    generated_dir: Path = DEFAULT_GENERATED_DIR,
    dataset_out: Path = DEFAULT_DATASET_OUT,
    small_out: Path = DEFAULT_SMALL_OUT,
    small_size: int = DEFAULT_SMALL_SIZE,
    seed: int = DEFAULT_SEED,
    legacy_suffix: str = DEFAULT_LEGACY_SUFFIX,
    skip_assets: bool = False,
    force: bool = False,
) -> dict[str, Any]:
    """Move one generated CIA-skill batch into ``data/input`` + ``data/skill_inject``."""
    generated_dir = _resolve(generated_dir)
    source = generated_dir / "dataset" / "attack_generated.jsonl"
    rows = load_attack_samples(source)
    if not rows:
        raise ValueError(f"no samples found in {source}")

    if skip_assets:
        print("[skip] asset archives left as they are")
    else:
        install_assets(generated_dir, legacy_suffix=legacy_suffix, force=force)
    verify_samples(rows)

    small = sample_subset(rows, small_size, seed)
    dataset_out = _resolve(dataset_out)
    small_out = _resolve(small_out)
    _write_jsonl(dataset_out, rows)
    _write_jsonl(small_out, small)
    print(f"[write] {len(rows)} sample(s) -> {dataset_out}")
    print(f"[write] {len(small)} sample(s) -> {small_out}")
    return {"total": len(rows), "small": len(small), "dataset": dataset_out, "small_dataset": small_out}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--generated_dir", type=Path, default=DEFAULT_GENERATED_DIR, help="flywheel attack output dir")
    parser.add_argument("--dataset_out", type=Path, default=DEFAULT_DATASET_OUT, help="full dataset destination")
    parser.add_argument("--small_out", type=Path, default=DEFAULT_SMALL_OUT, help="sampled dataset destination")
    parser.add_argument("--small_size", type=int, default=DEFAULT_SMALL_SIZE, help="sampled dataset size")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="sampling seed")
    parser.add_argument("--legacy_suffix", default=DEFAULT_LEGACY_SUFFIX, help="suffix for the archives being replaced")
    parser.add_argument("--skip_assets", action="store_true", help="only rewrite the datasets")
    parser.add_argument("--force", action="store_true", help="overwrite an existing legacy archive")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    merge_generated_batch(
        generated_dir=args.generated_dir,
        dataset_out=args.dataset_out,
        small_out=args.small_out,
        small_size=args.small_size,
        seed=args.seed,
        legacy_suffix=args.legacy_suffix,
        skip_assets=args.skip_assets,
        force=args.force,
    )


if __name__ == "__main__":
    main()
