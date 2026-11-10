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
    parser.add_argument("--shieldagent_base_url", required=True)
    parser.add_argument("--shieldagent_model", default="ShieldAgent")
    parser.add_argument("--shieldagent_timeout", type=float, default=30.0)
    args = parser.parse_args()
    if args.framework != "opencode":
        parser.error("ShieldAgent runtime verification only supports --framework opencode")
    run(
        args,
        runner_overrides={
            "shieldagent_runtime_verification": True,
            "shieldagent_base_url": args.shieldagent_base_url,
            "shieldagent_model": args.shieldagent_model,
            "shieldagent_timeout": args.shieldagent_timeout,
        },
    )


if __name__ == "__main__":
    main()
