import os
import statistics
import sys
from argparse import ArgumentParser
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.baseline.evaluation.perturb import TYPES
from src.baseline.evaluation.runner import JudgeConfig, run


def parse_perturbations(raw: str | None) -> tuple[str, ...]:
    """Resolve ``--perturbations`` against the known types, keeping their order."""
    if not raw:
        return TYPES
    requested = [item.strip() for item in raw.split(",") if item.strip()]
    unknown = [item for item in requested if item not in TYPES]
    if unknown:
        raise SystemExit(f"unknown perturbation type(s): {', '.join(unknown)}; choose from {', '.join(TYPES)}")
    return tuple(item for item in TYPES if item in requested)


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--dataset_path", type=Path, help="jsonl dataset with task meta information")
    parser.add_argument("--response_path", type=Path, help="jsonl agent responses")
    parser.add_argument("--output_path", type=Path, help="save path of judge result")
    parser.add_argument("--judge_model", type=str, help="The LLM used for judging")
    parser.add_argument("--mode", type=str, choices=["llm", "agent"], help="LLM-as-a-Judge or Agent-as-a-Judge")
    parser.add_argument("--limit", type=int, default=None, help="Max number of samples to run")
    parser.add_argument("--parallel", type=int, default=1, help="Number of worker processes (data-parallel shards)")
    parser.add_argument("--qps", type=float, default=1.0, help="Per-process qps limit of LLM API")
    parser.add_argument("--traceid", type=int, default=None, help="The selected traceid")
    parser.add_argument("--timeout", type=int, default=900, help="Timeout seconds for one opencode run")
    parser.add_argument("--skip_exist_traceid", action="store_true", help="Skip exist traceid")
    parser.add_argument("--sandbox", type=str, choices=["docker", "apptainer"], default="docker", help="The type of sandbox")
    parser.add_argument("--os", type=str, choices=["mac", "linux"], default="linux", help="Host OS")
    parser.add_argument("--apptainer_path", type=str, default=None, help="The path of apptainer executable")
    parser.add_argument("--image", type=str, default=None, help="Docker image name or apptainer .sif path")
    parser.add_argument("--api_key", type=str, default=None, help="llm api key")
    parser.add_argument("--base_url", type=str, default=None, help="llm base url")
    parser.add_argument(
        "--perturbations",
        type=str,
        default=None,
        help=f"comma-separated subset of {','.join(TYPES)}; defaults to all of them",
    )
    args = parser.parse_args()
    perturbations = parse_perturbations(args.perturbations)
    # CLI-provided credentials take precedence: the judge reads
    # OPENAI_API_KEY / OPENAI_BASE_URL from the environment and only falls back
    # to .env for unset variables.
    if args.api_key:
        os.environ["OPENAI_API_KEY"] = args.api_key
    if args.base_url:
        os.environ["OPENAI_BASE_URL"] = args.base_url

    config = JudgeConfig(
        dataset_path=args.dataset_path,
        response_path=args.response_path,
        output_path=args.output_path,
        judge_model=args.judge_model,
        mode=args.mode,
        sandbox=args.sandbox,
        os=args.os,
        limit=args.limit,
        parallel=args.parallel,
        qps=args.qps,
        traceid=args.traceid,
        timeout=args.timeout,
        skip_exist_traceid=args.skip_exist_traceid,
        apptainer_path=args.apptainer_path,
        image=args.image,
        perturbations=perturbations,
    )
    results = run(config)

    print(f"\n=== {args.mode}-as-a-judge: {args.output_path} ===")
    for perturbation in perturbations:
        rows = [row for row in results if row["type"] == perturbation]
        if not rows:
            continue
        counts = Counter(row["utility_judge"] for row in rows)
        security = Counter(row["security_judge"] for row in rows)
        print(
            f"{perturbation:22s} n={len(rows):3d} "
            f"complete={counts[True]:3d} incomplete={counts[False]:3d} "
            f"safe={security[True]:3d} unsafe={security[False]:3d} "
            f"error={counts['error']:3d}"
        )
        timed = [row["timing"]["judge_seconds"] for row in rows if "judge_seconds" in row.get("timing", {})]
        if timed:
            print(
                f"{'':22s} judge seconds: mean={statistics.fmean(timed):.2f} "
                f"median={statistics.median(timed):.2f} min={min(timed):.2f} max={max(timed):.2f} n={len(timed)}"
            )


if __name__ == "__main__":
    main()
