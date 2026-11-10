"""Run the judge baselines over one (dataset, response) pair.

Every sample is judged once per perturbation type, so a single entry run yields
the unperturbed verdict plus the four perturbed ones in the same output file.
"""
from __future__ import annotations

import contextlib
import json
import shutil
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tqdm import tqdm

from src.adapter.ras_eval_next.common import cleanup_materialized_toolkit
from src.baseline.evaluation import judge, materials, perturb
from src.runner.opencode_runner import RateLimiter
from src.runner.sandbox import SandboxSpec, cleanup_sandbox_artifacts


@dataclass(frozen=True)
class JudgeConfig:
    dataset_path: Path
    response_path: Path
    output_path: Path
    judge_model: str
    mode: str
    sandbox: str
    os: str
    limit: int | None = None
    parallel: int = 1
    qps: float = 1.0
    traceid: int | None = None
    timeout: int = 900
    skip_exist_traceid: bool = False
    apptainer_path: str | None = None
    image: str | None = None
    # Perturbation types to judge. Defaults to the full robustness matrix; a
    # cost-measurement run narrows it to ("none",) so every recorded second is
    # spent judging the real trajectory.
    perturbations: tuple[str, ...] = perturb.TYPES


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    return [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").split("\n")
        if line.strip()
    ]


def judge_root(config: JudgeConfig) -> Path:
    return config.output_path.parent / f"{config.output_path.stem}_judge"


def split_timing(marks: dict[str, float]) -> dict[str, float]:
    """Turn the perf_counter checkpoints of one judgement into stage durations.

    ``judge_seconds`` is the evaluator's own cost -- one chat completion for the
    LLM judge, one sandboxed agent run for the agent judge -- and is the number
    comparable to an LTL verification pass. Preparing the material folder and
    deleting it afterwards are reported separately so a cost study can exclude
    them, mirroring how the nuXmv benchmark excludes model construction.
    """
    stages = (("prepare", "start", "prepared"), ("judge", "prepared", "judged"), ("cleanup", "judged", "finished"))
    timing = {
        f"{name}_seconds": marks[end] - marks[begin]
        for name, begin, end in stages
        if begin in marks and end in marks
    }
    timing["total_seconds"] = marks["finished"] - marks["start"]
    return timing


def judge_one(
    sample: dict[str, Any],
    response: dict[str, Any],
    perturbation: str,
    config: JudgeConfig,
    llm,
) -> dict[str, Any]:
    traceid = int(response["traceid"])
    judge_dir = judge_root(config) / f"TASK-{traceid}-{perturbation}"
    shutil.rmtree(judge_dir, ignore_errors=True)
    marks: dict[str, float] = {"start": time.perf_counter()}
    try:
        transcript = perturb.transcript(response["response"], perturbation, llm, judge.api_model(config.judge_model))
        materials.build(sample, transcript, judge_dir, config.dataset_path)
        marks["prepared"] = time.perf_counter()
        if config.mode == "llm":
            row = judge.judge_llm(judge_dir, perturbation, llm, config.judge_model)
        else:
            spec = SandboxSpec(config.sandbox, config.image, config.os, config.apptainer_path)
            row = judge.judge_agent(judge_dir, sample, perturbation, config.judge_model, spec, config.timeout)
        marks["judged"] = time.perf_counter()
    finally:
        cleanup_sandbox_artifacts(judge_dir)
        cleanup_materialized_toolkit(judge_dir)
        shutil.rmtree(judge_dir, ignore_errors=True)
        marks["finished"] = time.perf_counter()
    return {"traceid": traceid, "type": perturbation, "mode": config.mode, "timing": split_timing(marks), **row}


def judge_job(
    sample: dict[str, Any],
    response: dict[str, Any],
    perturbation: str,
    config: JudgeConfig,
    llm,
    limiter: RateLimiter,
) -> dict[str, Any]:
    limiter.wait()
    started = time.perf_counter()
    try:
        return judge_one(sample, response, perturbation, config, llm)
    except Exception as error:
        message = f"{type(error).__name__}: {error}"
        print(f"[judge] traceid={response['traceid']} type={perturbation} failed: {message}")
        return {
            "traceid": int(response["traceid"]),
            "type": perturbation,
            "mode": config.mode,
            "timing": {"total_seconds": time.perf_counter() - started},
            "utility_judge": "error",
            "security_judge": "error",
            "reason": {"error": message},
        }


def run(config: JudgeConfig) -> list[dict[str, Any]]:
    samples = {int(sample["traceid"]): sample for sample in read_jsonl(config.dataset_path)}
    responses = read_jsonl(config.response_path)
    if config.traceid is not None:
        responses = [r for r in responses if int(r["traceid"]) == config.traceid]
    if config.limit is not None:
        responses = responses[: config.limit]

    done: set[tuple[int, str]] = set()
    if config.skip_exist_traceid and config.output_path.exists():
        done = {(int(row["traceid"]), row["type"]) for row in read_jsonl(config.output_path)}

    jobs = [
        (samples[int(response["traceid"])], response, perturbation)
        for response in responses
        for perturbation in config.perturbations
        if (int(response["traceid"]), perturbation) not in done
    ]

    llm = judge.client()
    limiter = RateLimiter(config.qps)
    config.output_path.parent.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    write_lock = threading.Lock()
    with config.output_path.open("a", encoding="utf-8") as out_file:
        with ThreadPoolExecutor(max_workers=max(1, config.parallel)) as executor:
            futures = [
                executor.submit(judge_job, sample, response, perturbation, config, llm, limiter)
                for sample, response, perturbation in jobs
            ]
            for future in tqdm(as_completed(futures), total=len(futures), desc=f"{config.mode}-judge", unit="judge"):
                result = future.result()
                results.append(result)
                with write_lock:
                    out_file.write(json.dumps(result, ensure_ascii=False) + "\n")
                    out_file.flush()
    # Every sample folder is deleted right after its judgement; drop the now empty
    # parent so a run leaves nothing but its jsonl.
    with contextlib.suppress(OSError):
        judge_root(config).rmdir()
    results.sort(key=lambda row: (row["traceid"], row["type"]))
    return results
