"""Build the container command that runs opencode inside a per-task sandbox.

Two backends sit behind one interface:

* ``docker``    -- ``docker run`` with ``-v``/``-e`` (hosts that have Docker).
* ``apptainer`` -- ``apptainer exec`` for hosts without Docker. On macOS
  apptainer runs inside the ``apptainer`` lima VM, so the command is prefixed
  with ``limactl shell apptainer``; on Linux the ``apptainer`` executable path
  is used directly.

Two quirks of the ``limactl shell`` / apptainer transport shape the design and
are handled here so callers stay backend-agnostic:

* The opencode prompt is fed via **stdin** (the returned command never carries
  it), so prompts with shell metacharacters survive the ``limactl shell``
  transport (which re-expands ``$`` in argv) unchanged. Callers pass the prompt
  as ``subprocess.run(..., input=prompt)``.
* The opencode config is forwarded with the ``APPTAINERENV_`` prefix rather than
  ``--env``: apptainer splits ``--env`` values on commas, which would shred the
  JSON config. ``HOME`` is set via ``--home`` because apptainer refuses to
  override ``HOME`` through the environment.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import os
import shutil
import tempfile

# (host_path, container_path, read_only)
Bind = tuple[str, str, bool]


@dataclass(frozen=True)
class SandboxSpec:
    sandbox: str                        # "docker" | "apptainer"
    image: str                          # docker image name or .sif path
    os: str                   # "mac" | "linux"
    apptainer_path: str   # apptainer executable path (Linux)


def opencode_config_path(sandbox_dir: Path) -> Path:
    """Where the opencode config for ``sandbox_dir`` is written -- a sibling of
    the sandbox (never inside it, so the skill-inject judge does not see it)."""
    return sandbox_dir.parent / f".opencode_config_{sandbox_dir.name}.json"


def mcp_sample_path(sandbox_dir: Path) -> Path:
    """Where the sample JSON handed to the in-sandbox MCP server is written -- a
    sibling of the sandbox, so the agent never sees the task definition."""
    return sandbox_dir.parent / f".mcp_sample_{sandbox_dir.name}.json"


def env_dir_for(io_path: Path, traceid: int) -> Path:
    """Per-task post-run environment snapshot next to the inference output
    (``{output_stem}_sandboxes/TASK-{traceid}/environment``). The inference side
    leaves the environment state here and the LTL evaluator's environment
    observers read it, so both sides must agree on the layout."""
    io_path = Path(io_path).absolute()
    return io_path.parent / f"{io_path.stem}_sandboxes" / f"TASK-{traceid}" / "environment"


LOCAL_STATE_ROOT_ENV = "DAEDALUS_LOCAL_STATE_ROOT"


def local_state_root() -> Path:
    """Root for per-task harness state, overridable with
    ``DAEDALUS_LOCAL_STATE_ROOT`` when the default temp dir is too small."""
    return Path(os.environ.get(LOCAL_STATE_ROOT_ENV) or tempfile.gettempdir()) / "daedalus-state"


def local_state_path(sandbox_dir: Path, prefix: str) -> Path:
    """Host dir for state that an agent harness mutates while running.

    Deliberately off the output tree: that often sits on a network filesystem
    (JuiceFS here), whose attribute cache keeps serving the pre-write mtime/ctime
    for a second or so after a write. OpenClaw fingerprints its session file on
    (dev, ino, size, mtimeNs, ctimeNs) across a lock release and reads any
    difference as another process taking the session over, so the timestamps
    settling late abort the run mid-task. Keyed by the sandbox path so concurrent
    runs over different datasets or models never collide.
    """
    sandbox_dir = Path(sandbox_dir).absolute()
    key = hashlib.sha1(str(sandbox_dir).encode("utf-8")).hexdigest()[:12]
    return local_state_root() / f"{prefix}_{sandbox_dir.name}_{key}"


def opencode_home_path(sandbox_dir: Path) -> Path:
    """Host dir bound as the writable container home for ``sandbox_dir``'s run
    (apptainer backend only). Removed by ``cleanup_sandbox_artifacts`` so long
    runs do not leak ``opencode_home_*`` dirs."""
    return local_state_path(sandbox_dir, "opencode_home")


def cleanup_sandbox_artifacts(sandbox_dir: Path) -> None:
    """Remove the per-run host artifacts tied to ``sandbox_dir``: the opencode
    config file, the MCP sample file and the apptainer writable home. Safe to
    call for docker runs (the home simply does not exist)."""
    opencode_config_path(sandbox_dir).unlink(missing_ok=True)
    mcp_sample_path(sandbox_dir).unlink(missing_ok=True)
    shutil.rmtree(opencode_home_path(sandbox_dir), ignore_errors=True)


def opencode_config_bind(sandbox_dir: Path, config_content: str) -> tuple[Bind, dict[str, str]]:
    """Write the opencode config to a file and return the bind + env that mount
    it at ``/opencode.json`` (via ``OPENCODE_CONFIG``). A file is used rather than
    an env var because apptainer shreds env values containing commas or quotes
    (it sources them from a generated shell script), and the config embeds
    arbitrary task JSON. Callers remove the file with ``opencode_config_path``."""
    path = opencode_config_path(sandbox_dir)
    path.write_text(config_content, encoding="utf-8")
    return (str(path.absolute()), "/opencode.json", True), {"OPENCODE_CONFIG": "/opencode.json"}


def build_command(
    spec: SandboxSpec,
    binds: list[Bind],
    env: dict[str, str],
    args: list[str],
    workdir: str = "/workspace",
    home: str = "/home/agent",
    writable_home: Path | None = None,
    name: str | None = None,
) -> list[str]:
    """Return the argv that launches ``args`` (e.g. ``opencode run ...``) inside
    the sandbox with the given bind mounts and environment. The prompt is NOT
    part of ``args`` -- feed it to the process via stdin.

    ``writable_home`` (apptainer only) is the host dir bound as the container
    home; pass ``opencode_home_path(sandbox_dir)`` and remove it after the run
    (see ``cleanup_sandbox_artifacts``). When omitted a ``tempfile`` dir is
    created that the caller must clean up itself.

    ``name`` (docker only) names the container so a caller that gives up on the
    run can still ``docker kill`` it: killing the ``docker run`` client only
    detaches, the container keeps going."""
    if spec.sandbox == "docker":
        command = [
            "docker", "run", "--rm", "-i", "-w", workdir,
            "--add-host", "host.docker.internal:host-gateway",
            "-e", f"HOME={home}",
        ]
        if name:
            command += ["--name", name]
        for host, dst, read_only in binds:
            command += ["-v", f"{host}:{dst}:ro" if read_only else f"{host}:{dst}"]
        for key, value in env.items():
            command += ["-e", f"{key}={value}"]
        command += [spec.image, *args]
        return command
    elif spec.sandbox == "apptainer":
        if writable_home is None:
            writable_home = Path(tempfile.mkdtemp(prefix="opencode_home_"))
        else:
            # Recreate fresh so a stale home from a crashed run never leaks state.
            shutil.rmtree(writable_home, ignore_errors=True)
            writable_home.mkdir(parents=True, exist_ok=True)
        binds = list(binds) + [(str(Path(writable_home).absolute()), home, False)]
        apptainer = [
            spec.apptainer_path or "apptainer", "exec",
            "--contain", "--writable-tmpfs", "--home", home, "--pwd", workdir,
        ]
        for host, dst, read_only in binds:
            apptainer += ["--bind", f"{host}:{dst}:ro" if read_only else f"{host}:{dst}"]
        apptainer += [spec.image, *args]

        # Forward the env with the APPTAINERENV_ prefix (comma-safe) via ``env`` so
        # it is set for the apptainer process regardless of backend host.
        prefixed_env = [f"APPTAINERENV_{key}={value}" for key, value in env.items()]
        if spec.os == "mac":
            return ["limactl", "shell", "apptainer", "env", *prefixed_env, *apptainer]
        elif spec.os == "linux":
            return ["env", *prefixed_env, *apptainer]
        else:
            raise ValueError(f"unknown os: {spec.os}")
    else:
        raise ValueError(f"unknown sandbox: {spec.sandbox}")
