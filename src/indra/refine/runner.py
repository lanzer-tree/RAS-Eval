"""Flywheel refine main loop with parallel scheduling and conflict avoidance.

Orchestrates the full refine pipeline: for each sample, run inference, check for
errors, invoke LLM fix if needed (up to 3 retries), and write results
incrementally. Samples sharing toolkits are serialized to prevent conflicts.
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

from src.indra.refine.checker import check_errors
from src.indra.refine.executor import RefineConfig, run_inference
from src.indra.refine.fixer import run_fix
from src.indra.refine.workspace import ensure_workspace

MAX_FIX_ATTEMPTS = 3


class _ToolkitLockManager:
    """Manages per-toolkit locks to prevent concurrent modification conflicts.

    Samples that share any toolkit must not run simultaneously because the fix
    phase modifies toolkit code in-place under the shared output directory.
    """

    def __init__(self) -> None:
        self._locks: dict[str, threading.Lock] = {}
        self._meta_lock = threading.Lock()

    def acquire(self, toolkits: list[str]) -> None:
        """Acquire locks for all toolkits in sorted order (deadlock-free)."""
        for tk in sorted(toolkits):
            lock = self._get_lock(tk)
            lock.acquire()

    def release(self, toolkits: list[str]) -> None:
        """Release locks for all toolkits."""
        for tk in sorted(toolkits):
            lock = self._get_lock(tk)
            lock.release()

    def _get_lock(self, toolkit: str) -> threading.Lock:
        with self._meta_lock:
            if toolkit not in self._locks:
                self._locks[toolkit] = threading.Lock()
            return self._locks[toolkit]


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


def _refine_sample(
    sample: dict[str, Any],
    cfg: RefineConfig,
    lock_manager: _ToolkitLockManager,
    limiter: _RateLimiter,
) -> dict[str, Any]:
    """Process one sample through the refine pipeline."""
    toolkits = sample["meta"].get("toolkits", [])
    lock_manager.acquire(toolkits)
    try:
        return _refine_sample_inner(sample, cfg, limiter)
    finally:
        lock_manager.release(toolkits)


def _refine_sample_inner(
    sample: dict[str, Any],
    cfg: RefineConfig,
    limiter: _RateLimiter,
) -> dict[str, Any]:
    """Core refine logic for a single sample (called with locks held)."""
    # First inference run
    limiter.wait()
    messages, stdout, stderr = run_inference(sample, cfg.output_dir, cfg)
    errors = check_errors(messages)

    if not errors:
        # Sample is fine, no optimization needed
        result = dict(sample)
        result["meta"] = {**result["meta"], "refined": False}
        return result

    # Attempt fix loop
    for attempt in range(1, MAX_FIX_ATTEMPTS + 1):
        limiter.wait()
        run_fix(
            sample=sample,
            errors=errors,
            messages=messages,
            output_dir=cfg.output_dir,
            cfg_model=cfg.model,
            cfg_sandbox=cfg.sandbox,
            cfg_os=cfg.os,
            cfg_timeout=cfg.timeout,
            cfg_apptainer_path=cfg.apptainer_path,
            cfg_image=cfg.image,
        )

        # Re-run inference to verify
        limiter.wait()
        messages, stdout, stderr = run_inference(sample, cfg.output_dir, cfg)
        errors = check_errors(messages)

        if not errors:
            result = dict(sample)
            result["meta"] = {
                **result["meta"],
                "refined": True,
                "refined_success": True,
                "refine_attempts": attempt,
            }
            return result

    # All attempts exhausted, still has errors
    result = dict(sample)
    result["meta"] = {
        **result["meta"],
        "refined": True,
        "refined_success": False,
        "refine_attempts": MAX_FIX_ATTEMPTS,
    }
    return result


def _load_existing_traceids(output_path: Path) -> set[int]:
    """Load traceids already written to the output file."""
    if not output_path.exists():
        return set()
    traceids = set()
    with open(output_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                record = json.loads(line)
                traceids.add(int(record["traceid"]))
    return traceids


def run_refine(cfg: RefineConfig) -> list[dict[str, Any]]:
    """Run the full flywheel refine pipeline."""
    # Initialize workspace
    ensure_workspace(cfg.output_dir)

    # Purge sandboxes left behind by a previous crashed/killed run: everything
    # under sandboxes/ (per-task dirs, .opencode_config_*, .opencode_home_*) is
    # disposable and recreated per run, so it must never accumulate.
    shutil.rmtree(cfg.output_dir / "sandboxes", ignore_errors=True)

    # Load samples
    with open(cfg.input_path, "r", encoding="utf-8") as f:
        samples = [json.loads(line) for line in f if line.strip()]

    # Filter by traceid
    output_path = cfg.output_dir / "dataset" / "refined.jsonl"
    exist_traceids = _load_existing_traceids(output_path) if cfg.skip_exist_traceid else set()

    if cfg.traceid is not None:
        samples = [s for s in samples if s["traceid"] == cfg.traceid]
    elif cfg.skip_exist_traceid:
        samples = [s for s in samples if int(s["traceid"]) not in exist_traceids]

    if not samples:
        print("No samples to process.")
        return []

    # Setup coordination
    lock_manager = _ToolkitLockManager()
    limiter = _RateLimiter(cfg.qps)
    write_lock = threading.Lock()
    results: list[dict[str, Any]] = []

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("a", encoding="utf-8") as out_file:
        with ThreadPoolExecutor(max_workers=max(1, cfg.parallel)) as executor:
            futures = {
                executor.submit(_refine_sample, sample, cfg, lock_manager, limiter): sample
                for sample in samples
            }
            for future in tqdm(
                as_completed(futures),
                total=len(futures),
                desc="Refine",
                unit="sample",
            ):
                try:
                    result = future.result()
                except Exception as exc:
                    sample = futures[future]
                    print(f"[ERROR] traceid={sample['traceid']}: {exc}")
                    result = dict(sample)
                    result["meta"] = {
                        **result["meta"],
                        "refined": True,
                        "refined_success": False,
                        "refine_attempts": 0,
                        "error": str(exc),
                    }
                results.append(result)
                with write_lock:
                    out_file.write(json.dumps(result, ensure_ascii=False) + "\n")
                    out_file.flush()
                    os.fsync(out_file.fileno())

    results.sort(key=lambda r: int(r["traceid"]))
    return results
