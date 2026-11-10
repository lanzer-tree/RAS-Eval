"""Archive-backed access to the SKILL-INJECT asset trees.

``data/skill_inject`` ships three asset trees — ``skills``, ``task_files`` and
``task_scripts`` — that together hold more than 11k tiny files. On a
distributed filesystem every file burns one inode, so the trees are stored as
sibling zip archives (``skills.zip``, ``task_files.zip``,
``task_scripts.zip``) and materialised on demand, which is exactly when a
sandbox is built and mounted into the container.

Resolution per tree: the archive provides the baseline and a loose directory of
the same name is overlaid on top of it, winning on conflicts. Either one alone
is enough, so a packed checkout, an unpacked checkout, and a locally generated
workspace (CIA red skills, flywheel output dirs) all keep working unchanged.

Maintenance (re-runnable; ``pack`` verifies before touching anything)::

    uv run python -m src.adapter.skill_inject.archive pack           # dirs -> zips
    uv run python -m src.adapter.skill_inject.archive pack --prune   # ... and drop the dirs
    uv run python -m src.adapter.skill_inject.archive verify
    uv run python -m src.adapter.skill_inject.archive unpack         # zips -> dirs
"""
from __future__ import annotations

import hashlib
import shutil
import zipfile
from pathlib import Path, PurePosixPath

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_ROOT = REPO_ROOT / "data" / "skill_inject"
TREES = ("skills", "task_files", "task_scripts")


def archive_for(data_root: Path, tree: str) -> Path:
    return Path(data_root) / f"{tree}.zip"


def _split(rel_path: str | Path) -> tuple[str, str]:
    """Split ``task_files/a/b`` into the tree name and the in-archive member."""
    parts = PurePosixPath(str(rel_path).replace("\\", "/")).parts
    if not parts or any(part in ("..", "") for part in parts):
        raise ValueError(f"invalid skill-inject asset path: {rel_path!r}")
    return parts[0], "/".join(parts[1:])


def _checked(name: str) -> str:
    if any(part == ".." for part in PurePosixPath(name).parts) or name.startswith("/"):
        raise ValueError(f"archive member escapes its destination: {name!r}")
    return name


def _members(zf: zipfile.ZipFile, member: str) -> list[str]:
    """Names of *member* itself (a file) or of everything below it (a directory)."""
    prefix = f"{member}/"
    return [name for name in zf.namelist() if name == member or name.startswith(prefix)]


def _extract(zf: zipfile.ZipFile, name: str, dest: Path) -> None:
    """Write one archive member to *dest*, keeping the recorded file mode."""
    if name.endswith("/"):
        dest.mkdir(parents=True, exist_ok=True)
        return
    info = zf.getinfo(name)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with zf.open(info) as src, dest.open("wb") as out:
        shutil.copyfileobj(src, out)
    mode = (info.external_attr >> 16) & 0o7777
    if mode:
        dest.chmod(mode)


def exists(data_root: Path, rel_path: str | Path) -> bool:
    """Whether *rel_path* is available either loose on disk or in its archive."""
    if (Path(data_root) / rel_path).exists():
        return True
    tree, member = _split(rel_path)
    archive = archive_for(data_root, tree)
    if not archive.exists():
        return False
    if not member:
        return True
    with zipfile.ZipFile(archive) as zf:
        return bool(_members(zf, member))


def copy_into(data_root: Path, rel_path: str | Path, dest: Path) -> bool:
    """Materialise the file or directory *rel_path* at *dest*.

    Mirrors ``shutil.copy2`` for files and ``shutil.copytree`` for directories
    (*dest* is the directory itself, not its parent). Returns ``False`` when the
    asset exists in neither the loose tree nor the archive, so callers can keep
    the benchmark's "skip what is missing" behaviour.
    """
    dest = Path(dest)
    loose = Path(data_root) / rel_path
    if loose.exists():
        if loose.is_dir():
            shutil.copytree(loose, dest, dirs_exist_ok=True)
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(loose, dest)
        return True

    tree, member = _split(rel_path)
    archive = archive_for(data_root, tree)
    if not member or not archive.exists():
        return False
    with zipfile.ZipFile(archive) as zf:
        names = _members(zf, member)
        if not names:
            return False
        if names == [member]:
            _extract(zf, member, dest)
        else:
            for name in names:
                _extract(zf, _checked(name), dest / name[len(member) + 1:])
    return True


def copy_tree(data_root: Path, tree: str, dest: Path) -> None:
    """Materialise a whole asset tree at *dest*: archive first, loose dir on top."""
    archive = archive_for(data_root, tree)
    loose = Path(data_root) / tree
    if not archive.exists() and not loose.is_dir():
        raise FileNotFoundError(f"skill-inject assets missing: neither {archive} nor {loose}")
    dest = Path(dest)
    dest.mkdir(parents=True, exist_ok=True)
    if archive.exists():
        with zipfile.ZipFile(archive) as zf:
            for name in zf.namelist():
                _extract(zf, _checked(name), dest / name)
    if loose.is_dir():
        shutil.copytree(loose, dest, dirs_exist_ok=True)


# --------------------------------------------------------------------------- #
# Maintenance CLI                                                             #
# --------------------------------------------------------------------------- #
def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pack_tree(data_root: Path, tree: str) -> Path:
    """(Re)build ``<tree>.zip`` from the loose ``<tree>/`` directory."""
    root = Path(data_root) / tree
    if not root.is_dir():
        raise FileNotFoundError(root)
    archive = archive_for(data_root, tree)
    tmp = archive.with_name(f"{archive.name}.tmp")
    with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for path in sorted(root.rglob("*")):
            if path.is_symlink():
                raise ValueError(f"symlinks are not archivable: {path}")
            rel = _checked(path.relative_to(root).as_posix())
            if path.is_dir():
                if not any(path.iterdir()):
                    zf.writestr(zipfile.ZipInfo(f"{rel}/"), b"")
            else:
                zf.write(path, rel)
    tmp.replace(archive)
    return archive


def verify_tree(data_root: Path, tree: str) -> list[str]:
    """Compare ``<tree>.zip`` against the loose ``<tree>/``; return the mismatches."""
    root = Path(data_root) / tree
    archive = archive_for(data_root, tree)
    if not root.is_dir():
        return [f"{tree}: no loose directory to compare against"]
    if not archive.exists():
        return [f"{tree}: {archive.name} missing"]

    on_disk: dict[str, Path] = {}
    for path in root.rglob("*"):
        if path.is_dir():
            if not any(path.iterdir()):
                on_disk[f"{path.relative_to(root).as_posix()}/"] = path
        else:
            on_disk[path.relative_to(root).as_posix()] = path

    problems: list[str] = []
    with zipfile.ZipFile(archive) as zf:
        archived = set(zf.namelist())
        for name in sorted(archived - set(on_disk)):
            problems.append(f"{tree}: only in archive: {name}")
        for name in sorted(set(on_disk) - archived):
            problems.append(f"{tree}: only on disk: {name}")
        for name in sorted(archived & set(on_disk)):
            if name.endswith("/"):
                continue
            path = on_disk[name]
            if _digest(zf.read(name)) != _digest(path.read_bytes()):
                problems.append(f"{tree}: content differs: {name}")
                continue
            archived_exec = bool((zf.getinfo(name).external_attr >> 16) & 0o111)
            if archived_exec != bool(path.stat().st_mode & 0o111):
                problems.append(f"{tree}: exec bit differs: {name}")
    return problems


def unpack_tree(data_root: Path, tree: str) -> Path:
    """Restore the loose ``<tree>/`` directory from ``<tree>.zip``."""
    dest = Path(data_root) / tree
    copy_tree(data_root, tree, dest)
    return dest


def main() -> None:
    from argparse import ArgumentParser

    parser = ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["pack", "verify", "unpack"])
    parser.add_argument("--data_root", type=Path, default=DATA_ROOT)
    parser.add_argument("--tree", action="append", choices=list(TREES), default=None)
    parser.add_argument(
        "--prune",
        action="store_true",
        help="pack only: delete the loose directory once the archive verifies",
    )
    args = parser.parse_args()
    trees = tuple(args.tree) if args.tree else TREES

    for tree in trees:
        if args.command == "unpack":
            print(f"[unpack] {tree} -> {unpack_tree(args.data_root, tree)}")
            continue
        if args.command == "pack":
            archive = pack_tree(args.data_root, tree)
            size = archive.stat().st_size / 1e6
            print(f"[pack] {tree} -> {archive.name} ({size:.1f} MB)")
        problems = verify_tree(args.data_root, tree)
        if problems:
            for problem in problems[:20]:
                print(f"[FAIL] {problem}")
            raise SystemExit(f"{tree}: {len(problems)} mismatch(es); nothing was deleted")
        print(f"[ok] {tree}: archive matches the loose directory")
        if args.command == "pack" and args.prune:
            shutil.rmtree(Path(args.data_root) / tree)
            print(f"[prune] removed {tree}/")


if __name__ == "__main__":
    main()
