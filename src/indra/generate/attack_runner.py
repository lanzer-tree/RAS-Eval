"""Main loop for LTL-guided attack generation."""
from __future__ import annotations

import json
import os
import shutil
from collections import deque
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from tqdm import tqdm

from src.indra.generate.attack_spec import draft_security_specs
from src.indra.generate.attack_task import run_attack_task
from src.indra.generate.attack_workspace import ensure_attack_generate_workspace
from src.indra.refine.runner import _RateLimiter


@dataclass(frozen=True)
class AttackGenerateConfig:
    input_path: Path
    output_dir: Path
    attack_model: str
    target_model: str
    sandbox: str
    os: str
    parallel: int = 1
    qps: float = 1.0
    traceid: int | None = None
    timeout: int = 900
    skip_exist_traceid: bool = False
    apptainer_path: str | None = None
    image: str | None = None
    max_iterations: int = 3
    max_restart: int = 3
    number_target_tool: int = 1
    attack_type: str = ""
    limit: int | None = None
    attack_api_key: str | None = None
    attack_base_url: str | None = None
    target_api_key: str | None = None
    target_base_url: str | None = None


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _load_traceids(path: Path) -> set[int]:
    traceids: set[int] = set()
    for item in _load_jsonl(path):
        try:
            traceids.add(int(item["traceid"]))
        except Exception:
            continue
    return traceids


def _load_attack_traceids(path: Path) -> set[int]:
    """Traceids of attack tasks already journaled in progress.jsonl.

    Attack rows carry ``base_traceid``; spec-level rows (spec_empty/spec_error) do
    not, which is what separates the two now that an attack sample reuses the
    traceid of its base sample.
    """
    traceids: set[int] = set()
    for item in _load_jsonl(path):
        if "base_traceid" not in item:
            continue
        try:
            traceids.add(int(item["traceid"]))
        except Exception:
            continue
    return traceids


def _load_security_cache(path: Path) -> dict[int, list[dict[str, str]]]:
    cache: dict[int, list[dict[str, str]]] = {}
    for item in _load_jsonl(path):
        try:
            cache[int(item["traceid"])] = item.get("specs") or []
        except Exception:
            continue
    return cache


def _write_jsonl(file, record: dict[str, Any]) -> None:
    file.write(json.dumps(record, ensure_ascii=False) + "\n")
    file.flush()
    os.fsync(file.fileno())


def _gc_trace_dirs(traces_dir: Path, keep: set[str]) -> None:
    """Drop trace dirs this run will never read again.

    A SPEC-{tid} dir only matters while its spec is missing from
    security_specs.jsonl (it doubles as the drafting agent's disk cache) and an
    ATTACK-{tid} dir only while its task is still pending, so everything else --
    including debris left by earlier runs or an older traceid scheme -- is
    reclaimed here. Each attack attempt snapshots the environment, so these dirs
    are the pipeline's dominant disk consumer.
    """
    if not traces_dir.exists():
        return
    for path in traces_dir.iterdir():
        if path.is_dir() and path.name not in keep:
            shutil.rmtree(path, ignore_errors=True)


def _filter_samples(samples: list[dict[str, Any]], cfg: AttackGenerateConfig) -> list[dict[str, Any]]:
    if cfg.traceid is not None:
        return [sample for sample in samples if int(sample["traceid"]) == cfg.traceid]
    return samples


def _append_security_specs(path: Path, sample: dict[str, Any], specs: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as file:
        _write_jsonl(file, {"traceid": sample["traceid"], "specs": specs})


def _partition_samples(
    samples: list[dict[str, Any]],
    cache: dict[int, list[dict[str, str]]],
) -> tuple[list[tuple[dict[str, Any], list[dict[str, str]]]], list[dict[str, Any]]]:
    """Split samples into those with cached specs and those still needing drafting."""
    cached: list[tuple[dict[str, Any], list[dict[str, str]]]] = []
    to_draft: list[dict[str, Any]] = []
    for sample in samples:
        specs = cache.get(int(sample["traceid"]))
        if specs is None:
            to_draft.append(sample)
        else:
            cached.append((sample, specs))
    return cached, to_draft


def _expand_attack_jobs(
    sample: dict[str, Any],
    specs: list[dict[str, str]],
    done: set[int],
) -> list[tuple[dict[str, Any], dict[str, str]]]:
    """Turn one sample's spec into a single attack job, dropping traceids already produced."""
    base_traceid = int(sample["traceid"])
    if base_traceid in done:
        return []
    # One base traceid drives exactly one attack task; legacy caches holding several
    # specs keep only their first entry.
    return [(sample, spec) for spec in specs[:1]]


def run_attack_generate(cfg: AttackGenerateConfig) -> list[dict[str, Any]]:
    if cfg.attack_type == "cia":
        from src.indra.generate.cia_runner import run_cia_generate

        return run_cia_generate(cfg)
    if cfg.attack_type == "cia-tool":
        from src.indra.generate.cia_tool_runner import run_cia_tool_generate

        return run_cia_tool_generate(cfg)
    if cfg.attack_type not in {"toma", "tpa", "eia"}:
        raise ValueError("task=generate mode=attack requires --attack_type toma, tpa, eia, cia, or cia-tool")
    ensure_attack_generate_workspace(cfg.output_dir, cfg.input_path)
    shutil.rmtree(Path(cfg.output_dir) / "sandboxes", ignore_errors=True)
    (Path(cfg.output_dir) / "sandboxes").mkdir(parents=True, exist_ok=True)

    samples = _load_jsonl(cfg.input_path)

    dataset_dir = Path(cfg.output_dir) / "dataset"
    traces_dir = Path(cfg.output_dir) / "traces"
    output_path = dataset_dir / "attack_generated.jsonl"
    progress_path = dataset_dir / "progress.jsonl"
    security_path = dataset_dir / "security_specs.jsonl"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    done = _load_traceids(output_path) | _load_attack_traceids(progress_path)
    cache = _load_security_cache(security_path)
    # Computed over every input sample (not the --traceid/--limit subset) so a
    # narrowed run never reclaims trace dirs a later full run still needs.
    keep_traces = {f"SPEC-{int(item['traceid'])}" for item in samples if int(item["traceid"]) not in cache}
    keep_traces |= {f"ATTACK-{int(item['traceid'])}" for item in samples if int(item["traceid"]) not in done}
    _gc_trace_dirs(traces_dir, keep_traces)

    samples = _filter_samples(samples, cfg)
    if not samples:
        print("No samples to process.")
        return []

    cached, to_draft = _partition_samples(samples, cache)

    # Samples whose specs are already cached skip drafting entirely; the rest are
    # drafted on the fly and their attack jobs join the queue as soon as they land.
    attack_queue: deque[tuple[dict[str, Any], dict[str, str]]] = deque()
    for sample, specs in cached:
        attack_queue.extend(_expand_attack_jobs(sample, specs, done))
    draft_queue: deque[dict[str, Any]] = deque(to_draft)

    if not attack_queue and not draft_queue:
        print("No attack tasks to process.")
        return []

    results: list[dict[str, Any]] = []
    limiter = _RateLimiter(cfg.qps)
    workers = max(1, cfg.parallel)
    submitted = 0
    added = 0

    with output_path.open("a", encoding="utf-8") as out_file, progress_path.open("a", encoding="utf-8") as progress_file:
        spec_bar = tqdm(total=len(draft_queue), desc="Draft specs", unit="sample", position=0, leave=True)
        attack_bar = tqdm(total=len(attack_queue), desc="Attack generate", unit="task", position=1, leave=True)
        pending: dict[Future, tuple[str, Any]] = {}

        def _limit_reached() -> bool:
            return cfg.limit is not None and submitted >= cfg.limit

        def _apply_limit_cutoff() -> None:
            """Drop queued work once --limit is hit so the bars reflect reality."""
            if not _limit_reached():
                return
            if draft_queue:
                spec_bar.total = max(spec_bar.n, spec_bar.total - len(draft_queue))
                draft_queue.clear()
                spec_bar.refresh()
            if attack_queue:
                attack_bar.total = max(attack_bar.n, attack_bar.total - len(attack_queue))
                attack_queue.clear()
                attack_bar.refresh()

        def _handle_spec(sample: dict[str, Any], future: Future) -> None:
            base_traceid = int(sample["traceid"])
            try:
                specs = future.result()
            except Exception as exc:  # noqa: BLE001 - journal and continue
                _write_jsonl(progress_file, {
                    "traceid": base_traceid,
                    "status": "spec_error",
                    "error": f"{type(exc).__name__}: {exc}",
                })
                return
            cache[base_traceid] = specs
            if not specs:
                _write_jsonl(progress_file, {"traceid": base_traceid, "status": "spec_empty"})
                return
            _append_security_specs(security_path, sample, specs)
            # The spec is durable in security_specs.jsonl now, so its drafting
            # workspace (only ever read back as a cache) can go.
            shutil.rmtree(traces_dir / f"SPEC-{base_traceid}", ignore_errors=True)
            jobs = _expand_attack_jobs(sample, specs, done)
            if not jobs:
                return
            attack_queue.extend(jobs)
            attack_bar.total += len(jobs)
            attack_bar.refresh()

        def _handle_attack(job: tuple[dict[str, Any], dict[str, str]], future: Future) -> None:
            nonlocal added
            sample, _ = job
            attack_traceid = int(sample["traceid"])
            try:
                result = future.result()
                status = "added" if result["meta"].get("security_success") else "exhausted"
                progress = {
                    "traceid": attack_traceid,
                    "base_traceid": sample["traceid"],
                    "status": status,
                    "security_success": result["meta"].get("security_success"),
                    "security_attempts": result["meta"].get("security_attempts"),
                    "num_attacks": result["meta"].get("attack_num_targets", 0),
                    "attack_target_tools": result["meta"].get("attack_target_tools", []),
                }
            except Exception as exc:  # noqa: BLE001 - journal and continue
                result = None
                progress = {
                    "traceid": attack_traceid,
                    "base_traceid": sample["traceid"],
                    "status": "error",
                    "error": f"{type(exc).__name__}: {exc}",
                }
            if result is not None:
                results.append(result)
                _write_jsonl(out_file, result)
                if progress["status"] == "added":
                    added += 1
                # The sample is durable in attack_generated.jsonl -- reclaim its
                # attempt workspaces. A crashed task keeps its trace dir for
                # inspection until the next run's startup sweep.
                shutil.rmtree(traces_dir / f"ATTACK-{attack_traceid}", ignore_errors=True)
            _write_jsonl(progress_file, progress)

        with ThreadPoolExecutor(max_workers=workers) as executor:
            def _submit_next() -> bool:
                nonlocal submitted
                if _limit_reached():
                    return False
                # Attack jobs take priority: a sample enters generation as soon as
                # its specs are ready, rather than after all drafting completes.
                if attack_queue:
                    job = attack_queue.popleft()
                    future = executor.submit(run_attack_task, job[0], job[1], cfg.attack_type, cfg, limiter)
                    pending[future] = ("attack", job)
                    submitted += 1
                    _apply_limit_cutoff()
                    return True
                if draft_queue:
                    sample = draft_queue.popleft()
                    pending[executor.submit(draft_security_specs, sample, cfg)] = ("spec", sample)
                    return True
                return False

            for _ in range(workers):
                if not _submit_next():
                    break

            while pending:
                done_futures, _ = wait(list(pending), return_when=FIRST_COMPLETED)
                for future in done_futures:
                    kind, payload = pending.pop(future)
                    if kind == "spec":
                        _handle_spec(payload, future)
                        spec_bar.update(1)
                    else:
                        _handle_attack(payload, future)
                        attack_bar.update(1)
                        attack_bar.set_postfix(added=added)
                    _submit_next()

        spec_bar.close()
        attack_bar.close()

    results.sort(key=lambda item: int(item["traceid"]))
    return results
