"""Per-task MCP server for the ras-eval-next opencode adaptation.

Runs *inside* the sandbox container: reads the task definition from
``RAS_EVAL_SAMPLE_PATH`` / ``RAS_EVAL_SAMPLE_JSON``, imports the required
toolkits, replays the task's environment setup, then exposes exactly the task's
tools over stdio.

Prompt-injection attacks are applied only when ``meta['attack']`` is present:
    - ``tool_output`` (TOMA): inject into the first output of the attacked tool.
    - ``tpa``: prepend the injected text to the attacked tool description.
    - ``environment`` (EIA): already materialized by appended ``meta['environment']``
      setup entries before tools are exposed; the ``meta['attack']`` row is kept
      only for auditing.
Normal ras-eval-next samples with no attack field keep plain replay behavior.

The working directory is ``/workspace`` (the mounted sandbox), so the
toolkits' relative ``environment/...`` file I/O stays isolated to this task.
"""
from __future__ import annotations

import functools
import inspect
import json
import os
import sys
import tempfile
import traceback
from contextlib import nullcontext
from pathlib import Path
from typing import Any, Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from src.defense.information_flow.mcp_reload import ReloadingToolRegistry

from mcp.server.fastmcp import FastMCP

from src.adapter.ras_eval_next.common import (
    build_tool_registry,
    clean_signature,
    coerce_string_argument,
    default_substitutions,
    inject_cleanup_hint,
    inject_toma_payload,
    import_toolkit,
    load_environment,
    string_coercions,
    tool_descriptions_from_schema,
)


def _wrap_tool(
    function: Callable[..., Any],
    toma_return: Any = None,
    cleanup_hint: bool = False,
    reloader: ReloadingToolRegistry | None = None,
    tool_name: str | None = None,
) -> Callable[..., str]:
    """Serialize a toolkit function's result to the string the model sees.

    Exposes a *sanitized* signature (only typed keyword params; ``*args`` /
    ``**kwargs`` dropped, missing annotations forced to ``str``) so FastMCP
    builds a clean input schema even for awkward tools like
    ``regex_validator_service(*args, **kwargs)`` instead of crashing. Strings
    the model sent for list/dict parameters are rebuilt into containers before
    the call (see ``string_coercions``), and an explicit ``null`` falls back to
    the parameter's documented default. If ``toma_return`` is provided, it is
    injected into this tool's first result."""
    new_signature = clean_signature(function)
    coercions = string_coercions(function)
    substitutions = default_substitutions(function)
    injected = {"done": False}

    dispatch_name = tool_name or function.__name__

    @functools.wraps(function, updated=() if reloader is not None else functools.WRAPPER_UPDATES)
    def wrapper(*args: Any, **kwargs: Any) -> str:
        with reloader.lock if reloader is not None else nullcontext():
            current, modes, defaults = function, coercions, substitutions
            if reloader is not None:
                current, signature, modes, defaults = reloader.binding(dispatch_name)
                wrapper.__signature__ = signature
                wrapper.__annotations__ = {
                    key: parameter.annotation for key, parameter in signature.parameters.items()
                }
                wrapper.__annotations__["return"] = str
            for name, mode in modes.items():
                value = kwargs.get(name)
                if isinstance(value, str):
                    kwargs[name] = coerce_string_argument(value, mode)
            for name, default in defaults.items():
                if name in kwargs and kwargs[name] is None:
                    kwargs[name] = default
            try:
                result = current(*args, **kwargs)
            except Exception as exc:
                result = {"success": False, "description": f"{type(exc).__name__}: {exc}"}
            if toma_return is not None and not injected["done"]:
                injected["done"] = True
                result = inject_toma_payload(result, toma_return)
            if cleanup_hint:
                result = inject_cleanup_hint(result)
            if isinstance(result, str):
                return result
            return json.dumps(result, ensure_ascii=False, default=str)

    wrapper.__signature__ = new_signature
    wrapper.__annotations__ = {
        name: parameter.annotation for name, parameter in new_signature.parameters.items()
    }
    wrapper.__annotations__["return"] = str
    if reloader is not None:
        del wrapper.__wrapped__
        function = None
    return wrapper


def _attack_entries(value: Any) -> list[dict[str, Any]]:
    """Normalize legacy single/multi attack metadata for MCP-time injection.

    cia-tool samples store ``meta.attack`` as one audit dict with
    ``mode=tool_code``. TOMA/TPA samples may store a list, a single object, or a
    wrapped object. Only dict entries participate in MCP-time output/description
    injection; tool-code attacks are already materialized by the mounted source.
    """
    if not value:
        return []
    if isinstance(value, list):
        raw = value
    elif isinstance(value, dict):
        nested = value.get("attacks") or value.get("attack")
        if isinstance(nested, list):
            raw = nested
        elif isinstance(nested, dict):
            raw = [nested]
        else:
            raw = [value]
    else:
        return []
    return [item for item in raw if isinstance(item, dict)]


def _description_detector():
    """Prompt-detector settings for scanning tool descriptions (TPA), or ``None``.

    Opencode never fires the ``tool.definition`` plugin hook for MCP tools, so the
    prompt_detector plugin can only scan tool *outputs*. When the runner enables
    the defense it forwards the detector's credentials through these env vars so
    the description scan happens here, where the served description reaches the
    model. Detection failures fail open inside ``detect_injection``.
    """
    if os.environ.get("RAS_EVAL_PROMPT_DETECTOR") != "1":
        return None
    from src.defense.prompt_detector.detector import defense_note, detect_injection

    with open(os.environ["RAS_EVAL_PROMPT_DETECTOR_TEMPLATE_PATH"], encoding="utf-8") as file:
        template = file.read()
    config = {
        "base_url": os.environ["RAS_EVAL_PROMPT_DETECTOR_BASE_URL"],
        "api_key": os.environ["RAS_EVAL_PROMPT_DETECTOR_API_KEY"],
        "model": os.environ["RAS_EVAL_PROMPT_DETECTOR_MODEL"],
        "template": template,
        "timeout": float(os.environ["RAS_EVAL_PROMPT_DETECTOR_TIMEOUT"]),
    }
    return defense_note, detect_injection, config


def _information_flow_config(path: Path) -> dict:
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ValueError(f"information-flow config read failed: {type(error).__name__}") from None
    if not isinstance(config, dict) or not isinstance(config.get("tool_map"), dict):
        raise ValueError("information-flow config is missing the tool_map object")
    if not all(isinstance(key, str) and isinstance(value, str) for key, value in config["tool_map"].items()):
        raise ValueError("information-flow tool_map must map real provider names to tool names")
    return config


def build_server() -> FastMCP:
    # Prefer a file path over the inline env var: apptainer forwards env vars
    # through a generated shell script that shreds JSON quotes/backslashes.
    sample_path = os.environ.get("RAS_EVAL_SAMPLE_PATH")
    if sample_path:
        with open(sample_path, encoding="utf-8") as file:
            sample = json.load(file)
    else:
        sample = json.loads(os.environ["RAS_EVAL_SAMPLE_JSON"])
    meta = sample["meta"]

    reloader = None
    information_flow_dir = os.environ.get("INFORMATION_FLOW_DIR")
    if information_flow_dir:
        from src.defense.information_flow.mcp_reload import ReloadingToolRegistry

        config_path = Path(information_flow_dir) / "config.json"
        flow_config = _information_flow_config(config_path)
        toolkit_root = Path(flow_config.get("toolkit_root") or "/app/src/toolkits/ras_eval")
        dependency_roots = [Path(path) for path in flow_config.get("toolkit_dependency_roots", [])]
        manifest = toolkit_root / ".information_flow_mounts.json"
        if manifest.is_file():
            dependency_roots.extend(Path(path) for path in json.loads(manifest.read_text(encoding="utf-8")))
        reloader = ReloadingToolRegistry(toolkit_root, meta["toolkits"], dependency_roots, meta["tools"])
        registry = reloader.registry
        flow_updates = {
            "toolkit_root": str(toolkit_root),
            "toolkit_dependency_roots": sorted({str(path) for path in dependency_roots}),
        }
        flow_updates["toolkits"] = {
            toolkit: str(Path(inspect.getfile(import_toolkit(toolkit))).resolve()) for toolkit in meta["toolkits"]
        }
        flow_updates["tool_sources"] = {
            name: str(Path(inspect.getfile(function)).resolve()) for name, function in registry.items()
            if name in meta["tools"]
        }
    else:
        registry = build_tool_registry(meta["toolkits"])
    # Replay environment setup first (mutates on-disk state under ./environment).
    # A failed entry only means the precondition could not be (re)established --
    # report it instead of killing the server, which would leave opencode with
    # zero tools and produce a misleading empty trajectory.
    replay_warnings = load_environment(meta["environment"], registry)
    if replay_warnings:
        for warning in replay_warnings:
            print(
                f"[ras-eval-next-mcp] environment replay warning: {warning['tool']}: {warning['error']}",
                file=sys.stderr,
                flush=True,
            )
        report_path = os.environ.get("RAS_EVAL_ENV_REPLAY_REPORT")
        if report_path:
            with open(report_path, "w", encoding="utf-8") as file:
                json.dump(replay_warnings, file, ensure_ascii=False, indent=2)

    toma_returns: dict[str, Any] = {}
    tpa_contents: dict[str, str] = {}
    for attack in _attack_entries(meta.get("attack")):
        if attack.get("mode") == "tool_output":
            toma_returns[attack.get("tool")] = attack.get("return")
        elif attack.get("mode") == "tpa":
            tpa_contents[attack.get("tool")] = str(attack.get("content") or "")

    server = FastMCP(name="ras_eval_next")
    detector = _description_detector()
    schema_descriptions = (
        tool_descriptions_from_schema(meta["toolkits"], meta["tools"])
        if meta.get("attack_type") == "cia-tool"
        else {}
    )
    registered_descriptions: dict[str, str] = {}
    for tool_name in meta["tools"]:
        function = registry[tool_name]
        description = schema_descriptions.get(tool_name) or inspect.getdoc(function) or tool_name
        if tool_name in tpa_contents:
            description = tpa_contents[tool_name] + description
        if detector is not None:
            defense_note, detect_injection, detector_config = detector
            verdict = detect_injection(tool_name=tool_name, content=description, **detector_config)
            if verdict and verdict["injected"] and verdict["injection"]:
                description = f"{description}\n\n{defense_note(verdict['injection'])}"
        server.add_tool(
            _wrap_tool(
                function,
                toma_returns.get(tool_name),
                cleanup_hint=meta.get("attack_type") == "cia-tool",
                reloader=reloader,
                tool_name=tool_name,
            ),
            name=tool_name,
            description=description,
            structured_output=False,
        )
        registered_descriptions[tool_name] = description
    if information_flow_dir:
        flow_config = _information_flow_config(config_path)
        flow_config.update(flow_updates)
        flow_config["tool_descriptions"] = {
            provider: registered_descriptions[name]
            for provider, name in flow_config["tool_map"].items() if name in registered_descriptions
        }
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=config_path.parent, delete=False) as handle:
                temporary = Path(handle.name)
                json.dump(flow_config, handle, ensure_ascii=False, indent=2)
                handle.flush()
                os.fsync(handle.fileno())
            temporary.replace(config_path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
    return server


def main() -> None:
    try:
        server = build_server()
    except Exception:
        print(
            "[ras-eval-next-mcp] failed to build server, stopping:\n"
            + traceback.format_exc(),
            file=sys.stderr,
            flush=True,
        )
        os._exit(1)
    # Preflight mode: build the server (surfacing any startup error) and exit
    # without serving, so the harness can fail fast instead of letting opencode
    # silently fall back to builtin tools.
    if "--check" in sys.argv[1:]:
        print("[ras-eval-next-mcp] ok", file=sys.stderr, flush=True)
        return
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
