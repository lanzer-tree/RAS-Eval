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
    args = parser.parse_args()
    if args.framework != "opencode":
        parser.error("ClawGuard runtime verification only supports --framework opencode")
    run(args, runner_overrides={"clawguard": True})


if __name__ == "__main__":
    main()
