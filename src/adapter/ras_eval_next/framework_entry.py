from __future__ import annotations

import asyncio
import importlib
import json
import os
import sys
import traceback
from typing import Any

from src.adapter.ras_eval_next.tool_runtime import ToolRuntime

FRAMEWORK_MODULES = {
    "langchain": "src.adapter.ras_eval_next.frameworks.langchain_agent",
    "autogen": "src.adapter.ras_eval_next.frameworks.autogen_agent",
    "mcp": "src.adapter.ras_eval_next.frameworks.mcp_agent",
    "openai-agent": "src.adapter.ras_eval_next.frameworks.openai_agent",
    "qwen-agent": "src.adapter.ras_eval_next.frameworks.qwen_agent",
}


def main() -> None:
    framework = os.environ["RAS_EVAL_FRAMEWORK"]
    model = os.environ["RAS_EVAL_MODEL"]
    if os.environ.get("OPENAI_BASE_URL") and not os.environ.get("OPENAI_API_BASE"):
        os.environ["OPENAI_API_BASE"] = os.environ["OPENAI_BASE_URL"]
    runtime: ToolRuntime | None = None
    try:
        runtime = ToolRuntime.from_env(
            replay_environment=not (framework == "mcp" and _sample_source() == "ras-eval-next")
        )
        module = importlib.import_module(FRAMEWORK_MODULES[framework])
        if hasattr(module, "run_async"):
            final_text = asyncio.run(module.run_async(runtime, model))
        else:
            final_text = module.run(runtime, model)
        print(json.dumps({"ok": True, "framework": framework, "final": final_text}, ensure_ascii=False), flush=True)
    except Exception as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "framework": framework,
                    "error": f"{type(exc).__name__}: {exc}",
                    "traceback": traceback.format_exc(),
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        sys.exit(1)
    finally:
        if runtime is not None:
            runtime.close()


def _sample_source() -> str:
    with open(os.environ["RAS_EVAL_SAMPLE_PATH"], encoding="utf-8") as file:
        return str(json.load(file).get("source"))


if __name__ == "__main__":
    main()
