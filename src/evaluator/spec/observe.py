from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
NUXMV_LINUX_DIR = REPO_ROOT / "bin" / "nuXmv-2.2.0-linux64"
NUXMV_SANDBOX_BIN = "/opt/nuXmv/usr/local/bin/nuXmv-portable.sh"
OBSERVE_SCRIPT = "/app/src/evaluator/spec/observe.py"
WORKSPACE = "/workspace"
SCRATCH = "/scratch"


# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
def sandbox_mount(env_dir: Path | str) -> tuple[Path, str]:
    env_dir = Path(env_dir).absolute()
    if env_dir.name == "environment":
        return env_dir.parent, f"{WORKSPACE}/environment"
    return env_dir, WORKSPACE


def verify_in_sandbox(
    response: list[dict[str, Any]],
    specs: list[str],
    env_dir: Path | str,
    spec,
    timeout: int = 300,
    nuxmv_timeout: int = 60,
) -> dict[str, Any]:
    if not specs:
        return {"results": [], "model": "", "output": ""}
    from src.runner.sandbox import build_command

    sandbox_root, container_env_dir = sandbox_mount(env_dir)
    scratch = sandbox_root.parent / f".verify_{sandbox_root.name}"
    shutil.rmtree(scratch, ignore_errors=True)
    scratch.mkdir(parents=True, exist_ok=True)
    payload = {
        "response": response,
        "specs": specs,
        "env_dir": container_env_dir,
        "nuxmv_timeout": nuxmv_timeout,
    }
    (scratch / "request.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    binds = [
        (str(sandbox_root), WORKSPACE, True),
        (str(scratch.absolute()), SCRATCH, False),
        (str((REPO_ROOT / "src").absolute()), "/app/src", True),
        (str(NUXMV_LINUX_DIR.absolute()), "/opt/nuXmv", True),
    ]
    root_dir = sandbox_root / "_root_files"
    if root_dir.exists():
        for item in root_dir.iterdir():
            binds.append((str(item.absolute()), f"/{item.name}", True))

    container = f"specagent-verify-{os.getpid()}-{sandbox_root.name}"
    command = build_command(
        spec,
        binds,
        {"PYTHONPATH": "/app"},
        [
            "python",
            OBSERVE_SCRIPT,
            "verify",
            f"{SCRATCH}/request.json",
            f"{SCRATCH}/verification.json",
        ],
        writable_home=scratch / "home",
        name=container,
    )
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            input="",
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(
                f"verification container exit code {completed.returncode}：{completed.stderr.strip()[-1000:]}"
            )
        results_path = scratch / "verification.json"
        if not results_path.exists():
            raise RuntimeError("verification container did not produce nuXmv results")
        return json.loads(results_path.read_text(encoding="utf-8"))
    except subprocess.TimeoutExpired:
        if spec.sandbox == "docker":
            subprocess.run(
                ["docker", "kill", container],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        raise
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def main() -> None:
    if len(sys.argv) != 4 or sys.argv[1] != "verify":
        raise SystemExit("usage: observe.py verify <request.json> <verification.json>")
    payload = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
    from src.evaluator.spec.verifier import verify_task

    outcome = verify_task(
        payload["response"],
        payload["specs"],
        payload["env_dir"],
        NUXMV_SANDBOX_BIN,
        timeout=payload.get("nuxmv_timeout", 60),
    )
    Path(sys.argv[3]).write_text(json.dumps(outcome, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
