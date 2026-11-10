"""Generation flywheel main loop.

For each tool combination: generate a candidate sample, run it, verify the tool
trace uses all of the combination's toolkit tools (built-in tools such as bash
and other toolkit tools are allowed; one regeneration retry), then error-check
and optimize if needed (up to 3 retries), writing accepted samples incrementally.

Combinations from the same toolkit are serialized (they share toolkit code that
the optimize phase edits); a global lock guards the optimize phase because it
also edits the shared environment directory. Progress is journaled so a run can
resume from an existing output directory.
"""
from __future__ import annotations

import json
import os
import shutil
import threading
from concurrent.futures import FIRST_COMPLETED, ThreadPoolExecutor, wait
from pathlib import Path
from typing import Any

from tqdm import tqdm

from src.indra.generate.combinations import Combination, enumerate_combinations
from src.indra.generate.generator import GenerateConfig, build_sample, generate_sample
from src.indra.generate.workspace import ensure_workspace
from src.indra.refine.checker import check_errors
from src.indra.refine.executor import run_inference
from src.indra.refine.fixer import run_fix
from src.indra.refine.runner import _RateLimiter, _ToolkitLockManager

MAX_GENERATE_ATTEMPTS = 2   # initial + 1 regeneration on trace mismatch
MAX_OPTIMIZE_ATTEMPTS = 3


def _used_tools(messages: list[dict[str, Any]], toolkit_tools: tuple[str, ...]) -> set[str]:
    """The distinct toolkit tools invoked in a trace (built-in tools ignored)."""
    allowed = set(toolkit_tools)
    used: set[str] = set()
    for msg in messages:
        if msg.get("role") != "assistant":
            continue
        for call in msg.get("tool_calls", []) or []:
            name = call.get("function", {}).get("name")
            if name in allowed:
                used.add(name)
    return used


def _mismatch_feedback(target: tuple[str, ...], used: set[str]) -> str:
    missing = sorted(set(target) - used)
    return (
        f"Your previous task did not lead the agent to use all required toolkit "
        f"tools (missing: {missing}). Rewrite the task so that solving it clearly "
        f"requires every one of the target tools. The agent may also use built-in "
        f"tools (bash, file read/write) or other toolkit tools -- that is fine -- "
        f"but all target tools must be genuinely needed."
    )


def _process_combo(
    combo: Combination,
    cfg: GenerateConfig,
    lock_manager: _ToolkitLockManager,
    optimize_lock: threading.Lock,
    limiter: _RateLimiter,
) -> dict[str, Any]:
    lock_manager.acquire([combo.toolkit])
    try:
        return _process_combo_inner(combo, cfg, optimize_lock, limiter)
    finally:
        lock_manager.release([combo.toolkit])


def _process_combo_inner(
    combo: Combination,
    cfg: GenerateConfig,
    optimize_lock: threading.Lock,
    limiter: _RateLimiter,
) -> dict[str, Any]:
    base = {"traceid": combo.traceid, "toolkit": combo.toolkit, "combination": list(combo.tools)}
    target = set(combo.tools)

    sample = None
    messages: list[dict[str, Any]] = []
    retry_feedback = ""
    last_used: set[str] = set()

    for _ in range(MAX_GENERATE_ATTEMPTS):
        limiter.wait()
        gen_output = generate_sample(combo, cfg, retry_feedback)
        if gen_output.get("refuse"):
            return {**base, "status": "refused", "reason": gen_output.get("reason", "")}
        if "prompt" not in gen_output:
            retry_feedback = "Your reply was not a valid task JSON object. Output the required JSON."
            sample = None
            continue

        sample = build_sample(combo, gen_output)
        limiter.wait()
        messages, _, _ = run_inference(sample, cfg.output_dir, cfg)
        last_used = _used_tools(messages, combo.all_tools)
        if target.issubset(last_used):
            break
        retry_feedback = _mismatch_feedback(combo.tools, last_used)
        sample = None

    if sample is None:
        return {**base, "status": "skipped", "reason": f"tool trace mismatch, used={sorted(last_used)}"}

    # Error check + optimize.
    errors = check_errors(messages)
    optimized = bool(errors)
    optimize_success = not errors
    attempts = 0
    if errors:
        for attempt in range(1, MAX_OPTIMIZE_ATTEMPTS + 1):
            attempts = attempt
            with optimize_lock:
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
            limiter.wait()
            messages, _, _ = run_inference(sample, cfg.output_dir, cfg)
            errors = check_errors(messages)
            if not errors and target.issubset(_used_tools(messages, combo.all_tools)):
                optimize_success = True
                break

    result = dict(sample)
    result["meta"] = {
        **sample["meta"],
        "generated": True,
        "optimized": optimized,
        "optimize_success": optimize_success,
        "optimize_attempts": attempts,
    }
    return {**base, "status": "added", "sample": result, "optimize_success": optimize_success}


def _load_processed_traceids(progress_path: Path) -> set[int]:
    if not progress_path.exists():
        return set()
    processed: set[int] = set()
    for line in progress_path.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if line:
            processed.add(int(json.loads(line)["traceid"]))
    return processed


def run_generate(cfg: GenerateConfig) -> int:
    """Run the generation flywheel. Returns the number of samples added."""
    ensure_workspace(cfg.output_dir, cfg.input_path)

    # Purge sandboxes left behind by a previous crashed/killed run: everything
    # under sandboxes/ (per-task dirs, .opencode_config_*, .opencode_home_*) is
    # disposable and recreated per run, so it must never accumulate.
    shutil.rmtree(cfg.output_dir / "sandboxes", ignore_errors=True)

    combos = enumerate_combinations(cfg.output_dir, cfg.depth, cfg.max_per_toolkit, cfg.seed)
    dataset_dir = cfg.output_dir / "dataset"
    generated_path = dataset_dir / "generated.jsonl"
    progress_path = dataset_dir / "progress.jsonl"

    processed = _load_processed_traceids(progress_path)
    combos = [c for c in combos if c.traceid not in processed]
    if not combos:
        print("No combinations to process.")
        return 0

    lock_manager = _ToolkitLockManager()
    optimize_lock = threading.Lock()
    limiter = _RateLimiter(cfg.qps)
    write_lock = threading.Lock()

    combos_iter = iter(combos)
    pending: set = set()
    added = 0

    def _write(path: Path, record: dict[str, Any]) -> None:
        with write_lock:
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())

    with ThreadPoolExecutor(max_workers=max(1, cfg.parallel)) as executor:
        def _submit_next() -> bool:
            combo = next(combos_iter, None)
            if combo is None:
                return False
            pending.add(executor.submit(_process_combo, combo, cfg, lock_manager, optimize_lock, limiter))
            return True

        for _ in range(max(1, cfg.parallel)):
            if not _submit_next():
                break

        pbar = tqdm(desc="Generate", unit="combo")
        while pending:
            done, pending = wait(pending, return_when=FIRST_COMPLETED)
            for future in done:
                try:
                    record = future.result()
                except Exception as exc:  # noqa: BLE001 - journal and continue
                    record = {"status": "error", "reason": str(exc), "traceid": -1}

                if record.get("status") == "added":
                    added += 1
                    _write(generated_path, record.pop("sample"))
                _write(progress_path, record)

                pbar.update(1)
                pbar.set_postfix(added=added)

                if cfg.limit is None or added < cfg.limit:
                    _submit_next()
        pbar.close()

    return added
