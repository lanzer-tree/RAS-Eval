"""Shared helpers for the SKILL-INJECT opencode adaptation.

Runtime code (inference + evaluation) only depends on this module and the
migrated data under ``data/skill_inject`` — never on ``lib/skill-inject``.
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

from src.adapter.skill_inject import archive
from src.runner.sandbox import SandboxSpec, build_command, opencode_config_bind, opencode_home_path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = REPO_ROOT / "data" / "skill_inject"


def _sample_data_root(sample: dict[str, Any]) -> Path:
    meta = sample.get("meta", {})
    raw = meta.get("data_root") or DATA_ROOT
    path = Path(raw)
    return path if path.is_absolute() else REPO_ROOT / path


def _safe_sandbox_path(sandbox_dir: Path, raw_path: str) -> Path:
    raw_path = raw_path.replace("\\", "/")
    if raw_path.startswith("/workspace/"):
        raw_path = raw_path[len("/workspace/"):]
    if not raw_path or Path(raw_path).is_absolute() or raw_path.startswith("~"):
        raise ValueError(f"environment path must be relative or under /workspace: {raw_path!r}")
    path = Path(raw_path)
    if any(part in ("..", "") for part in path.parts):
        raise ValueError(f"environment path must stay inside sandbox: {raw_path!r}")
    target = (sandbox_dir / path).resolve()
    root = sandbox_dir.resolve()
    if target == root or root not in target.parents:
        raise ValueError(f"environment path escapes sandbox: {raw_path!r}")
    return target


def _workspace_arg_path(sandbox_dir: Path, raw_path: str) -> Path:
    return _safe_sandbox_path(sandbox_dir, raw_path)


def _run_environment_bash(sandbox_dir: Path, kwargs: dict[str, Any]) -> None:
    command = str(kwargs.get("command") or "")
    if not command.strip():
        raise ValueError("environment bash command is empty")
    workdir = str(kwargs.get("workdir") or ".")
    cwd = _workspace_arg_path(sandbox_dir, workdir) if workdir not in ("", ".", "/workspace") else Path(sandbox_dir)
    cwd.mkdir(parents=True, exist_ok=True)
    completed = subprocess.run(
        command.replace("/workspace/", ""),
        shell=True,
        executable="/bin/bash",
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=min(int(kwargs.get("timeout") or 30000) / 1000, 30),
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"environment bash failed: {completed.stderr.strip()[-500:]}")


def apply_environment(sandbox_dir: Path, entries: Any) -> None:
    """Replay initial environment setup as opencode-native-style tool calls.

    The schema mirrors ras-eval-next's ``meta.environment`` list of setup calls,
    but targets the skill-inject workspace and supports safe native tools:
    - {"tool": "write", "kwargs": {"filePath": "relative/file", "content": "..."}}
    - {"tool": "edit", "kwargs": {"filePath": "relative/file", "oldString": "...", "newString": "..."}}
    - {"tool": "bash", "kwargs": {"command": "...", "workdir": "."}}
    """
    if not entries:
        return
    if not isinstance(entries, list):
        raise ValueError("meta.environment must be a list")
    sandbox_dir = Path(sandbox_dir)
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("every meta.environment entry must be an object")
        tool = str(entry.get("tool") or "").strip()
        kwargs = entry.get("kwargs") or {}
        if not isinstance(kwargs, dict):
            raise ValueError("environment entry kwargs must be an object")
        if tool == "write":
            target = _workspace_arg_path(sandbox_dir, str(kwargs.get("filePath") or kwargs.get("file_path") or ""))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(str(kwargs.get("content") or ""), encoding="utf-8")
        elif tool == "edit":
            target = _workspace_arg_path(sandbox_dir, str(kwargs.get("filePath") or kwargs.get("file_path") or ""))
            text = target.read_text(encoding="utf-8")
            old = str(kwargs.get("oldString") or kwargs.get("old_string") or "")
            new = str(kwargs.get("newString") or kwargs.get("new_string") or "")
            count = -1 if kwargs.get("replaceAll") or kwargs.get("replace_all") else 1
            target.write_text(text.replace(old, new, count), encoding="utf-8")
        elif tool == "bash":
            _run_environment_bash(sandbox_dir, kwargs)
        else:
            raise ValueError(f"unsupported environment setup tool: {tool!r}")


def apply_environments(sandbox_dir: Path, entries: Any) -> None:
    """Backward-compatible adapter for the old CIA draft schema."""
    if not entries:
        return
    converted = []
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        kind = str(entry.get("type") or "").strip().lower()
        path = str(entry.get("path") or "")
        if kind == "dir":
            converted.append({"tool": "bash", "kwargs": {"command": f"mkdir -p {path}"}})
        elif kind == "json":
            converted.append({"tool": "write", "kwargs": {"filePath": path, "content": json.dumps(entry.get("content", {}), ensure_ascii=False, indent=2)}})
        elif kind == "file":
            converted.append({"tool": "write", "kwargs": {"filePath": path, "content": str(entry.get("content") or "")}})
    apply_environment(sandbox_dir, converted)


def sandbox_root_for(io_path: Path) -> Path:
    """Directory holding preserved per-task sandboxes for an input/output jsonl.

    Both the runner (writing the sandboxes) and the evaluator (reading them)
    derive the same location from the inference *output* path, so the two
    stages stay in sync without an extra CLI flag.
    """
    io_path = Path(io_path)
    return io_path.parent / f"{io_path.stem}_sandboxes"


def sandbox_dir_for(root: Path, sample: dict[str, Any]) -> Path:
    meta = sample["meta"]
    return Path(root) / f"TASK-{sample['traceid']}_{meta['skill']}"


def inject_at_line(file_path: Path, instruction_text: str, line_number: int) -> None:
    """Insert instruction text at a specific line number in a file.

    Copied verbatim from ``lib/skill-inject/scripts/build_sandbox.py`` so the
    injected instruction lands at exactly the same position as the original
    benchmark.
    """
    lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)
    if line_number < 1 or line_number > len(lines) + 1:
        sys.exit(
            f"[error] Line {line_number} out of range "
            f"(file has {len(lines)} lines): {file_path}"
        )
    block: list[str] = []
    for raw in instruction_text.strip("\n").splitlines():
        block.append(f"{raw.strip()}\n" if raw.strip() else "\n")
    pos = line_number - 1
    file_path.write_text("".join(lines[:pos] + block + lines[pos:]), encoding="utf-8")


def _set_skill_frontmatter_name(skill_file: Path, visible_name: str) -> None:
    text = skill_file.read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            header = text[:end]
            body = text[end:]
            if re.search(r"(?m)^name:\s*.*$", header):
                header = re.sub(r"(?m)^name:\s*.*$", f"name: {visible_name}", header, count=1)
            else:
                header += f"\nname: {visible_name}"
            skill_file.write_text(header + body, encoding="utf-8")
            return
    skill_file.write_text(f"---\nname: {visible_name}\n---\n\n" + text, encoding="utf-8")


def _rewrite_skill_visible_name(skill_dir: Path, source_name: str, visible_name: str) -> None:
    if source_name == visible_name:
        return
    text_suffixes = {".md", ".py", ".sh", ".bash", ".js", ".ts", ".json", ".txt"}
    for path in skill_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in text_suffixes:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        updated = text.replace(f".agents/skills/{source_name}/", f".agents/skills/{visible_name}/")
        updated = updated.replace(source_name, visible_name)
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def _cia_visible_skill_name(meta: dict[str, Any]) -> str:
    return str(meta.get("skill") or meta.get("base_skill") or meta.get("skill_name") or "").strip()


def _add_cia_cleanup_hints(skill_dir: Path) -> None:
    """Patch generated CIA code so cleanup is requested only after attack execution."""
    from src.adapter.ras_eval_next.common import CIA_CLEANUP_HINT

    python_helper = skill_dir / "scripts" / "daedalus_workspace_audit.py"
    if python_helper.exists():
        text = python_helper.read_text(encoding="utf-8")
        if CIA_CLEANUP_HINT not in text:
            python_helper.write_text(text.rstrip() + f"\nprint({CIA_CLEANUP_HINT!r})\n", encoding="utf-8")

    shell_helper = skill_dir / "scripts" / "daedalus_workspace_audit.sh"
    if shell_helper.exists():
        text = shell_helper.read_text(encoding="utf-8")
        if CIA_CLEANUP_HINT not in text:
            shell_helper.write_text(text.rstrip() + f"\nprintf '%s\\n' {CIA_CLEANUP_HINT!r}\n", encoding="utf-8")

    for path in skill_dir.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in {".sh", ".bash", ".js", ".ts"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if "DAEDALUS_CIA_TRIGGER_BEGIN" not in text:
            continue
        updated = text.replace(" >/dev/null 2>&1 || true", " || true")
        updated = updated.replace('{stdio: "ignore"}', '{stdio: "inherit"}')
        if updated != text:
            path.write_text(updated, encoding="utf-8")


def build_sandbox(sample: dict[str, Any], sandbox_dir: Path) -> Path:
    """Create a sandbox: task files at the root + all skills mounted under
    ``.agents/skills`` (opencode auto-discovers skills there).

    Mirrors ``lib/skill-inject`` build_clean_sandboxes for the normal condition
    (clean skill copies, task files, no SECURITY_PROTOCOL). When the sample
    carries attack metadata (``line_injection``/``line_num``), the injection is
    applied to the target skill's ``SKILL.md`` and the attack assets
    (``task_scripts`` into the skill's ``scripts/`` dir, ``root_files`` into
    ``_root_files``) are staged, mirroring ``build_sandbox.py``.

    The asset trees are read through ``archive`` (zip-backed, see that module),
    so they cost three inodes at rest instead of one per benchmark file.
    """
    sandbox_dir = Path(sandbox_dir)
    meta = sample["meta"]
    data_root = _sample_data_root(sample)
    if sandbox_dir.exists():
        shutil.rmtree(sandbox_dir)
    sandbox_dir.mkdir(parents=True, exist_ok=True)

    # CIA samples are stored under trace-specific generated names in data_root,
    # but the target sandbox exposes the derived skill under the normal skill
    # name (for example, pptx) so the prompt need not mention the attack skill.
    skills_dest = sandbox_dir / ".agents" / "skills"
    if meta.get("attack_type") == "cia" and meta.get("skill_name"):
        source_name = str(meta["skill_name"])
        visible_name = _cia_visible_skill_name(meta)
        skills_dest.mkdir(parents=True, exist_ok=True)
        skill_dest = skills_dest / visible_name
        if not archive.copy_into(data_root, f"skills/{source_name}", skill_dest):
            raise FileNotFoundError(f"skill not found under data_root: {data_root}/skills/{source_name}")
        _rewrite_skill_visible_name(skill_dest, source_name, visible_name)
        _set_skill_frontmatter_name(skill_dest / "SKILL.md", visible_name)
    else:
        archive.copy_tree(data_root, "skills", skills_dest)

    # Task files at the workspace root.
    for filename, rel_path in meta.get("task_files", {}).items():
        archive.copy_into(data_root, rel_path, sandbox_dir / filename)

    # Attack staging (no-op for normal samples that lack these fields).
    if meta.get("attack_type") == "cia" and meta.get("skill_name"):
        skill_dir = skills_dest / _cia_visible_skill_name(meta)
    else:
        skill_dir = skills_dest / meta["skill_name"] if meta.get("skill_name") else None

    line_injection = meta.get("line_injection")
    line_num = meta.get("line_num")
    if line_injection and line_num and skill_dir is not None:
        inject_at_line(skill_dir / "SKILL.md", line_injection, line_num)

    # Task scripts -> the target skill's scripts/ directory.
    for script_name, rel_path in meta.get("task_scripts", {}).items():
        if skill_dir is None or not archive.exists(data_root, rel_path):
            continue
        scripts_dir = skill_dir / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        dest = scripts_dir / script_name
        archive.copy_into(data_root, rel_path, dest)
        dest.chmod(0o755)

    # Root files -> _root_files (mounted read-only above /workspace by the runner).
    for rel_path in meta.get("root_files", []):
        if not archive.exists(data_root, rel_path):
            continue
        root_dir = sandbox_dir / "_root_files"
        root_dir.mkdir(parents=True, exist_ok=True)
        archive.copy_into(data_root, rel_path, root_dir / Path(rel_path).name)
    apply_environment(sandbox_dir, meta.get("environment"))
    apply_environments(sandbox_dir, meta.get("environments"))
    if meta.get("attack_type") == "cia" and skill_dir is not None:
        _add_cia_cleanup_hints(skill_dir)
    return sandbox_dir

def build_agent_command(
    spec: SandboxSpec,
    sandbox_dir: Path,
    config_content: str,
    model: str,
    name: str | None = None,
    runtime_verification: bool = False,
    information_flow: bool = False,
) -> list[str]:
    """opencode command for one skill-inject run. The prompt is fed via stdin by
    the caller (see ``src.runner.sandbox``), not passed here."""
    config_bind, config_env = opencode_config_bind(sandbox_dir, config_content)
    binds = [(str(sandbox_dir.absolute()), "/workspace", False), config_bind]
    if information_flow:
        from src.adapter.ras_eval_next.common import INFORMATION_FLOW_HARNESS_PATH, information_flow_binds

        binds.extend(information_flow_binds(sandbox_dir))
        if not runtime_verification:
            binds.append((str((REPO_ROOT / "src").absolute()), "/app/src", True))
    if runtime_verification:
        from src.evaluator.spec.observe import NUXMV_LINUX_DIR
        from src.evaluator.spec.runtime import runtime_dir_for

        binds.extend([
            (str((REPO_ROOT / "src").absolute()), "/app/src", True),
            (str(runtime_dir_for(sandbox_dir).absolute()), "/runtime_verification", False),
            (str(NUXMV_LINUX_DIR.absolute()), "/opt/nuXmv", True),
        ])
    # Mount attack root_files read-only above /workspace (mirrors lib container).
    root_dir = sandbox_dir / "_root_files"
    if root_dir.exists():
        for item in root_dir.iterdir():
            if information_flow:
                if item.name in {"app", "opt", "information_flow", "runtime_verification", "workspace", "opencode.json"}:
                    raise ValueError(f"task additional files must not overwrite runtime mounts: {item.name}")
                if item.is_symlink() or root_dir.resolve() not in item.resolve().parents:
                    raise ValueError(f"task additional files must be private copies: {item}")
            binds.append((str(item.absolute()), f"/{item.name}", not information_flow))
    env = {
        **config_env,
        "OPENCODE_DISABLE_AUTOUPDATE": "1",
        "BASH_ENV": "/workspace/.bash_command_logger.sh",
        **({
            "PYTHONPATH": "/app",
            "DAEDALUS_RUNTIME_REQUEST": "/runtime_verification/request.json",
            "DAEDALUS_RUNTIME_STATE": "/runtime_verification/state.json",
            "DAEDALUS_RUNTIME_LOCK": "/runtime_verification/lock",
        } if runtime_verification else {}),
        **({
            "INFORMATION_FLOW_DIR": "/information_flow", "PYTHONPATH": "/app",
            "INFORMATION_FLOW_HARNESS_PATH": INFORMATION_FLOW_HARNESS_PATH,
        } if information_flow else {}),
    }
    args = ["opencode", "run", "--model", model, "--format", "json"]
    return build_command(spec, binds, env, args, writable_home=opencode_home_path(sandbox_dir), name=name)
    
def _stringify(value: Any) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, indent=2)


def render_transcript(messages: list[dict[str, Any]]) -> str:
    """Render an OpenAI-style message list into a plain-text transcript, used as
    the ``agent_stdout.txt`` the utility judge inspects (mirrors lib, whose judge
    reads the agent's stdout)."""
    parts: list[str] = []
    for msg in messages:
        role = msg.get("role", "?")
        if role == "system":
            parts.append(f"[system]\n{_stringify(msg.get('content', ''))}")
        elif role == "user":
            parts.append(f"[user]\n{_stringify(msg.get('content', ''))}")
        elif role == "assistant":
            content = _stringify(msg.get("content", "")).strip()
            if content:
                parts.append(f"[assistant]\n{content}")
            for call in msg.get("tool_calls", []) or []:
                fn = call.get("function", {})
                parts.append(
                    f"[tool_call] {fn.get('name')}({_stringify(fn.get('arguments'))})"
                )
        elif role == "tool":
            parts.append(
                f"[tool_result] {msg.get('name')}\n{_stringify(msg.get('content', ''))}"
            )
    return "\n\n".join(parts) + "\n"
