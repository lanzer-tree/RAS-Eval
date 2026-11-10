from __future__ import annotations

import inspect
import json
import os
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, get_args, get_origin, Union
from types import UnionType

from src.adapter.ras_eval_next import common
from src.toolkits.ras_eval.computer_toolkit.function import computer_toolkit


NATIVE_TOOL_ALIASES: dict[str, dict[str, str]] = {
    "bash": {"command": "command", "timeout": "timeout"},
    "read": {"filePath": "file_path", "path": "file_path", "file_path": "file_path", "offset": "offset", "limit": "limit"},
    "write": {"filePath": "file_path", "path": "file_path", "file_path": "file_path", "content": "content"},
    "edit": {
        "filePath": "file_path",
        "path": "file_path",
        "file_path": "file_path",
        "oldString": "old_string",
        "newString": "new_string",
        "replaceAll": "replace_all",
        "old_string": "old_string",
        "new_string": "new_string",
        "replace_all": "replace_all",
    },
    "grep": {"pattern": "pattern", "path": "path", "glob": "glob", "include": "include"},
    "glob": {"pattern": "pattern", "path": "path"},
    "webfetch": {"url": "url", "timeout": "timeout", "max_chars": "max_chars"},
    "todowrite": {"todos": "todos"},
}

NATIVE_TOOL_FUNCTIONS: dict[str, Callable[..., Any]] = {
    name: getattr(computer_toolkit, name) for name in NATIVE_TOOL_ALIASES
}

NATIVE_PUBLIC_PARAMETERS: dict[str, dict[str, str]] = {
    "read": {"filePath": "string", "offset": "integer", "limit": "integer"},
    "write": {"filePath": "string", "content": "string"},
    "edit": {"filePath": "string", "oldString": "string", "newString": "string", "replaceAll": "boolean"},
}

JSON_TYPE_TO_PY = {"string": str, "integer": int, "number": float, "boolean": bool, "array": list, "object": dict}


@dataclass(frozen=True)
class RuntimeTool:
    name: str
    description: str
    schema: dict[str, Any]
    function: Callable[..., Any]
    aliases: dict[str, str]
    toma_return: Any = None


def attack_entries(value: Any) -> list[dict[str, Any]]:
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


def _json_type(annotation: Any) -> str:
    if annotation is inspect.Parameter.empty:
        return "string"
    if isinstance(annotation, str):
        normalized = annotation.replace("typing.", "").strip().lower()
        if normalized in {"str", "string"}:
            return "string"
        if normalized in {"int", "integer"}:
            return "integer"
        if normalized in {"float", "number"}:
            return "number"
        if normalized in {"bool", "boolean"}:
            return "boolean"
        if normalized.startswith(("list", "tuple", "set")):
            return "array"
        if normalized.startswith("dict"):
            return "object"
        return "string"
    origin = get_origin(annotation)
    if origin is Union or origin is UnionType:
        for argument in get_args(annotation):
            if argument is not type(None):
                return _json_type(argument)
        return "string"
    if origin in (list, tuple, set):
        return "array"
    if origin is dict:
        return "object"
    return {str: "string", int: "integer", float: "number", bool: "boolean", list: "array", dict: "object"}.get(annotation, "string")


def _public_parameters(function: Callable[..., Any], aliases: dict[str, str]) -> tuple[dict[str, Any], list[str]]:
    reverse: dict[str, str] = {}
    for public, private in aliases.items():
        reverse.setdefault(private, public)
    properties: dict[str, Any] = {}
    required: list[str] = []
    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError):
        return properties, required
    for name, parameter in signature.parameters.items():
        if parameter.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        public_name = reverse.get(name, name)
        json_type = _json_type(parameter.annotation)
        properties[public_name] = {"type": json_type}
        if parameter.default is inspect.Parameter.empty:
            required.append(public_name)
    return properties, required


def _schema_for(name: str, description: str, function: Callable[..., Any], aliases: dict[str, str]) -> dict[str, Any]:
    if name in NATIVE_PUBLIC_PARAMETERS:
        properties = {
            key: {"type": value}
            for key, value in NATIVE_PUBLIC_PARAMETERS[name].items()
        }
        required = [key for key in properties if key not in {"offset", "limit", "replaceAll"}]
    else:
        properties, required = _public_parameters(function, aliases)
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        },
    }


def _scalar_coercions(function: Callable[..., Any]) -> dict[str, str]:
    coercions: dict[str, str] = {}
    try:
        signature = inspect.signature(function)
    except (TypeError, ValueError):
        return coercions
    for name, parameter in signature.parameters.items():
        json_type = _json_type(parameter.annotation)
        if json_type in {"integer", "number", "boolean"}:
            coercions[name] = json_type
    return coercions


def _coerce_scalar(value: Any, json_type: str) -> Any:
    if not isinstance(value, str):
        return value
    text = value.strip()
    if json_type == "integer":
        try:
            return int(text)
        except ValueError:
            return value
    if json_type == "number":
        try:
            return float(text)
        except ValueError:
            return value
    if json_type == "boolean":
        lowered = text.lower()
        if lowered in {"true", "1", "yes"}:
            return True
        if lowered in {"false", "0", "no"}:
            return False
    return value


def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)


class ToolTraceRecorder:
    def __init__(self, trace_path: Path, initial_messages: list[dict[str, Any]]) -> None:
        self.trace_path = Path(trace_path)
        self.trace_path.parent.mkdir(parents=True, exist_ok=True)
        self.messages: list[dict[str, Any]] = []
        self._lock = threading.Lock()
        self._file = self.trace_path.open("w", encoding="utf-8")
        for message in initial_messages:
            self.append(message)

    def append(self, message: dict[str, Any]) -> None:
        with self._lock:
            self.messages.append(message)
            self._file.write(json.dumps(message, ensure_ascii=False, default=str) + "\n")
            self._file.flush()
            os.fsync(self._file.fileno())

    def record_tool_call(self, name: str, arguments: dict[str, Any]) -> None:
        self.append({
            "role": "assistant",
            "content": "",
            "tool_calls": [{
                "type": "function",
                "function": {"name": name, "arguments": arguments},
            }],
        })

    def record_tool_result(self, name: str, content: Any) -> None:
        self.append({"role": "tool", "name": name, "content": _stringify(content)})

    def record_assistant(self, content: str) -> None:
        if content:
            self.append({"role": "assistant", "content": content})

    def close(self) -> None:
        self._file.close()


class ToolRuntime:
    def __init__(
        self,
        sample: dict[str, Any],
        trace_path: Path,
        *,
        replay_environment: bool = True,
        record_trace: bool = True,
        runtime_verification: bool = True,
    ) -> None:
        self.sample = sample
        self.meta = sample.get("meta", {})
        self.source = sample.get("source")
        self.replay_environment = replay_environment
        self.tools = self._build_tools()
        self.recorder = ToolTraceRecorder(trace_path, self._initial_messages()) if record_trace else None
        self.verifier = None
        if runtime_verification and os.environ.get("DAEDALUS_RUNTIME_REQUEST"):
            from src.evaluator.spec.runtime import RuntimeVerifier

            self.verifier = RuntimeVerifier.from_env()

    @classmethod
    def from_env(
        cls,
        *,
        replay_environment: bool = True,
        record_trace: bool = True,
        runtime_verification: bool = True,
    ) -> "ToolRuntime":
        sample_path = os.environ["RAS_EVAL_SAMPLE_PATH"]
        with open(sample_path, encoding="utf-8") as file:
            sample = json.load(file)
        workdir = Path(os.environ.get("RAS_EVAL_WORKDIR", "/workspace"))
        os.chdir(workdir)
        return cls(
            sample,
            workdir / ".daedalus_trace.jsonl",
            replay_environment=replay_environment,
            record_trace=record_trace,
            runtime_verification=runtime_verification,
        )

    def _initial_messages(self) -> list[dict[str, Any]]:
        system_parts: list[str] = []
        if self.meta.get("system_prompt"):
            system_parts.append(str(self.meta["system_prompt"]))
        if self.source == "skill_inject":
            skill_text = self._skill_instructions()
            if skill_text:
                system_parts.append("The following skill is available in this workspace. Use its instructions and scripts when helpful.\n\n" + skill_text)
        messages: list[dict[str, Any]] = []
        if system_parts:
            messages.append({"role": "system", "content": "\n\n".join(system_parts)})
        messages.append({"role": "user", "content": self.sample.get("prompt", "")})
        return messages

    def _skill_instructions(self) -> str:
        candidates = [
            self.meta.get("skill"),
            self.meta.get("base_skill"),
            self.meta.get("skill_name"),
        ]
        for candidate in candidates:
            if not candidate:
                continue
            path = Path(".agents") / "skills" / str(candidate) / "SKILL.md"
            if path.exists():
                return path.read_text(encoding="utf-8", errors="replace")
        return ""

    def _build_tools(self) -> dict[str, RuntimeTool]:
        tools: dict[str, RuntimeTool] = {}
        registry: dict[str, Callable[..., Any]] = {}
        if self.source == "ras-eval-next":
            registry = common.build_tool_registry(self.meta.get("toolkits") or [])
            if self.replay_environment:
                warnings = common.load_environment(self.meta.get("environment"), registry)
                if warnings:
                    report_path = os.environ.get("RAS_EVAL_ENV_REPLAY_REPORT")
                    if report_path:
                        Path(report_path).write_text(json.dumps(warnings, ensure_ascii=False, indent=2), encoding="utf-8")
        toma_returns: dict[str, Any] = {}
        tpa_contents: dict[str, str] = {}
        for attack in attack_entries(self.meta.get("attack")):
            if attack.get("mode") == "tool_output":
                toma_returns[str(attack.get("tool"))] = attack.get("return")
            elif attack.get("mode") == "tpa":
                tpa_contents[str(attack.get("tool"))] = str(attack.get("content") or "")
        schema_descriptions = (
            common.tool_descriptions_from_schema(self.meta.get("toolkits") or [], self.meta.get("tools") or [])
            if self.meta.get("attack_type") == "cia-tool"
            else {}
        )
        for name in self.meta.get("tools") or []:
            if name not in registry:
                continue
            function = registry[name]
            description = schema_descriptions.get(name) or inspect.getdoc(function) or name
            if name in tpa_contents:
                description = tpa_contents[name] + description
            aliases: dict[str, str] = {}
            tools[name] = RuntimeTool(
                name=name,
                description=description,
                schema=_schema_for(name, description, function, aliases),
                function=function,
                aliases=aliases,
                toma_return=toma_returns.get(name),
            )
        for name, function in NATIVE_TOOL_FUNCTIONS.items():
            if name in tools:
                continue
            description = inspect.getdoc(function) or name
            aliases = NATIVE_TOOL_ALIASES[name]
            tools[name] = RuntimeTool(
                name=name,
                description=description,
                schema=_schema_for(name, description, function, aliases),
                function=function,
                aliases=aliases,
            )
        return tools

    def openai_tools(self) -> list[dict[str, Any]]:
        return [tool.schema for tool in self.tools.values()]

    def messages_for_model(self) -> list[dict[str, Any]]:
        if self.recorder is None:
            return []
        return [dict(message) for message in self.recorder.messages]

    def callable_for(self, name: str) -> Callable[..., str]:
        tool = self.tools[name]
        parameters = tool.schema["function"]["parameters"]
        required = set(parameters.get("required") or [])
        signature_parameters = []
        annotations: dict[str, Any] = {"return": str}
        for parameter_name, spec in (parameters.get("properties") or {}).items():
            if not str(parameter_name).isidentifier():
                continue
            annotation = JSON_TYPE_TO_PY.get((spec or {}).get("type"), str)
            default = inspect.Parameter.empty if parameter_name in required else None
            signature_parameters.append(
                inspect.Parameter(
                    str(parameter_name),
                    inspect.Parameter.POSITIONAL_OR_KEYWORD,
                    default=default,
                    annotation=annotation,
                )
            )
            annotations[str(parameter_name)] = annotation

        def invoke(**kwargs: Any) -> str:
            return self.call_tool(name, kwargs)

        invoke.__name__ = name
        invoke.__doc__ = tool.description
        invoke.__annotations__ = annotations
        invoke.__signature__ = inspect.Signature(signature_parameters, return_annotation=str)
        return invoke

    def call_tool(self, name: str, arguments: dict[str, Any] | str | None) -> str:
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments) if arguments.strip() else {}
            except json.JSONDecodeError:
                arguments = {}
        if arguments is None:
            arguments = {}
        if name not in self.tools:
            public_arguments = dict(arguments)
            if self.verifier is not None:
                self.verifier.before_tool()
            if self.recorder is not None:
                self.recorder.record_tool_call(name, public_arguments)
            result = {"success": False, "description": f"unknown tool: {name}"}
            if self.recorder is not None:
                self.recorder.record_tool_result(name, result)
            if self.verifier is not None:
                self.verifier.after_tool(name, public_arguments, result)
            return _stringify(result)
        tool = self.tools[name]
        public_arguments = dict(arguments)
        if self.verifier is not None:
            self.verifier.before_tool()
        if self.recorder is not None:
            self.recorder.record_tool_call(name, public_arguments)
        kwargs = self._private_arguments(tool, public_arguments)
        result = self._invoke(tool, kwargs)
        if self.recorder is not None:
            self.recorder.record_tool_result(name, result)
        if self.verifier is not None:
            self.verifier.after_tool(name, public_arguments, result)
        return _stringify(result)

    def _private_arguments(self, tool: RuntimeTool, arguments: dict[str, Any]) -> dict[str, Any]:
        kwargs: dict[str, Any] = {}
        for key, value in arguments.items():
            kwargs[tool.aliases.get(key, key)] = value
        return kwargs

    def _invoke(self, tool: RuntimeTool, kwargs: dict[str, Any]) -> Any:
        coercions = common.string_coercions(tool.function)
        scalar_coercions = _scalar_coercions(tool.function)
        substitutions = common.default_substitutions(tool.function)
        for name, json_type in scalar_coercions.items():
            if name in kwargs:
                kwargs[name] = _coerce_scalar(kwargs[name], json_type)
        for name, mode in coercions.items():
            value = kwargs.get(name)
            if isinstance(value, str):
                kwargs[name] = common.coerce_string_argument(value, mode)
        for name, default in substitutions.items():
            if name in kwargs and kwargs[name] is None:
                kwargs[name] = default
        try:
            result = tool.function(**kwargs)
        except Exception as exc:
            result = {"success": False, "description": f"{type(exc).__name__}: {exc}"}
        if tool.toma_return is not None:
            marker = f"_DAEDALUS_TOMA_USED_{tool.name}"
            if not hasattr(self, marker):
                setattr(self, marker, True)
                result = common.inject_toma_payload(result, tool.toma_return)
        if (
            self.meta.get("attack_type") == "cia-tool"
            and tool.name in (self.meta.get("tools") or [])
        ):
            result = common.inject_cleanup_hint(result)
        return result

    def close(self) -> None:
        if self.recorder is not None:
            self.recorder.close()
