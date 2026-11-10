"""SKILL-INJECT utility (task-completion) evaluator.

Faithful to ``lib/skill-inject`` utility baseline evaluation: for each task an
LLM-as-judge inspects the *post-run sandbox* (modified files + agent stdout +
``.command_history``) and decides whether the user's task was completed. The
judge prompt and verdict parsing are byte-for-byte identical to lib; only the
judge is executed via opencode inside the same Docker image instead of the
codex/claude CLI.

Utility = fraction of tasks with verdict ``task_success``.
"""
from __future__ import annotations

import json
import os
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import threading
from tqdm import tqdm

from src.adapter.skill_inject.common import (
    render_transcript,
    sandbox_dir_for,
    sandbox_root_for,
)
from src.adapter.skill_inject.judge import build_task_prompt, parse_task_verdict
from src.runner.opencode_runner import _load_env
from src.runner.sandbox import SandboxSpec, build_command, opencode_config_bind, opencode_home_path, cleanup_sandbox_artifacts

# Same technical-error markers lib treats as non-evaluable failures.
TECHNICAL_ERROR_MARKERS = (
    "Rate limit exceeded",
    "usage_limit_reached",
    "429 Too Many Requests",
)

# PARALLEL_EVALUATIONS = 8
# JUDGE_TIMEOUT = 300


@dataclass(frozen=True)
class EvaluationConfig:
    input_path: Path
    output_path: Path
    dataset_path: Path
    model: str
    sandbox: str
    os: str
    traceid: int | None = None
    parallel: int = 4
    timeout: int = 900
    skip_exist_traceid: bool = True
    qps: float = 1.0
    apptainer_path: str | None = None
    image: str | None = None


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def opencode_judge_config(model: str) -> str:
    """opencode config for the judge: same provider, all skills denied (the
    judge only inspects files, it must not load task skills)."""
    _load_env()
    base_url = os.environ.get("OPENAI_BASE_URL")
    api_key = os.environ.get("OPENAI_API_KEY")
    # if not base_url or not api_key:
    #     raise RuntimeError(
    #         "OPENAI_BASE_URL / OPENAI_API_KEY must be set (via .env) for the judge."
    #     )
    provider_id, _, model_id = model.partition("/")
    config = {
        "provider": {
            provider_id: {
                "npm": "@ai-sdk/openai-compatible",
                "name": provider_id,
                "options": {"baseURL": base_url, "apiKey": api_key},
                "models": {model_id: {}},
            }
        },
        "permission": {
            "*": "allow",
            "question": "deny",
            "external_directory": {"*": "allow"},
            "doom_loop": "allow",
            "skill": {"*": "deny"},
        },
    }
    return json.dumps(config, ensure_ascii=False)


def _extract_text(stdout: str) -> str:
    """Join all assistant ``text`` parts from opencode's json event stream."""
    texts: list[str] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("type") == "text":
            texts.append(event.get("part", {}).get("text", ""))
    return "\n".join(t for t in texts if t)


def _extract_verdict_json(text: str) -> str:
    """Return the last JSON object containing a ``verdict`` key found anywhere in
    the judge output, as a JSON string. Models often wrap the verdict in prose
    or a ```json fence; ``parse_task_verdict`` expects a clean JSON string, so we
    isolate it first (the verdict-decision logic itself stays identical to lib).
    """
    decoder = json.JSONDecoder()
    best: str | None = None
    idx = 0
    while True:
        start = text.find("{", idx)
        if start == -1:
            break
        try:
            obj, end = decoder.raw_decode(text, start)
        except json.JSONDecodeError:
            idx = start + 1
            continue
        if isinstance(obj, dict) and "verdict" in obj:
            best = json.dumps(obj, ensure_ascii=False)
        idx = end
    return best if best is not None else text


def _run_judge(
    sandbox_dir: Path, 
    judge_prompt: str, 
    judge_config: str, 
    model: str, 
    image: str,
    config: EvaluationConfig,
) -> str:
    spec = SandboxSpec(config.sandbox, image, config.os, config.apptainer_path)
    config_bind, config_env = opencode_config_bind(sandbox_dir, judge_config)
    binds = [(str(sandbox_dir.absolute()), "/workspace", False), config_bind]
    env = {**config_env, "OPENCODE_DISABLE_AUTOUPDATE": "1"}
    command = build_command(spec, binds, env, ["opencode", "run", "--model", model, "--format", "json"], writable_home=opencode_home_path(sandbox_dir))
    try:
        completed = subprocess.run(
            command, env=os.environ.copy(), input=judge_prompt, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=config.timeout, check=False,
        )
        return _extract_text(completed.stdout)
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout or ""
        if isinstance(out, bytes):
            out = out.decode("utf-8", errors="replace")
        return _extract_text(out)
    finally:
        cleanup_sandbox_artifacts(sandbox_dir)


def _has_technical_failure(sandbox_dir: Path) -> bool:
    stderr = sandbox_dir / "agent_stderr.txt"
    if stderr.exists():
        content = stderr.read_text(encoding="utf-8", errors="ignore")
        return any(marker in content for marker in TECHNICAL_ERROR_MARKERS)
    return False


def traceid_filter(samples: Iterable[dict[str, Any]], config: EvaluationConfig, exist_traceids: list[int]) -> list[dict[str, Any]]:
    if config.traceid is None:
        if config.skip_exist_traceid:
            samples = [sample for sample in samples if int(sample["traceid"]) not in exist_traceids]
            return samples
        else:
            return samples
    else:
        for sample in samples:
            if sample["traceid"] == config.traceid:
                return [sample]
    return []


def evaluate_single(
    response: dict[str, Any],
    sample: dict[str, Any],
    sandbox_dir: Path,
    judge_config: str,
    config: EvaluationConfig,
) -> dict[str, Any]:
    traceid = response["traceid"]
    image = config.image

    if not sandbox_dir.exists():
        return {
            "traceid": traceid, "utility": False, "verdict": "technical",
            "evidence": f"sandbox not found: {sandbox_dir}",
        }

    # Refresh agent_stdout.txt from the recorded response so the judge sees the
    # same transcript regardless of who produced the sandbox.
    messages = response.get("response") or []
    if messages:
        (sandbox_dir / "agent_stdout.txt").write_text(
            render_transcript(messages), encoding="utf-8"
        )

    if _has_technical_failure(sandbox_dir):
        return {
            "traceid": traceid, "utility": False, "verdict": "technical",
            "evidence": "technical failure detected in agent_stderr.txt",
        }

    judge_prompt = build_task_prompt(sample["meta"]["task_prompt"])
    judge_output = _run_judge(sandbox_dir, judge_prompt, judge_config, config.model, image, config)
    verdict = parse_task_verdict(_extract_verdict_json(judge_output))
    return {
        "traceid": traceid,
        "utility": verdict == "task_success",
        "verdict": verdict,
        "evidence": judge_output,
    }


def evaluate_file(config: EvaluationConfig) -> list[dict[str, Any]]:
    with open(config.input_path, "r", encoding="utf-8") as file:
        responses = [json.loads(line) for line in file]
    dataset = {}
    with open(config.dataset_path, "r", encoding="utf-8") as file:
        for line in file:
            sample = json.loads(line)
            dataset[sample["traceid"]] = sample

    if config.output_path.exists():
        with open(config.output_path, "r", encoding="utf-8") as file:
            exist_outputs = [json.loads(line) for line in file]
            exist_traceids = [int(output["traceid"]) for output in exist_outputs]
    else:
        config.output_path.parent.mkdir(parents=True, exist_ok=True)
        exist_traceids = []

    responses = traceid_filter(responses, config, exist_traceids)

    sandbox_root = sandbox_root_for(config.input_path)
    judge_config = opencode_judge_config(config.model)

    jobs = []
    for response in responses:
        traceid = response["traceid"]
        sample = dataset[traceid]
        sandbox_dir = sandbox_dir_for(sandbox_root, sample)
        jobs.append((response, sample, sandbox_dir))

    results: list[dict[str, Any]] = []
    write_lock = threading.Lock()
    with config.output_path.open("a", encoding="utf-8") as out_file:
        with ThreadPoolExecutor(max_workers=config.parallel) as pool:
            futures = [
                pool.submit(evaluate_single, r, s, d, judge_config, config)
                for (r, s, d) in jobs
            ]
            for future in tqdm(
                as_completed(futures), total=len(futures),
                desc="Evaluation", unit="sample",
            ):
                result = future.result()
                results.append(result)
                with write_lock:
                    out_file.write(json.dumps(result, ensure_ascii=False) + "\n")
                    out_file.flush()
                    os.fsync(out_file.fileno())

    results.sort(key=lambda item: int(item["traceid"]))
    return results


def evaluate(config: EvaluationConfig) -> list[dict[str, Any]]:
    return evaluate_file(config)
