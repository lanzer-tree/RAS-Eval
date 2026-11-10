from __future__ import annotations

import contextlib
import json
import os
import sys
import traceback
from typing import Any

from src.adapter.ras_eval_next.tool_runtime import ToolRuntime


def _selected_tool_names(runtime: ToolRuntime) -> list[str]:
    names: list[str] = []
    if runtime.source == "ras-eval-next":
        names.extend(str(name) for name in runtime.meta.get("tools") or [])
    extras = os.environ.get("DAEDALUS_BRIDGE_EXTRA_TOOLS", "")
    names.extend(name.strip() for name in extras.split(",") if name.strip())
    return list(dict.fromkeys(name for name in names if name in runtime.tools))


def _write(value: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(value, ensure_ascii=False, default=str) + "\n")
    sys.stdout.flush()


def main() -> None:
    runtime: ToolRuntime | None = None
    try:
        # Toolkit imports and environment replay may print diagnostics. Keep stdout
        # reserved for the JSONL protocol consumed by the JavaScript adapter.
        with contextlib.redirect_stdout(sys.stderr):
            runtime = ToolRuntime.from_env(record_trace=False, runtime_verification=False)
        names = _selected_tool_names(runtime)
        tools = [runtime.tools[name].schema["function"] for name in names]
        _write({"type": "ready", "tools": tools})

        for line in sys.stdin:
            if not line.strip():
                continue
            request: dict[str, Any] = {}
            try:
                request = json.loads(line)
                if request.get("type") == "close":
                    break
                request_id = request.get("id")
                name = str(request.get("tool") or "")
                arguments = request.get("arguments")
                with contextlib.redirect_stdout(sys.stderr):
                    result = runtime.call_tool(name, arguments)
                _write({"id": request_id, "ok": True, "result": result})
            except Exception as exc:
                traceback.print_exc(file=sys.stderr)
                _write({
                    "id": request.get("id"),
                    "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                })
    except Exception as exc:
        traceback.print_exc(file=sys.stderr)
        _write({"type": "fatal", "error": f"{type(exc).__name__}: {exc}"})
        raise
    finally:
        if runtime is not None:
            runtime.close()


if __name__ == "__main__":
    main()
