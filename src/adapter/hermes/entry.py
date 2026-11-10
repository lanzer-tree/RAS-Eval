"""Launch Hermes in its sealed venv while exposing the image's shared MCP SDK."""
from __future__ import annotations

import sys
from pathlib import Path


GLOBAL_SITE_PACKAGES = Path("/usr/local/lib/python3.11/site-packages")
if GLOBAL_SITE_PACKAGES.exists() and str(GLOBAL_SITE_PACKAGES) not in sys.path:
    # Append rather than prepend so Hermes keeps its pinned dependencies; the
    # image-level MCP SDK is only a fallback for the optional package omitted by
    # installations made with --skip-setup.
    sys.path.append(str(GLOBAL_SITE_PACKAGES))

from hermes_cli.main import main


if __name__ == "__main__":
    raise SystemExit(main())
