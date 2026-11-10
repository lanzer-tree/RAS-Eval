from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from entries.runtime_verification import _parser, run


def main() -> None:
    parser = _parser()
    parser.set_defaults(framework="opencode")
    parser.add_argument("--agentdog_base_url", required=True)
    parser.add_argument("--agentdog_model", default="AgentDoG1.5-Qwen3.5-4B")
    parser.add_argument("--agentdog_timeout", type=float, default=30.0)
    args = parser.parse_args()
    if args.framework != "opencode":
        parser.error("AgentDoG runtime verification only supports --framework opencode")
    run(
        args,
        runner_overrides={
            "agentdog_runtime_verification": True,
            "agentdog_base_url": args.agentdog_base_url,
            "agentdog_model": args.agentdog_model,
            "agentdog_timeout": args.agentdog_timeout,
        },
    )


if __name__ == "__main__":
    main()
