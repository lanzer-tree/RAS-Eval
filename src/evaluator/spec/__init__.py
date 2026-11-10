from __future__ import annotations

import json
import shutil
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tqdm import tqdm

from src.evaluator.spec.replay import rebuild, replay_dir_for, scratch_dir_for
from src.runner.sandbox import SandboxSpec

DIMENSIONS = (
    ("utility", "completion_specifications"),
    ("safety", "safety_specifications"),
    ("security", "security_specifications"),
)


def _is_attack_sample(sample: dict[str, Any]) -> bool:
    return bool(sample.get("meta", {}).get("security_specifications"))


def _spec_dimensions(sample: dict[str, Any]) -> tuple[tuple[str, str], ...]:
    if _is_attack_sample(sample):
        return DIMENSIONS
    return (
        ("utility", "completion_specifications"),
        ("safety", "safety_specifications"),
    )


def merge_normal_specs(samples: list[dict[str, Any]], normal_path: Path) -> None:
    if not normal_path.exists():
        raise FileNotFoundError(f"normal dataset not found: {normal_path}")
    normal_samples = [
        json.loads(line)
        for line in normal_path.read_text(encoding="utf-8").split("\n")
        if line.strip()
    ]
    source = samples[0]["source"] if samples else ""
    if source == "agentdojo":
        index = {
            (s["meta"]["suite_name"], s["meta"]["user_task_id"]): s
            for s in normal_samples
        }
        def key(meta: dict[str, Any]) -> tuple[str, str]:
            return (meta["suite_name"], meta["user_task_id"])
    elif source == "skill_inject":
        index = {
            (s["meta"]["skill"], s["meta"]["task_prompt"]): s
            for s in normal_samples
        }
        def key(meta: dict[str, Any]) -> tuple[str, str]:
            return (meta["skill"], meta["task_prompt"])
    else:
        return
    for sample in samples:
        normal_sample = index.get(key(sample["meta"]))
        if not normal_sample:
            continue
        sample["meta"]["completion_specifications"] = normal_sample["meta"].get("completion_specifications", [])
        sample["meta"]["safety_specifications"] = normal_sample["meta"].get("safety_specifications", [])


@dataclass(frozen=True)
class EvaluationConfig:
    input_path: Path
    output_path: Path
    dataset_path: Path
    sandbox: str
    os: str
    image: str | None = None
    apptainer_path: str | None = None
    traceid: int | None = None
    parallel: int = 1
    timeout: int = 900
    nuxmv_timeout: int = 60
    skip_exist_traceid: bool = False


def normalize_response(response: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for message in response:
        message = dict(message)
        if message.get("tool_calls"):
            calls = []
            for call in message["tool_calls"]:
                function = dict(call["function"])
                if not isinstance(function.get("arguments"), str):
                    function["arguments"] = json.dumps(function.get("arguments", {}), ensure_ascii=False)
                calls.append({**call, "function": function})
            message["tool_calls"] = calls
        if message.get("role") == "tool" and not isinstance(message.get("content"), str):
            message["content"] = json.dumps(message.get("content"), ensure_ascii=False)
        normalized.append(message)
    return normalized


def evaluation_row(
    response: dict[str, Any],
    meta: dict[str, Any],
    results: list[str | list[str]],
    dimensions: tuple[tuple[str, str], ...] | None = None,
) -> dict[str, Any]:
    if dimensions is None:
        dimensions = DIMENSIONS
    groups = [(dimension, meta.get(key) or []) for dimension, key in dimensions]

    row: dict[str, Any] = {"traceid": int(response["traceid"])}
    cursor = 0
    evaluated: dict[str, dict[str, Any]] = {}
    for dimension, specs in groups:
        reports = []
        for spec in specs:
            result = results[cursor] if cursor < len(results) else "error: container did not return a result for this specification"
            reports.append({
                "formal_spec": spec["formal_spec"],
                "language_spec": spec.get("language_spec"),
                "result": result,
            })
            cursor += 1
        num_sat = sum(
            1
            for report in reports
            if (
                report["result"][-1] == "sat"
                if isinstance(report["result"], list) and report["result"]
                else report["result"] == "sat"
            )
        )
        evaluated[dimension] = {"num_sat": num_sat, "num_total": len(reports), "reports": reports}
    for dimension, _ in DIMENSIONS:
        row[dimension] = evaluated.get(dimension, {"num_sat": 0, "num_total": 0, "reports": []})
    return row


def evaluate_offline(sample: dict[str, Any], response: dict[str, Any], config: EvaluationConfig) -> dict[str, Any]:
    work_dir = replay_dir_for(config.input_path, int(response["traceid"]))
    scratch_dir = scratch_dir_for(work_dir)
    for path in (work_dir, scratch_dir):
        shutil.rmtree(path, ignore_errors=True)
    work_dir.mkdir(parents=True, exist_ok=True)
    spec = SandboxSpec(config.sandbox, config.image, config.os, config.apptainer_path)

    dimensions = _spec_dimensions(sample)
    flat_specs = [
        item["formal_spec"]
        for _, key in dimensions
        for item in (sample["meta"].get(key) or [])
    ]
    rebuild_error: str | None = None
    try:
        try:
            _, outcome = rebuild(
                sample,
                normalize_response(response["response"]),
                work_dir,
                spec,
                config.timeout,
                flat_specs,
                config.nuxmv_timeout,
                config.dataset_path,
            )
            results = outcome["results"]
        except Exception as exc:
            rebuild_error = f"{type(exc).__name__}: {exc}"
            print(f"[WARN] traceid={response['traceid']}: container rebuild verification failed ({rebuild_error})")
            results = [f"error: {rebuild_error}"] * len(flat_specs)
        row = evaluation_row(response, sample["meta"], results, dimensions=dimensions)
        if rebuild_error:
            row["rebuild_error"] = rebuild_error
        return row
    finally:
        if sample["source"] == "ras-eval-next":
            from src.adapter.ras_eval_next.common import cleanup_materialized_toolkit

            cleanup_materialized_toolkit(work_dir)
        for path in (work_dir, scratch_dir):
            shutil.rmtree(path, ignore_errors=True)
        try:
            work_dir.parent.rmdir()
        except OSError:
            pass


def evaluate_file(config: EvaluationConfig, samples: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    if samples is None:
        samples = [
            json.loads(line)
            for line in config.dataset_path.read_text(encoding="utf-8").split("\n")
            if line.strip()
        ]
    sample_by_traceid = {int(sample["traceid"]): sample for sample in samples}
    responses = [
        json.loads(line)
        for line in config.input_path.read_text(encoding="utf-8").split("\n")
        if line.strip()
    ]
    if config.traceid is not None:
        responses = [r for r in responses if int(r["traceid"]) == config.traceid]

    exist_traceids: set[int] = set()
    if config.output_path.exists() and config.skip_exist_traceid:
        exist_traceids = {
            int(json.loads(line)["traceid"])
            for line in config.output_path.read_text(encoding="utf-8").split("\n")
            if line.strip()
        }
    responses = [r for r in responses if int(r["traceid"]) not in exist_traceids]

    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    write_lock = threading.Lock()
    with config.output_path.open("a", encoding="utf-8") as out_file:
        with ThreadPoolExecutor(max_workers=max(1, config.parallel)) as executor:
            futures = [
                executor.submit(evaluate_offline, sample_by_traceid[int(response["traceid"])], response, config)
                for response in responses
            ]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Evaluation", unit="sample"):
                result = future.result()
                results.append(result)
                with write_lock:
                    out_file.write(json.dumps(result, ensure_ascii=False) + "\n")
                    out_file.flush()
    results.sort(key=lambda item: int(item["traceid"]))
    return results
