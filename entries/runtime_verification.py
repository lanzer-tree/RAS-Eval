"""Per-sample inference with LTL verification after every completed tool call."""
from __future__ import annotations

import json
import math
import os
import shutil
import sys
import threading
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tqdm import tqdm

from src.evaluator.spec import DIMENSIONS, _spec_dimensions, evaluation_row
from src.evaluator.spec.runtime import cleanup_runtime_dir, read_result_history, runtime_dir_for
from src.runner.deepseek_harness_runner import run_sample as run_deepseek_harness_sample
from src.runner.framework_runner import run_sample as run_framework_sample
from src.runner.hermes_runner import run_sample as run_hermes_sample
from src.runner.openclaw_runner import run_sample as run_openclaw_sample
from src.runner.opencode_runner import RateLimiter, RunnerConfig, run_sample as run_opencode_sample, traceid_filter
from src.runner.pi_runner import run_sample as run_pi_sample
from src.runner.sandbox import cleanup_sandbox_artifacts


def _parser() -> ArgumentParser:
    parser = ArgumentParser()
    parser.add_argument("--input_path", type=Path, required=True)
    parser.add_argument("--output_path", type=Path, required=True)
    parser.add_argument(
        "--framework",
        default="opencode",
        choices=[
            "opencode", "autogen", "langchain", "mcp", "openai-agent", "qwen-agent",
            "hermes", "openclaw", "deepseek-harness", "pi",
        ],
    )
    parser.add_argument("--model", required=True)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--parallel", type=int, default=1)
    parser.add_argument("--qps", type=float, default=1.0)
    parser.add_argument(
        "--request_qps",
        type=float,
        default=None,
        help="Approximate aggregate model-turn QPS for autogen/mcp/langchain (defaults to --qps; 0 disables pacing)",
    )
    parser.add_argument(
        "--request_max_retries",
        type=int,
        default=5,
        help="SDK retries for transient model API errors in autogen/mcp/langchain",
    )
    parser.add_argument("--traceid", type=int, default=None)
    parser.add_argument("--timeout", type=int, default=900)
    parser.add_argument("--skip_exist_traceid", action="store_true")
    parser.add_argument("--sandbox", choices=["docker", "apptainer"], default="docker")
    parser.add_argument("--os", choices=["mac", "linux"], default="linux")
    parser.add_argument("--apptainer_path", default=None)
    parser.add_argument("--image", default=None)
    parser.add_argument("--api_key", default=None)
    parser.add_argument("--base_url", default=None)
    return parser


# Runtime verification needs a sandbox that stays alive across the whole
# trajectory plus an in-container nuXmv, which only the sandboxed sources give us.
SUPPORTED_ATTACK_TYPES: dict[str, frozenset[str]] = {
    "skill_inject": frozenset({"cia"}),
    "ras-eval-next": frozenset({"cia-tool", "toma", "tpa"}),
}


def _validate_sample(sample: dict[str, Any]) -> None:
    source = sample.get("source")
    attack_type = (sample.get("meta") or {}).get("attack_type")
    if attack_type not in SUPPORTED_ATTACK_TYPES.get(str(source), frozenset()):
        supported = ", ".join(
            f"{name}/{value}"
            for name, values in SUPPORTED_ATTACK_TYPES.items()
            for value in sorted(values)
        )
        raise ValueError(
            f"runtime verification only supports {supported}; "
            f"got source={source!r}, attack_type={attack_type!r}"
        )


def _sandbox_dir(sample: dict[str, Any], output_path: Path) -> Path:
    if sample["source"] == "skill_inject":
        from src.adapter.skill_inject.common import sandbox_dir_for, sandbox_root_for
    else:
        from src.adapter.ras_eval_next.common import sandbox_dir_for, sandbox_root_for
    return sandbox_dir_for(sandbox_root_for(output_path), sample)


def _cleanup(sample: dict[str, Any], output_path: Path) -> None:
    sandbox_dir = _sandbox_dir(sample, output_path)
    cleanup_sandbox_artifacts(sandbox_dir)
    cleanup_runtime_dir(sandbox_dir)
    if sample["source"] == "ras-eval-next":
        from src.adapter.ras_eval_next.common import cleanup_materialized_toolkit

        cleanup_materialized_toolkit(sandbox_dir)
    shutil.rmtree(sandbox_dir, ignore_errors=True)
    try:
        sandbox_dir.parent.rmdir()
    except OSError:
        pass


def _runtime_ltl(sample: dict[str, Any], result: dict[str, Any], output_path: Path) -> dict[str, Any]:
    dimensions = _spec_dimensions(sample)
    flat_specs = [
        item["formal_spec"]
        for _, key in dimensions
        for item in (sample["meta"].get(key) or [])
    ]
    histories, errors = read_result_history(runtime_dir_for(_sandbox_dir(sample, output_path)), len(flat_specs))
    row = evaluation_row(result, sample["meta"], histories, dimensions=dimensions)
    if errors:
        row["verify_error"] = "; ".join(errors)
    return {"ltl": {dimension: row[dimension] for dimension, _ in DIMENSIONS}, **(
        {"verify_error": row["verify_error"]} if "verify_error" in row else {}
    )}


def run(args: Any, *, runner_overrides: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    request_qps = args.qps if args.request_qps is None else args.request_qps
    if not math.isfinite(request_qps) or request_qps < 0:
        raise ValueError("--request_qps (or inherited --qps) must be finite and non-negative")
    if args.request_max_retries < 0:
        raise ValueError("--request_max_retries must be non-negative")
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
    if args.base_url:
        os.environ["OPENAI_BASE_URL"] = args.base_url

    with args.input_path.open(encoding="utf-8") as file:
        samples = [json.loads(line) for line in file if line.strip()]
    if args.limit is not None:
        samples = samples[:args.limit]
    for sample in samples:
        _validate_sample(sample)

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    existing = []
    if args.output_path.exists():
        with args.output_path.open(encoding="utf-8") as file:
            existing = [int(json.loads(line)["traceid"]) for line in file if line.strip()]

    config = RunnerConfig(
        input_path=args.input_path,
        output_path=args.output_path,
        model=args.model,
        parallel=args.parallel,
        qps=args.qps,
        traceid=args.traceid,
        timeout=args.timeout,
        skip_exist_traceid=args.skip_exist_traceid,
        sandbox=args.sandbox,
        os=args.os,
        apptainer_path=args.apptainer_path,
        image=args.image,
        framework=args.framework,
        keep_sandbox=True,
        runtime_verification=True,
        request_qps=request_qps,
        request_max_retries=args.request_max_retries,
        **(runner_overrides or {}),
    )
    samples = traceid_filter(samples, config, existing)
    if not samples:
        print("No samples to run.")
        return []

    limiter = RateLimiter(args.qps)

    def run_one(sample: dict[str, Any]) -> dict[str, Any]:
        try:
            if args.framework == "opencode":
                result = run_opencode_sample(sample, config, limiter)
            elif args.framework == "hermes":
                result = run_hermes_sample(sample, config, limiter)
            elif args.framework == "openclaw":
                result = run_openclaw_sample(sample, config, limiter)
            elif args.framework == "deepseek-harness":
                result = run_deepseek_harness_sample(sample, config, limiter)
            elif args.framework == "pi":
                result = run_pi_sample(sample, config, limiter)
            else:
                result = run_framework_sample(sample, config, limiter)
            return {**result, **_runtime_ltl(sample, result, args.output_path)}
        finally:
            _cleanup(sample, args.output_path)

    results: list[dict[str, Any]] = []
    failure_count = 0
    write_lock = threading.Lock()
    with args.output_path.open("a", encoding="utf-8") as out_file:
        with ThreadPoolExecutor(max_workers=max(1, args.parallel)) as executor:
            futures = {executor.submit(run_one, sample): sample for sample in samples}
            for future in tqdm(as_completed(futures), total=len(futures), desc="Infer+RuntimeVerify", unit="sample"):
                sample = futures[future]
                try:
                    result = future.result()
                except Exception as error:
                    failure_count += 1
                    print(
                        f"[WARN] traceid={sample['traceid']}: sample failed "
                        f"({type(error).__name__}: {error}); continuing with the remaining samples."
                    )
                    continue
                results.append(result)
                with write_lock:
                    out_file.write(json.dumps(result, ensure_ascii=False) + "\n")
                    out_file.flush()
                    os.fsync(out_file.fileno())

    if failure_count and not results:
        raise RuntimeError(f"All {failure_count} sample(s) failed; no results were written")

    results.sort(key=lambda item: int(item["traceid"]))
    print(f"Wrote {len(results)} result(s) to {args.output_path}")
    for dimension, _ in DIMENSIONS:
        rows = [item["ltl"][dimension] for item in results if "ltl" in item]
        total = sum(row["num_total"] for row in rows)
        satisfied = sum(row["num_sat"] for row in rows)
        if total:
            print(f"ltl_{dimension}: {satisfied / total:.4f} ({satisfied}/{total} specs over {len(rows)} tasks)")
        else:
            print(f"ltl_{dimension}: no specs annotated")
    return results


def main() -> None:
    run(_parser().parse_args())


if __name__ == "__main__":
    main()
