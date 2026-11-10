from __future__ import annotations

import math
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from entries.runtime_verification import _parser, run


def main() -> None:
    parser = _parser()
    parser.set_defaults(
        framework="opencode", parallel=1, timeout=7200,
        image="ras-eval-agent:information-flow",
    )
    parser.add_argument("--analysis_budget", type=str.upper, choices=["L0", "L1", "L2", "L3"], default="L2")
    parser.add_argument("--query_mode", choices=["source", "sink", "source-sink"], default="sink")
    parser.add_argument("--analysis_timeout", type=float, default=300.0)
    parser.add_argument("--review_timeout", type=float, default=600.0)
    args = parser.parse_args()
    if args.framework != "opencode":
        parser.error("information_flow only supports --framework opencode")
    if any(not math.isfinite(value) or value <= 0 for value in (args.analysis_timeout, args.review_timeout)):
        parser.error("analysis_timeout/review_timeout must be a positive finite number of seconds")
    sandbox_root = args.output_path.parent / (args.output_path.stem + "_sandboxes")
    if sandbox_root.is_symlink() or (sandbox_root.exists() and (not sandbox_root.is_dir() or any(sandbox_root.iterdir()))):
        parser.error("Task sandbox directory already exists and is non-empty; refusing to overwrite or delete existing files")
    run(args, runner_overrides={
        "information_flow": True,
        "analysis_budget": args.analysis_budget,
        "query_mode": args.query_mode,
        "analysis_timeout": args.analysis_timeout,
        "review_timeout": args.review_timeout,
    })


if __name__ == "__main__":
    main()
