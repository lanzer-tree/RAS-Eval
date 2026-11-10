from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
ENV_SEED = REPO_ROOT / "data" / "ras_eval" / "environment"
NUXMV_LINUX_DIR = REPO_ROOT / "bin" / "nuXmv-2.2.0-linux64"
NUXMV_SANDBOX_BIN = "/opt/nuXmv/usr/local/bin/nuXmv-portable.sh"
REPLAY_SCRIPT = "/app/src/evaluator/spec/replay.py"
WORKSPACE = "/workspace"
SCRATCH = "/scratch"
PAYLOAD = f"{SCRATCH}/replay.json"
VERIFICATION = f"{SCRATCH}/verification.json"


def tool_calls_of(response: list[dict[str, Any]]) -> list[tuple[str, dict[str, Any]]]:
    calls = []
    for message in response:
        for call in message.get("tool_calls") or []:
            function = call["function"]
            try:
                arguments = json.loads(function["arguments"] or "{}")
            except json.JSONDecodeError:
                continue
            if isinstance(arguments, dict):
                calls.append((function["name"], arguments))
    return calls


# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
def replay_dir_for(input_path: Path, traceid: int) -> Path:
    input_path = Path(input_path).absolute()
    return input_path.parent / f"{input_path.stem}_replay" / f"TASK-{traceid}"


def scratch_dir_for(work_dir: Path) -> Path:
    work_dir = Path(work_dir)
    return work_dir.parent / f".scratch_{work_dir.name}"


def env_dir_for_sample(sample: dict[str, Any], work_dir: Path) -> Path:
    work_dir = Path(work_dir)
    return work_dir if sample["source"] == "skill_inject" else work_dir / "environment"


def container_env_dir(source: str) -> str:
    return WORKSPACE if source == "skill_inject" else f"{WORKSPACE}/environment"


def rebuild(
    sample: dict[str, Any],
    response: list[dict[str, Any]],
    work_dir: Path,
    spec,
    timeout: int,
    specs: list[str],
    nuxmv_timeout: int = 60,
    dataset_path: Path | None = None,
) -> tuple[Path, dict[str, Any]]:
    from src.adapter.skill_inject.annotate import build_environment
    from src.runner.sandbox import build_command

    work_dir = Path(work_dir)
    env_dir = env_dir_for_sample(sample, work_dir)
    meta = sample["meta"]
    payload: dict[str, Any] = {
        "source": sample["source"],
        "calls": tool_calls_of(response),
        "response": response,
        "specs": specs,
        "nuxmv_timeout": nuxmv_timeout,
        "env_dir": container_env_dir(sample["source"]),
    }
    toolkit_root: Path | None = None
    if sample["source"] == "ras-eval-next":
        from src.adapter.ras_eval_next.common import materialize_toolkit_root

        shutil.copytree(ENV_SEED, env_dir)
        payload["toolkits"] = meta["toolkits"]
        payload["environment"] = meta["environment"]
        toolkit_root = materialize_toolkit_root(sample, dataset_path, work_dir)
    elif sample["source"] == "agentdojo":
        env_dir.mkdir()
        payload["suite_name"] = meta["suite_name"]
        payload["environment"] = meta["environment"]
    elif sample["source"] == "skill_inject":
        build_environment(sample, env_dir)
    else:
        raise NotImplementedError(f"environment rebuild does not support source={sample['source']}")

    scratch_dir = scratch_dir_for(work_dir)
    shutil.rmtree(scratch_dir, ignore_errors=True)
    scratch_dir.mkdir(parents=True, exist_ok=True)
    (scratch_dir / "replay.json").write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    binds = [
        (str(work_dir.absolute()), WORKSPACE, False),
        (str(scratch_dir.absolute()), SCRATCH, False),
        (str((REPO_ROOT / "src").absolute()), "/app/src", True),
        (str(NUXMV_LINUX_DIR.absolute()), "/opt/nuXmv", True),
    ]
    if toolkit_root is not None:
        binds.append((str(toolkit_root.absolute()), "/app/src/toolkits/ras_eval", True))
    if sample["source"] == "skill_inject":
        root_dir = work_dir / "_root_files"
        if root_dir.exists():
            for item in root_dir.iterdir():
                binds.append((str(item.absolute()), f"/{item.name}", True))

    container = f"specagent-replay-{os.getpid()}-{work_dir.name}"
    command = build_command(
        spec,
        binds,
        {"PYTHONPATH": "/app"},
        ["python", REPLAY_SCRIPT, PAYLOAD],
        writable_home=scratch_dir / "home",
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
    except subprocess.TimeoutExpired:
        if spec.sandbox == "docker":
            subprocess.run(["docker", "kill", container], stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, check=False)
        raise
    if completed.returncode != 0:
        raise RuntimeError(f"replay container exit code {completed.returncode}：{completed.stderr.strip()[-1000:]}")
    results_path = scratch_dir / "verification.json"
    if not results_path.exists():
        raise RuntimeError("replay container did not produce nuXmv verification results")
    return env_dir, json.loads(results_path.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- #
# --------------------------------------------------------------------------- #
def _replay_agentdojo(payload: dict[str, Any]) -> None:
    from src.adapter.agentdojo.agentdojo_environment import build_environment, dump_environment, suite_tools

    suite_name = payload["suite_name"]
    environment = build_environment(suite_name, payload["environment"])
    tools = {function.__name__: function for function in suite_tools(suite_name)}
    for name, arguments in payload["calls"]:
        if name not in tools:
            continue
        try:
            tools[name](environment, **arguments)
        except Exception:
            pass
    dump_environment(environment, Path("environment"))


def _replay_write(name: str, arguments: dict[str, Any]) -> None:
    path = Path(arguments.get("filePath") or arguments["file_path"])
    if name == "write":
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(arguments["content"], encoding="utf-8")
        return
    count = -1 if arguments.get("replaceAll") or arguments.get("replace_all") else 1
    path.write_text(
        path.read_text(encoding="utf-8").replace(arguments["oldString"], arguments["newString"], count),
        encoding="utf-8",
    )


def _replay_bash(arguments: dict[str, Any]) -> None:
    timeout = arguments.get("timeout")
    workdir = arguments.get("workdir")
    subprocess.run(
        arguments["command"],
        shell=True,
        executable="/bin/bash",
        cwd=workdir if workdir and os.path.isdir(workdir) else None,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=timeout / 1000 if timeout else 120,
    )


def _replay_ras_eval_next(payload: dict[str, Any]) -> None:
    from src.adapter.ras_eval_next.common import build_tool_registry, load_environment

    registry = build_tool_registry(payload["toolkits"])
    load_environment(payload["environment"], registry)
    for name, arguments in payload["calls"]:
        try:
            if name in registry:
                registry[name](**arguments)
            elif name in ("write", "edit"):
                _replay_write(name, arguments)
            elif name == "bash":
                _replay_bash(arguments)
        except Exception:
            pass


def _replay_skill_inject(payload: dict[str, Any]) -> None:
    logger = os.path.join(WORKSPACE, ".bash_command_logger.sh")
    if os.path.exists(logger):
        os.environ["BASH_ENV"] = logger
    for name, arguments in payload["calls"]:
        try:
            if name in ("write", "edit"):
                _replay_write(name, arguments)
            elif name == "bash":
                _replay_bash(arguments)
        except Exception:
            pass


def main() -> None:
    payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    if payload["source"] == "agentdojo":
        _replay_agentdojo(payload)
    elif payload["source"] == "skill_inject":
        _replay_skill_inject(payload)
    else:
        _replay_ras_eval_next(payload)

    from src.evaluator.spec.verifier import verify_task

    outcome = verify_task(
        payload["response"],
        payload["specs"],
        payload["env_dir"],
        NUXMV_SANDBOX_BIN,
        timeout=payload.get("nuxmv_timeout", 60),
    )
    Path(VERIFICATION).write_text(json.dumps(outcome, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
