"""Flywheel annotate main loop: inference caching + SpecAgent annotation.

For each sample: replay the trajectory (checkpointed under traces/), run the
self-driven SpecAgent session that writes specs.json, then collect the result
into dataset/annotated.jsonl incrementally. Failures land in dataset/failed.jsonl.
Fully resumable: cached trajectories and already-annotated traceids are skipped.
"""
from __future__ import annotations

import json
import os
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from tqdm import tqdm

from src.indra.annotator.executor import AnnotateConfig, collect_result, run_inference, run_spec_agent, trace_dir_for
from src.indra.annotator.workspace import ensure_annotate_workspace


class _RateLimiter:
    """Simple token-bucket rate limiter."""

    def __init__(self, qps: float) -> None:
        self.interval = 0.0 if qps <= 0 else 1.0 / qps
        self._lock = threading.Lock()
        self._next_time = 0.0

    def wait(self) -> None:
        if self.interval <= 0:
            return
        with self._lock:
            now = time.monotonic()
            if now < self._next_time:
                time.sleep(self._next_time - now)
                now = time.monotonic()
            self._next_time = now + self.interval


def _annotate_sample(sample: dict[str, Any], cfg: AnnotateConfig, limiter: _RateLimiter) -> dict[str, Any]:
    """Process one sample: inference (cached) -> SpecAgent -> collect."""
    limiter.wait()
    run_inference(sample, cfg)
    limiter.wait()
    run_spec_agent(sample, cfg)
    return collect_result(sample, cfg)


def _load_existing_traceids(output_path: Path) -> set[int]:
    if not output_path.exists():
        return set()
    traceids = set()
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                traceids.add(int(json.loads(line)["traceid"]))
    return traceids


def _select_representative(samples: list[dict[str, Any]], limit: int) -> list[dict[str, Any]]:
    """Round-robin across agent (ras-eval-next) / suite (agentdojo) / skill
    (skill_inject) groups so a small --limit run still covers diverse task types."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for sample in samples:
        meta = sample["meta"]
        key = meta.get("agent") or meta.get("suite_name") or meta.get("skill", "")
        groups.setdefault(key, []).append(sample)
    selected: list[dict[str, Any]] = []
    queues = list(groups.values())
    while len(selected) < limit and any(queues):
        for queue in queues:
            if queue and len(selected) < limit:
                selected.append(queue.pop(0))
    return selected


def _purge_run_artifacts(traces_dir: Path) -> None:
    """Remove disposable opencode config/home leftovers from a crashed run
    while keeping the trace checkpoints themselves."""
    if not traces_dir.exists():
        return
    for path in traces_dir.rglob(".opencode_config_*"):
        path.unlink(missing_ok=True)
    for path in traces_dir.rglob(".opencode_home_*"):
        shutil.rmtree(path, ignore_errors=True)


def _gc_trace_dirs(traces_dir: Path, done_traceids: set[int]) -> None:
    """Garbage-collect trace checkpoints of already-annotated samples.

    Once a sample's record is persisted in annotated.jsonl the host never reads
    its traces/TASK-{tid} again, so the dir (trajectory, environment snapshot,
    agent workspace) is deleted to reclaim storage. Failed samples keep their
    trace dir so a resumed run can reuse the cached trajectory."""
    if not traces_dir.exists():
        return
    for path in traces_dir.glob("TASK-*"):
        try:
            traceid = int(path.name.split("-", 1)[1])
        except ValueError:
            continue
        if traceid in done_traceids:
            shutil.rmtree(path, ignore_errors=True)


def run_annotate(cfg: AnnotateConfig) -> list[dict[str, Any]]:
    """Run the full annotate pipeline and return the accepted rows."""
    ensure_annotate_workspace(cfg.output_dir, cfg.benchmark)
    _purge_run_artifacts(Path(cfg.output_dir) / "traces")

    with open(cfg.input_path, "r", encoding="utf-8") as f:
        samples = [json.loads(line) for line in f if line.strip()]

    annotated_path = cfg.output_dir / "dataset" / "annotated.jsonl"
    failed_path = cfg.output_dir / "dataset" / "failed.jsonl"
    exist_traceids = _load_existing_traceids(annotated_path)
    # Reclaim trace dirs left behind by earlier runs (e.g. crash between the
    # dataset write and the per-sample cleanup below).
    _gc_trace_dirs(Path(cfg.output_dir) / "traces", exist_traceids)

    if cfg.traceid is not None:
        samples = [s for s in samples if int(s["traceid"]) == cfg.traceid]
    elif cfg.skip_exist_traceid:
        samples = [s for s in samples if int(s["traceid"]) not in exist_traceids]
    if cfg.limit is not None:
        samples = _select_representative(samples, cfg.limit)

    if not samples:
        print("No samples to process.")
        return []

    limiter = _RateLimiter(cfg.qps)
    write_lock = threading.Lock()
    results: list[dict[str, Any]] = []

    with annotated_path.open("a", encoding="utf-8") as out_file, failed_path.open("a", encoding="utf-8") as fail_file:
        with ThreadPoolExecutor(max_workers=max(1, cfg.parallel)) as executor:
            futures = {
                executor.submit(_annotate_sample, sample, cfg, limiter): sample
                for sample in samples
            }
            for future in tqdm(as_completed(futures), total=len(futures), desc="Annotate", unit="sample"):
                sample = futures[future]
                try:
                    result = future.result()
                except Exception as exc:
                    print(f"[ERROR] traceid={sample['traceid']}: {exc}")
                    failure = {"traceid": sample["traceid"], "prompt": sample["prompt"], "error": str(exc)}
                    with write_lock:
                        fail_file.write(json.dumps(failure, ensure_ascii=False) + "\n")
                        fail_file.flush()
                        os.fsync(fail_file.fileno())
                    continue
                results.append(result)
                with write_lock:
                    out_file.write(json.dumps(result, ensure_ascii=False) + "\n")
                    out_file.flush()
                    os.fsync(out_file.fileno())
                # The record is durable now -- drop the sample's trace dir to
                # reclaim storage (trajectory, env snapshot, agent workspace).
                shutil.rmtree(trace_dir_for(cfg, sample["traceid"]), ignore_errors=True)

    results.sort(key=lambda r: int(r["traceid"]))
    return results
