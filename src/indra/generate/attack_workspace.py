"""Workspace setup for LTL-guided attack generation."""
from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from src.indra.annotator.workspace import (
    ENVIRONMENT_SRC,
    NATIVE_TOOLS_DOC_SRC,
    SPEC_DOC_SRC,
    TOOLKITS_SRC,
    VERIFIER_SRC,
    VERIFY_CLI_SRC,
)

_SAFE_BASH_DENY = re.compile(
    r"(\.\.|\$HOME|~|\bsudo\b|\brm\b|\bmv\b|\bcurl\b|\bwget\b|\bpython\b|\bperl\b|\bruby\b|\bnode\b|[\s'\"]/[A-Za-z0-9_./-]*)"
)
REPO_ROOT = Path(__file__).resolve().parents[3]
SKILL_INJECT_SRC = REPO_ROOT / "data" / "skill_inject"


def ensure_attack_generate_workspace(output_dir: Path, input_path: Path) -> None:
    """Initialize an isolated attack-generation workspace under ``output_dir``."""
    output_dir = Path(output_dir)
    toolkits_dst = output_dir / "toolkits"
    environment_dst = output_dir / "environment"
    verifier_dst = output_dir / "verifier"
    dataset_dst = output_dir / "dataset"

    if not toolkits_dst.exists():
        shutil.copytree(TOOLKITS_SRC, toolkits_dst)
    if not environment_dst.exists():
        shutil.copytree(ENVIRONMENT_SRC, environment_dst)
    if not verifier_dst.exists():
        verifier_dst.mkdir(parents=True)
        shutil.copy(VERIFIER_SRC, verifier_dst / "verifier.py")
        shutil.copy(VERIFY_CLI_SRC, verifier_dst / "verify.py")
        shutil.copy(SPEC_DOC_SRC, verifier_dst / "agent_ltl_specification.md")
    if not (verifier_dst / "opencode_native_tools.md").exists():
        shutil.copy(NATIVE_TOOLS_DOC_SRC, verifier_dst / "opencode_native_tools.md")

    dataset_dst.mkdir(parents=True, exist_ok=True)
    (output_dir / "traces").mkdir(parents=True, exist_ok=True)
    (output_dir / "sandboxes").mkdir(parents=True, exist_ok=True)

    base_path = dataset_dst / "base.jsonl"
    if not base_path.exists():
        shutil.copyfile(input_path, base_path)


def ensure_cia_generate_workspace(output_dir: Path, input_path: Path) -> None:
    """Initialize an isolated CIA skill-inject generation workspace.

    The generation agent edits real skill directories, so the zip-backed asset
    trees (see ``src.adapter.skill_inject.archive``) are materialised here once.
    """
    from src.adapter.skill_inject import archive

    output_dir = Path(output_dir)
    dataset_dst = output_dir / "dataset"
    skill_root = output_dir / "skill_inject"
    skill_root.mkdir(parents=True, exist_ok=True)
    for name in archive.TREES:
        dst = skill_root / name
        if not dst.exists():
            archive.copy_tree(SKILL_INJECT_SRC, name, dst)
    dataset_dst.mkdir(parents=True, exist_ok=True)
    (output_dir / "traces").mkdir(parents=True, exist_ok=True)
    (output_dir / "sandboxes").mkdir(parents=True, exist_ok=True)
    base_path = dataset_dst / "base.jsonl"
    if not base_path.exists():
        shutil.copyfile(input_path, base_path)



def _safe_environment_path(env_root: Path, raw_path: str) -> Path:
    if not raw_path or Path(raw_path).is_absolute():
        raise ValueError(f"extra_environment path must be relative: {raw_path!r}")
    path = (env_root / raw_path).resolve()
    env_root = env_root.resolve()
    if path != env_root and env_root not in path.parents:
        raise ValueError(f"extra_environment path escapes environment: {raw_path!r}")
    return path


def _ensure_safe_bash(command: str) -> None:
    if not command.strip():
        raise ValueError("native bash command is empty")
    if _SAFE_BASH_DENY.search(command):
        raise ValueError("native bash command contains unsafe path or command token")


def apply_extra_environment(sandbox_dir: Path, entries: Any) -> None:
    """Apply synthetic native-tool setup to ``sandbox_dir/environment``.

    Supported entries:
    - {"native": "write", "path": "relative/file", "content": "..."}
    - {"native": "bash", "command": "safe relative command"}
    """
    if not entries:
        return
    if not isinstance(entries, list):
        raise ValueError("extra_environment must be a list")

    env_root = Path(sandbox_dir) / "environment"
    env_root.mkdir(parents=True, exist_ok=True)
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("every extra_environment entry must be an object")
        native = entry.get("native")
        if native == "write":
            path = _safe_environment_path(env_root, str(entry.get("path") or ""))
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(str(entry.get("content") or ""), encoding="utf-8")
        elif native == "bash":
            command = str(entry.get("command") or "")
            _ensure_safe_bash(command)
            completed = subprocess.run(
                ["bash", "-lc", command],
                cwd=env_root,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                check=False,
            )
            if completed.returncode != 0:
                raise RuntimeError(f"native bash setup failed: {completed.stderr.strip()[-500:]}")
        else:
            raise ValueError(f"unsupported native setup entry: {native!r}")
