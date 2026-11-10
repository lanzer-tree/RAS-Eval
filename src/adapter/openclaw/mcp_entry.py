"""Launch the ras-eval-next MCP server without relying on forwarded PYTHONPATH."""
from __future__ import annotations

import sys
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[3]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))

from src.adapter.ras_eval_next.ras_eval_mcp import main


if __name__ == "__main__":
    main()
