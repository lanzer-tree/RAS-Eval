"""CIA attack-generation runner for skill-inject samples."""
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

from src.indra.generate.attack_workspace import ensure_cia_generate_workspace
from src.indra.generate.cia_schema import iter_behaviors
from src.indra.generate.cia_task import clean_cia_attack_sample, run_cia_attack_task
from src.indra.refine.runner import _RateLimiter


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _write_jsonl(file, record: dict[str, Any]) -> None:
    file.write(json.dumps(record, ensure_ascii=False) + "\n")
    file.flush()
    os.fsync(file.fileno())


def _spec_trace_name(base_traceid: int, behavior_id: str) -> str:
    return f"SPEC-{base_traceid}-{behavior_id}"


def _attack_trace_name(attack_traceid: int) -> str:
    return f"ATTACK-{attack_traceid}"


def _gc_trace_dirs(traces_dir: Path, keep: set[str]) -> None:
    """Delete CIA trace workspaces that are no longer needed.

    Security specs are durable once written to security_specs.jsonl, and attack
    attempts are durable once progress/output rows are fsynced. Stale trace dirs
    from older runs can therefore be reclaimed at startup and after each job.
    """
    if not traces_dir.exists():
        return
    for path in traces_dir.iterdir():
        if path.is_dir() and path.name not in keep:
            shutil.rmtree(path, ignore_errors=True)


def _keep_trace_dirs(samples: list[dict[str, Any]], done: set[int], security_done: set[int]) -> set[str]:
    keep: set[str] = set()
    for sample in samples:
        base_traceid = int(sample["traceid"])
        for behavior in iter_behaviors():
            attack_traceid = _attack_traceid(base_traceid, behavior["id"])
            if attack_traceid not in security_done:
                keep.add(_spec_trace_name(base_traceid, behavior["id"]))
            if attack_traceid not in done:
                keep.add(_attack_trace_name(attack_traceid))
    return keep


def _load_traceids(path: Path) -> set[int]:
    traceids: set[int] = set()
    for row in _load_jsonl(path):
        try:
            traceids.add(int(row["traceid"]))
        except Exception:
            continue
    return traceids


def _attack_traceid(base_traceid: int, behavior_id: str) -> int:
    return base_traceid * 100 + int(behavior_id[1:])


def _selected_behavior_ids(cfg: Any) -> set[str] | None:
    if cfg.traceid is None or cfg.traceid < 100:
        return None
    behavior_index = cfg.traceid % 100
    if 1 <= behavior_index <= len(iter_behaviors()):
        return {f"B{behavior_index}"}
    return None


def _filter_samples(samples: list[dict[str, Any]], cfg: Any) -> list[dict[str, Any]]:
    if cfg.traceid is None:
        return samples
    selected: list[dict[str, Any]] = []
    for sample in samples:
        base_traceid = int(sample["traceid"])
        target_base = cfg.traceid // 100 if cfg.traceid >= 100 else cfg.traceid
        if base_traceid == target_base:
            selected.append(sample)
    return selected


def _build_jobs(
    samples: list[dict[str, Any]],
    done: set[int],
    selected_behavior_ids: set[str] | None = None,
) -> deque[tuple[dict[str, Any], dict[str, str]]]:
    jobs: deque[tuple[dict[str, Any], dict[str, str]]] = deque()
    for behavior in iter_behaviors():
        if selected_behavior_ids is not None and behavior["id"] not in selected_behavior_ids:
            continue
        for sample in samples:
            base_traceid = int(sample["traceid"])
            if _attack_traceid(base_traceid, behavior["id"]) not in done:
                jobs.append((sample, behavior))
    return jobs


def _progress_row(result: dict[str, Any], status: str) -> dict[str, Any]:
    meta = result.get("meta", {})
    return {
        "traceid": int(result["traceid"]),
        "base_traceid": meta.get("base_traceid"),
        "behavior_id": meta.get("behavior_id"),
        "attack_category": meta.get("attack_category"),
        "red_skill": meta.get("skill_name"),
        "status": status,
        "security_success": meta.get("security_success"),
        "security_attempts": meta.get("security_attempts"),
        "security_error": meta.get("security_error"),
    }


def _security_row(result: dict[str, Any]) -> dict[str, Any]:
    meta = result["meta"]
    return {
        "traceid": int(result["traceid"]),
        "base_traceid": meta.get("base_traceid"),
        "behavior_id": meta.get("behavior_id"),
        "specs": meta.get("security_specifications", []),
        "environment": meta.get("environment", []),
    }


def _manifest_row(result: dict[str, Any]) -> dict[str, Any]:
    meta = result["meta"]
    return {
        "traceid": int(result["traceid"]),
        "base_traceid": meta.get("base_traceid"),
        "behavior_id": meta.get("behavior_id"),
        "base_skill": meta.get("base_skill"),
        "red_skill": meta.get("skill_name"),
        "data_root": meta.get("data_root"),
        "expected_markers": (meta.get("attack") or {}).get("expected_markers", []),
        "environment": meta.get("environment", []),
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
        raise RuntimeError("Docker daemon is not available for CIA generation: " + (detail[0] if detail else "docker info failed"))



def run_cia_generate(cfg: Any) -> list[dict[str, Any]]:
    ensure_cia_generate_workspace(cfg.output_dir, cfg.input_path)
    output_dir = Path(cfg.output_dir)
    shutil.rmtree(output_dir / "sandboxes", ignore_errors=True)
    (output_dir / "sandboxes").mkdir(parents=True, exist_ok=True)
    _preflight_sandbox(cfg)
    all_samples = _load_jsonl(cfg.input_path)
    samples = _filter_samples(all_samples, cfg)
    if not samples:
        print("No CIA samples to process.")
        return []

    dataset_dir = output_dir / "dataset"
    traces_dir = output_dir / "traces"
    output_path = dataset_dir / "attack_generated.jsonl"
    progress_path = dataset_dir / "progress.jsonl"
    security_path = dataset_dir / "security_specs.jsonl"
    manifest_path = dataset_dir / "cia_skill_manifest.jsonl"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    done = _load_traceids(output_path)
    security_done = _load_traceids(security_path)
    _gc_trace_dirs(traces_dir, _keep_trace_dirs(all_samples, done, security_done))
    jobs = _build_jobs(samples, done, _selected_behavior_ids(cfg))
    if not jobs:
        print("No CIA attack tasks to process.")
        return []

    limiter = _RateLimiter(cfg.qps)
    workers = max(1, cfg.parallel)
    added = 0
    results: list[dict[str, Any]] = []

    with output_path.open("a", encoding="utf-8") as out_file, \
        progress_path.open("a", encoding="utf-8") as progress_file, \
        security_path.open("a", encoding="utf-8") as security_file, \
        manifest_path.open("a", encoding="utf-8") as manifest_file:
        bar = tqdm(total=len(jobs), desc="CIA attack generate", unit="task")
        pending: dict[Future, tuple[dict[str, Any], dict[str, str]]] = {}

        def limit_reached() -> bool:
            return cfg.limit is not None and added >= cfg.limit

        def limit_slots_full() -> bool:
            return cfg.limit is not None and added + len(pending) >= cfg.limit

        def submit_next(executor: ThreadPoolExecutor) -> bool:
            if limit_reached() or limit_slots_full() or not jobs:
                return False
            job = jobs.popleft()
            pending[executor.submit(run_cia_attack_task, job[0], job[1], cfg, limiter)] = job
            return True

        with ThreadPoolExecutor(max_workers=workers) as executor:
            for _ in range(workers):
                if not submit_next(executor):
                    break
            while pending:
                done_futures, _ = wait(list(pending), return_when=FIRST_COMPLETED)
                for future in done_futures:
                    sample, behavior = pending.pop(future)
                    attack_tid = _attack_traceid(int(sample["traceid"]), behavior["id"])
                    try:
                        result = future.result()
                        success = bool(result.get("meta", {}).get("security_success"))
                        status = "added" if success else "exhausted"
                        _write_jsonl(progress_file, _progress_row(result, status))
                        if attack_tid not in security_done:
                            _write_jsonl(security_file, _security_row(result))
                            security_done.add(attack_tid)
                        shutil.rmtree(traces_dir / _spec_trace_name(int(sample["traceid"]), behavior["id"]), ignore_errors=True)
                        if success:
                            clean_result = clean_cia_attack_sample(result)
                            _write_jsonl(out_file, clean_result)
                            _write_jsonl(manifest_file, _manifest_row(result))
                            results.append(clean_result)
                            done.add(attack_tid)
                            added += 1
                        shutil.rmtree(traces_dir / _attack_trace_name(attack_tid), ignore_errors=True)
                    except Exception as exc:  # noqa: BLE001
                        _write_jsonl(progress_file, {
                            "traceid": attack_tid,
                            "base_traceid": sample["traceid"],
                            "behavior_id": behavior["id"],
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
