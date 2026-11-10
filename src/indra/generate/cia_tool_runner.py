"""CIA-tool attack-generation runner for ras-eval-next samples."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from collections import deque
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any

from tqdm import tqdm

from src.indra.generate.attack_workspace import ensure_attack_generate_workspace
from src.indra.generate.cia_tool_task import run_cia_tool_attack_task
from src.indra.refine.runner import _RateLimiter


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(file, record: dict[str, Any]) -> None:
    file.write(json.dumps(record, ensure_ascii=False) + "\n")
    file.flush()
    os.fsync(file.fileno())


def _load_traceids(path: Path) -> set[int]:
    traceids: set[int] = set()
    for row in _load_jsonl(path):
        try:
            traceids.add(int(row["traceid"]))
        except Exception:
            continue
    return traceids


def _load_progress_traceids(path: Path) -> set[int]:
    traceids: set[int] = set()
    for row in _load_jsonl(path):
        if "base_traceid" not in row or row.get("status") != "added":
            continue
        try:
            traceids.add(int(row["traceid"]))
        except Exception:
            continue
    return traceids


def _filter_samples(samples: list[dict[str, Any]], cfg: Any) -> list[dict[str, Any]]:
    if cfg.traceid is None:
        return samples
    return [sample for sample in samples if int(sample["traceid"]) == int(cfg.traceid)]


def _build_jobs(samples: list[dict[str, Any]], done: set[int]) -> deque[dict[str, Any]]:
    jobs: deque[dict[str, Any]] = deque()
    for sample in samples:
        if int(sample["traceid"]) not in done:
            jobs.append(sample)
    return jobs


def _progress_row(result: dict[str, Any], status: str) -> dict[str, Any]:
    meta = result.get("meta", {})
    return {
        "traceid": int(result["traceid"]),
        "base_traceid": meta.get("base_traceid"),
        "behavior_id": meta.get("behavior_id"),
        "attack_category": meta.get("attack_category"),
        "toolkit_root": meta.get("toolkit_root"),
        "status": status,
        "security_success": meta.get("security_success"),
        "security_attempts": meta.get("security_attempts"),
        "security_error": meta.get("security_error"),
    }


def _security_row(result: dict[str, Any]) -> dict[str, Any]:
    meta = result.get("meta", {})
    return {
        "traceid": int(result["traceid"]),
        "base_traceid": meta.get("base_traceid"),
        "behavior_id": meta.get("behavior_id"),
        "specs": meta.get("security_specifications", []),
        "toolkit_root": meta.get("toolkit_root"),
        "expected_markers": (meta.get("attack") or {}).get("expected_markers", []),
    }


def _preflight_sandbox(cfg: Any) -> None:
    if cfg.sandbox != "docker":
        return
    completed = subprocess.run(
        ["docker", "info"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if completed.returncode != 0:
        detail = (completed.stderr or completed.stdout or "").strip().splitlines()[-1:]
        raise RuntimeError(
            "Docker daemon is not available for cia-tool generation: "
            + (detail[0] if detail else "docker info failed")
        )


def _gc_trace_dirs(traces_dir: Path, keep: set[str]) -> None:
    if not traces_dir.exists():
        return
    for path in traces_dir.iterdir():
        if path.is_dir() and path.name not in keep:
            shutil.rmtree(path, ignore_errors=True)


def _keep_trace_dirs(samples: list[dict[str, Any]], done: set[int]) -> set[str]:
    keep: set[str] = set()
    for sample in samples:
        traceid = int(sample["traceid"])
        if traceid not in done:
            keep.add(f"SPEC-{traceid}")
            keep.add(f"ATTACK-{traceid}")
    return keep


def run_cia_tool_generate(cfg: Any) -> list[dict[str, Any]]:
    ensure_attack_generate_workspace(cfg.output_dir, cfg.input_path)
    output_dir = Path(cfg.output_dir)
    (output_dir / "toolkits_cia_tool").mkdir(parents=True, exist_ok=True)
    shutil.rmtree(output_dir / "sandboxes", ignore_errors=True)
    (output_dir / "sandboxes").mkdir(parents=True, exist_ok=True)
    _preflight_sandbox(cfg)

    all_samples = _load_jsonl(cfg.input_path)
    samples = _filter_samples(all_samples, cfg)
    if not samples:
        print("No cia-tool samples to process.")
        return []

    dataset_dir = output_dir / "dataset"
    traces_dir = output_dir / "traces"
    output_path = dataset_dir / "attack_generated.jsonl"
    progress_path = dataset_dir / "progress.jsonl"
    security_path = dataset_dir / "security_specs.jsonl"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    done = _load_traceids(output_path)
    if cfg.skip_exist_traceid:
        done |= _load_progress_traceids(progress_path)
    _gc_trace_dirs(traces_dir, _keep_trace_dirs(all_samples, done))
    jobs = _build_jobs(samples, done)
    if not jobs:
        print("No cia-tool attack tasks to process.")
        return []

    limiter = _RateLimiter(cfg.qps)
    workers = max(1, cfg.parallel)
    added = 0
    results: list[dict[str, Any]] = []

    with output_path.open("a", encoding="utf-8") as out_file, \
        progress_path.open("a", encoding="utf-8") as progress_file, \
        security_path.open("a", encoding="utf-8") as security_file:
        bar = tqdm(total=len(jobs), desc="CIA-tool generate", unit="task")
        pending: dict[Future, dict[str, Any]] = {}

        def limit_reached() -> bool:
            return cfg.limit is not None and added >= cfg.limit

        def limit_slots_full() -> bool:
            return cfg.limit is not None and added + len(pending) >= cfg.limit

        def submit_next(executor: ThreadPoolExecutor) -> bool:
            if limit_reached() or limit_slots_full() or not jobs:
                return False
            sample = jobs.popleft()
            pending[executor.submit(run_cia_tool_attack_task, sample, cfg, limiter)] = sample
            return True

        with ThreadPoolExecutor(max_workers=workers) as executor:
            for _ in range(workers):
                if not submit_next(executor):
                    break
            while pending:
                done_futures, _ = wait(list(pending), return_when=FIRST_COMPLETED)
                for future in done_futures:
                    sample = pending.pop(future)
                    traceid = int(sample["traceid"])
                    try:
                        result = future.result()
                        success = bool(result.get("meta", {}).get("security_success"))
                        status = "added" if success else "exhausted"
                        _write_jsonl(progress_file, _progress_row(result, status))
                        _write_jsonl(security_file, _security_row(result))
                        _write_jsonl(out_file, result)
                        results.append(result)
                        done.add(traceid)
                        added += 1
                        # The job is durable in progress.jsonl / attack_generated.jsonl now,
                        # so its per-attempt environment snapshots can be reclaimed.
                        shutil.rmtree(traces_dir / f"SPEC-{traceid}", ignore_errors=True)
                        shutil.rmtree(traces_dir / f"ATTACK-{traceid}", ignore_errors=True)
                    except Exception as exc:  # noqa: BLE001
                        _write_jsonl(progress_file, {
                            "traceid": traceid,
                            "base_traceid": sample["traceid"],
                            "status": "error",
                            "error": f"{type(exc).__name__}: {exc}",
                        })
                    bar.update(1)
                    bar.set_postfix(added=added)
                    submit_next(executor)
                    if limit_reached():
                        bar.total = max(bar.n, bar.total - len(jobs))
                        jobs.clear()
                        bar.refresh()
        bar.close()

    results.sort(key=lambda item: int(item["traceid"]))
    return results
