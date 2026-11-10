from __future__ import annotations

import functools
import inspect
import json
import os
import sys
import traceback
import typing
from pathlib import Path
from typing import Any, Callable
from mcp.server.fastmcp import FastMCP
from src.toolkits.agentdojo.common import to_plain
from src.adapter.agentdojo.agentdojo_environment import build_environment, dump_environment, suite_tools


def _bind_environment(function: Callable[..., Any], environment: Any, dump_dir: Path | None) -> Callable[..., Any]:
    """Wrap an AgentDojo tool so FastMCP sees a clean signature.

    The original tool functions take the suite ``environment`` as their first
    argument. That argument is injected here and hidden from the tool schema so
    that the model only sees the real parameters. The result is serialized to a
    JSON string to keep parity with the previous hand-rolled MCP server.

    When ``dump_dir`` is set the environment state is snapshotted to disk after
    every call, so the last dump is the post-run state even though opencode
    kills this process without a graceful shutdown.
    """
    hints = typing.get_type_hints(function)
    signature = inspect.signature(function)  

    parameters = []
    for name, parameter in signature.parameters.items():
        if name == "environment":
            continue
        annotation = hints.get(name, parameter.annotation)
        parameters.append(parameter.replace(annotation=annotation))
    new_signature = signature.replace(parameters=parameters, return_annotation=str)

    @functools.wraps(function)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        try:
            result = function(environment, *args, **kwargs)
            return json.dumps(to_plain(result), ensure_ascii=False)
        except Exception as exc:
            # AgentDojo tools raise exceptions (e.g. ValueError for "not found")
            # as a normal control-flow signal. Return the error back to opencode
            # as the tool result so the model can recover, matching AgentDojo's
            # native ``run_function`` behavior (``'ErrorType: ErrorMessage'``)
            # instead of tearing down the whole MCP server. The traceback is
            # still logged to stderr for diagnostics.
            # print(
            #     f"[agentdojo-mcp] tool {function.__name__} raised, returning error to model:\n"
            #     + traceback.format_exc(),
            #     file=sys.stderr,
            #     flush=True,
            # )
            return f"{type(exc).__name__}: {exc}"
        finally:
            if dump_dir is not None:
                dump_environment(environment, dump_dir)

    wrapper.__signature__ = new_signature
    annotations = {name: hint for name, hint in hints.items() if name != "environment"}
    annotations["return"] = str
    wrapper.__annotations__ = annotations
    return wrapper


def build_server() -> FastMCP:
    suite_name = os.environ["AGENTDOJO_SUITE"]
    # The sample travels either inline or through a file: apptainer sources env
    # vars from a generated shell script that shreds JSON quotes, so sandboxed
    # callers (e.g. the annotate preflight) pass a path instead.
    if os.environ.get("AGENTDOJO_SAMPLE_PATH"):
        sample = json.loads(Path(os.environ["AGENTDOJO_SAMPLE_PATH"]).read_text(encoding="utf-8"))
    else:
        sample = json.loads(os.environ["AGENTDOJO_SAMPLE_JSON"])
    environment = build_environment(suite_name, sample["meta"]["environment"])

    dump_dir = Path(os.environ["AGENTDOJO_ENV_DUMP_DIR"]) if os.environ.get("AGENTDOJO_ENV_DUMP_DIR") else None
    if dump_dir is not None:
        # Dump the initial state so a trajectory without any tool call still has
        # an environment snapshot to verify against.
        dump_environment(environment, dump_dir)

    server = FastMCP(name=f"agentdojo-{suite_name}")
    for function in suite_tools(suite_name):
        tool = _bind_environment(function, environment, dump_dir)
        server.add_tool(
            tool,
            name=function.__name__,
            description=inspect.getdoc(function) or function.__name__,
            structured_output=False,
        )
    return server


def main() -> None:
    try:
        server = build_server()
    except Exception:
        print(
            "[agentdojo-mcp] failed to build server, stopping:\n"
            + traceback.format_exc(),
            file=sys.stderr,
            flush=True,
        )
        os._exit(1)
    # Preflight mode: build the server (surfacing any startup error) and exit
    # without serving over stdio. The harness uses this to fail fast before
    # launching opencode, instead of letting opencode silently fall back to its
    # builtin tools when the MCP server is broken.
    if "--check" in sys.argv[1:]:
        print("[agentdojo-mcp] ok", file=sys.stderr, flush=True)
        return
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
