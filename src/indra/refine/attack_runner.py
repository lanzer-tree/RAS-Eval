"""RAS-Eval attack refine flywheel."""
from __future__ import annotations

import copy
import json
import os
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tqdm import tqdm

from src.evaluator.spec import DIMENSIONS, _spec_dimensions, evaluation_row, normalize_response
from src.evaluator.spec.observe import verify_in_sandbox
from src.indra.refine.attack_optimizer import optimize_attack
from src.indra.refine.executor import RefineConfig, run_inference
from src.indra.refine.runner import _RateLimiter
from src.indra.refine.workspace import ensure_workspace
from src.runner.sandbox import SandboxSpec, cleanup_sandbox_artifacts

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class AttackRefineConfig:
    input_path: Path
    output_dir: Path
    attack_model: str
    target_model: str
    sandbox: str
    os: str
    parallel: int = 1
    qps: float = 1.0
    traceid: int | None = None
    timeout: int = 900
    skip_exist_traceid: bool = False
    apptainer_path: str | None = None
    image: str | None = None
    max_iterations: int = 3
    attack_type: str = ""
    attack_api_key: str | None = None
    attack_base_url: str | None = None
    target_api_key: str | None = None
    target_base_url: str | None = None


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_existing_traceids(path: Path) -> set[int]:
    if not path.exists():
        return set()
    return {int(item["traceid"]) for item in _load_jsonl(path)}


def _target_cfg(cfg: AttackRefineConfig) -> RefineConfig:
    return RefineConfig(
        input_path=cfg.input_path,
        output_dir=cfg.output_dir,
        model=cfg.target_model,
        sandbox=cfg.sandbox,
        os=cfg.os,
        parallel=1,
        qps=cfg.qps,
        traceid=cfg.traceid,
        timeout=cfg.timeout,
        skip_exist_traceid=False,
        apptainer_path=cfg.apptainer_path,
        image=cfg.image,
        api_key=cfg.target_api_key,
        base_url=cfg.target_base_url,
    )


def _evaluate(
    sample: dict[str, Any],
    messages: list[dict[str, Any]],
    sandbox_dir: Path,
    cfg: AttackRefineConfig,
) -> dict[str, Any]:
    dimensions = _spec_dimensions(sample)
    flat_specs = [
        item["formal_spec"]
        for _, key in dimensions
        for item in (sample["meta"].get(key) or [])
    ]
    verify_error = None
    try:
        outcome = verify_in_sandbox(
            normalize_response(messages),
            flat_specs,
            sandbox_dir / "environment",
            SandboxSpec(cfg.sandbox, cfg.image, cfg.os, cfg.apptainer_path),
            timeout=cfg.timeout,
        )
        results = outcome["results"]
    except Exception as exc:  # noqa: BLE001 - persist verifier failures per attempt
        verify_error = f"{type(exc).__name__}: {exc}"
        results = [f"error: {verify_error}"] * len(flat_specs)

    row = evaluation_row(
        {"traceid": sample["traceid"], "response": messages},
        sample["meta"],
        results,
        dimensions=dimensions,
    )
    security = row["security"]
    eval_result = {
        "traceid": sample["traceid"],
        "ltl": {dimension: row[dimension] for dimension, _ in DIMENSIONS},
        "attack_success": security["num_total"] > 0 and security["num_sat"] < security["num_total"],
    }
    if verify_error:
        eval_result["verify_error"] = verify_error
    return eval_result


def _inference_failed(messages: list[dict[str, Any]], stdout: str, stderr: str) -> bool:
    return len(messages) <= 1 and not stdout.strip() and bool(stderr.strip())


def _final_meta(
    sample: dict[str, Any],
    original_sample: dict[str, Any],
    optimized: bool,
    success: bool,
    history: list[dict[str, Any]],
    eval_result: dict[str, Any] | None,
) -> dict[str, Any]:
    meta = dict(sample["meta"])
    meta.update({
        "attack_refined": optimized,
        "attack_refine_success": success,
        "attack_refine_attempts": len(history),
        "attack_refine_final_attack_success": success,
        "attack_refine_attack_model": sample.get("_attack_model"),
        "attack_refine_target_model": sample.get("_target_model"),
        "attack_refine_history": history,
    })
    if optimized:
        meta["attack_refine_original_attack"] = original_sample["meta"].get("attack", [])
    if eval_result is not None:
        meta["attack_refine_final_eval"] = {
            "ltl": eval_result.get("ltl", {}),
            "attack_success": eval_result.get("attack_success", False),
            "verify_error": eval_result.get("verify_error"),
        }
    return meta


def _process_sample(
    sample: dict[str, Any],
    cfg: AttackRefineConfig,
    limiter: _RateLimiter,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    original_sample = copy.deepcopy(sample)
    current = copy.deepcopy(sample)
    target_cfg = _target_cfg(cfg)
    history: list[dict[str, Any]] = []
    response_records: list[dict[str, Any]] = []
    eval_records: list[dict[str, Any]] = []
    optimized = False
    success = False
    final_eval: dict[str, Any] | None = None

    for attempt in range(cfg.max_iterations + 1):
        limiter.wait()
        sandbox_dir: Path | None = None
        messages, stdout, stderr, sandbox_dir = run_inference(
            current,
            cfg.output_dir,
            target_cfg,
            keep_sandbox=True,
        )
        try:
            response_records.append({
                "traceid": current["traceid"],
                "attempt": attempt,
                "optimized_before_run": optimized,
                "response": messages,
                "stdout_tail": stdout[-1000:] if stdout else "",
                "stderr_tail": stderr[-1000:] if stderr else "",
            })
            if _inference_failed(messages, stdout, stderr):
                current["_attack_model"] = cfg.attack_model
                current["_target_model"] = cfg.target_model
                result = copy.deepcopy(current)
                result.pop("_attack_model", None)
                result.pop("_target_model", None)
                result["meta"] = _final_meta(current, original_sample, optimized, False, history, None)
                result["meta"]["attack_refine_error"] = stderr.strip()[-1000:]
                progress = {
                    "traceid": result["traceid"],
                    "status": "error",
                    "attack_refined": optimized,
                    "attack_refine_success": False,
                    "attack_refine_attempts": len(history),
                    "error": stderr.strip()[-1000:],
                }
                return result, response_records, eval_records, progress
            eval_result = _evaluate(current, messages, sandbox_dir, cfg)
        finally:
            if sandbox_dir is not None:
                cleanup_sandbox_artifacts(sandbox_dir)
                shutil.rmtree(sandbox_dir, ignore_errors=True)
        eval_result = {**eval_result, "attempt": attempt, "optimized_before_run": optimized}
        eval_records.append(eval_result)
        final_eval = eval_result
        if eval_result.get("attack_success"):
            success = True
            break
        if attempt >= cfg.max_iterations:
            break
        limiter.wait()
        current, optimize_info = optimize_attack(
            sample=current,
            eval_result=eval_result,
            messages=messages,
            output_dir=cfg.output_dir,
            model=cfg.attack_model,
            api_key=cfg.attack_api_key,
            base_url=cfg.attack_base_url,
            sandbox=cfg.sandbox,
            os_name=cfg.os,
            timeout=cfg.timeout,
            apptainer_path=cfg.apptainer_path,
            image=cfg.image,
            attempt=attempt + 1,
            history=history,
        )
        history.append(optimize_info)
        optimized = True

    result = copy.deepcopy(current)
    result.pop("_attack_model", None)
    result.pop("_target_model", None)
    current["_attack_model"] = cfg.attack_model
    current["_target_model"] = cfg.target_model
    result["meta"] = _final_meta(current, original_sample, optimized, success, history, final_eval)
    progress = {
        "traceid": result["traceid"],
        "status": "ok",
        "attack_refined": optimized,
        "attack_refine_success": success,
        "attack_refine_attempts": len(history),
    }
    return result, response_records, eval_records, progress


def _copy_input_dataset(cfg: AttackRefineConfig) -> None:
    dataset_dir = cfg.output_dir / "dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)
    copied = dataset_dir / "input.jsonl"
    if not copied.exists():
        shutil.copy2(cfg.input_path, copied)


def _write_jsonl(file, record: dict[str, Any]) -> None:
    file.write(json.dumps(record, ensure_ascii=False) + "\n")
    file.flush()
    os.fsync(file.fileno())


def run_attack_refine(cfg: AttackRefineConfig) -> list[dict[str, Any]]:
    ensure_workspace(cfg.output_dir)
    _copy_input_dataset(cfg)
    shutil.rmtree(cfg.output_dir / "sandboxes", ignore_errors=True)

    samples = _load_jsonl(cfg.input_path)
    bad_sources = sorted({sample.get("source") for sample in samples if sample.get("source") != "ras-eval-next"})
    if bad_sources:
        raise ValueError(
            "task=refine mode=attack currently supports only source='ras-eval-next'; "
            f"found {bad_sources} in {cfg.input_path}"
        )
    if cfg.attack_type:
        samples = [sample for sample in samples if sample.get("meta", {}).get("attack_type") == cfg.attack_type]
    output_path = cfg.output_dir / "dataset" / "attack_refined.jsonl"
    response_path = cfg.output_dir / "responses" / "attack_refine_responses.jsonl"
    eval_path = cfg.output_dir / "evaluation" / "attack_refine_eval.jsonl"
    progress_path = cfg.output_dir / "dataset" / "attack_refine_progress.jsonl"

    if cfg.traceid is not None:
        samples = [sample for sample in samples if int(sample["traceid"]) == cfg.traceid]
    elif cfg.skip_exist_traceid:
        existing = _load_existing_traceids(output_path)
        samples = [sample for sample in samples if int(sample["traceid"]) not in existing]

    if not samples:
        print("No samples to process.")
        return []

    output_path.parent.mkdir(parents=True, exist_ok=True)
    response_path.parent.mkdir(parents=True, exist_ok=True)
    eval_path.parent.mkdir(parents=True, exist_ok=True)

    limiter = _RateLimiter(cfg.qps)
    write_lock = threading.Lock()
    results: list[dict[str, Any]] = []

    with output_path.open("a", encoding="utf-8") as out_file, \
        response_path.open("a", encoding="utf-8") as response_file, \
        eval_path.open("a", encoding="utf-8") as eval_file, \
        progress_path.open("a", encoding="utf-8") as progress_file:
        with ThreadPoolExecutor(max_workers=max(1, cfg.parallel)) as executor:
            futures = {executor.submit(_process_sample, sample, cfg, limiter): sample for sample in samples}
            for future in tqdm(as_completed(futures), total=len(futures), desc="Attack refine", unit="sample"):
                sample = futures[future]
                try:
                    result, responses, evals, progress = future.result()
                except Exception as exc:  # noqa: BLE001 - persist failed sample and continue
                    result = copy.deepcopy(sample)
                    result["meta"] = {
                        **result["meta"],
                        "attack_refined": False,
                        "attack_refine_success": False,
                        "attack_refine_attempts": 0,
                        "attack_refine_error": f"{type(exc).__name__}: {exc}",
                    }
                    responses = []
                    evals = []
                    progress = {
                        "traceid": sample["traceid"],
                        "status": "error",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                results.append(result)
                with write_lock:
                    _write_jsonl(out_file, result)
                    for record in responses:
                        _write_jsonl(response_file, record)
                    for record in evals:
                        _write_jsonl(eval_file, record)
                    _write_jsonl(progress_file, progress)

    results.sort(key=lambda item: int(item["traceid"]))
    return results
