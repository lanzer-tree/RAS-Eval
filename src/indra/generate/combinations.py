"""Tool-combination enumeration to guide diverse sample generation.

A combination is *k* distinct tools drawn from a single toolkit. To keep small
runs diverse and bound cost at large depth we:

* cap the number of combinations kept per toolkit (``max_per_toolkit``), counting
  already-generated samples against that cap;
* shuffle candidates within each toolkit and shuffle the toolkits' contributions
  together, all with a fixed seed so resuming stays deterministic;
* sample (rather than fully enumerate) when ``C(n, k)`` is huge, so memory stays
  bounded at large depth.

Each combination gets a content-derived traceid (independent of ordering) so a
run can resume from an existing output directory regardless of shuffle order.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import math
import random
from dataclasses import dataclass
from pathlib import Path

# Attack/injection toolkits are enormous and not meaningful task material.
_EXCLUDED_TOOLKITS = {"attack_toolkit", "tpa_toolkit"}
_TRACEID_BASE = 2_000_000
_TRACEID_SPAN = 90_000_000
# Above this many combinations we sample instead of materializing the full list.
_ENUM_CAP = 200_000
_DEFAULT_SEED = 0


@dataclass(frozen=True)
class Combination:
    toolkit: str
    tools: tuple[str, ...]        # the k selected tools (sorted)
    all_tools: tuple[str, ...]    # every tool exposed by the toolkit
    specs: tuple[dict, ...]       # json schema of the k selected tools
    traceid: int


def load_toolkit_tools(output_dir: Path, toolkit: str) -> list[dict]:
    """Read a toolkit's tool schemas from its json file in the workspace copy.

    Returns a list of ``{"name", "description", "parameters"}`` dicts. Static
    parsing avoids importing toolkit modules (and their heavy deps) on the host.
    """
    json_path = Path(output_dir) / "toolkits" / toolkit / "json" / f"{toolkit}.json"
    entries = json.loads(json_path.read_text(encoding="utf-8"))
    tools = []
    for entry in entries:
        fn = entry.get("function", entry)
        tools.append({
            "name": fn["name"],
            "description": fn.get("description", ""),
            "parameters": fn.get("parameters", {}),
        })
    return tools


def _combo_traceid(toolkit: str, tools: tuple[str, ...]) -> int:
    """Stable traceid derived from the combination content (order-independent)."""
    key = f"{toolkit}|{','.join(sorted(tools))}"
    digest = hashlib.sha1(key.encode("utf-8")).hexdigest()
    return _TRACEID_BASE + int(digest[:10], 16) % _TRACEID_SPAN


def _load_existing_tool_sets(*jsonl_paths: Path) -> set[frozenset[str]]:
    """Collect the exact tool sets of every sample in the given files.

    Generated samples expose the whole toolkit in ``meta.tools`` but record the
    guiding combination in ``meta.combination``; that field takes precedence so a
    combination is excluded even if its progress journal is missing.
    """
    existing: set[frozenset[str]] = set()
    for path in jsonl_paths:
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").split("\n"):
            line = line.strip()
            if not line:
                continue
            meta = json.loads(line).get("meta", {})
            tools = meta.get("combination") or meta.get("tools", [])
            if tools:
                existing.add(frozenset(tools))
    return existing


def _load_generated_toolkit_counts(generated_path: Path) -> dict[str, int]:
    """Count how many samples each toolkit already contributed to generated.jsonl."""
    counts: dict[str, int] = {}
    if not generated_path.exists():
        return counts
    for line in generated_path.read_text(encoding="utf-8").split("\n"):
        line = line.strip()
        if not line:
            continue
        for toolkit in json.loads(line).get("meta", {}).get("toolkits", []):
            counts[toolkit] = counts.get(toolkit, 0) + 1
    return counts


def _toolkit_pool(all_names: tuple[str, ...], depth: int, cap: int | None, rng: random.Random) -> list[tuple[str, ...]]:
    """A shuffled pool of up to ``cap`` distinct depth-``k`` combinations.

    When ``cap`` is None the full (shuffled) enumeration is returned. When the
    total number of combinations is large the pool is sampled by rejection so
    memory stays bounded at high depth.
    """
    total = math.comb(len(all_names), depth)
    if cap is None or total <= _ENUM_CAP:
        combos = [tuple(c) for c in itertools.combinations(all_names, depth)]
        rng.shuffle(combos)
        return combos if cap is None else combos[:cap]

    # total > _ENUM_CAP and a cap is set: rejection-sample distinct combinations.
    seen: set[tuple[str, ...]] = set()
    pool: list[tuple[str, ...]] = []
    max_attempts = cap * 50
    for _ in range(max_attempts):
        if len(pool) >= cap:
            break
        combo = tuple(sorted(rng.sample(all_names, depth)))
        if combo not in seen:
            seen.add(combo)
            pool.append(combo)
    return pool


def enumerate_combinations(
    output_dir: Path,
    depth: int,
    max_per_toolkit: int | None = None,
    seed: int = _DEFAULT_SEED,
) -> list[Combination]:
    """Enumerate depth-``k`` combinations across toolkits in the workspace.

    Excludes attack toolkits and any combination whose exact tool set already
    appears in ``dataset/base.jsonl`` or ``dataset/generated.jsonl``. When
    ``max_per_toolkit`` is set, each toolkit yields at most that many samples in
    total (already-generated samples count against the budget). Results are
    shuffled deterministically for cross-toolkit diversity.
    """
    output_dir = Path(output_dir)
    toolkits_dir = output_dir / "toolkits"
    dataset_dir = output_dir / "dataset"
    existing = _load_existing_tool_sets(
        dataset_dir / "base.jsonl",
        dataset_dir / "generated.jsonl",
    )
    generated_counts = _load_generated_toolkit_counts(dataset_dir / "generated.jsonl")

    combinations: list[Combination] = []
    for toolkit_dir in sorted(p for p in toolkits_dir.iterdir() if p.is_dir()):
        toolkit = toolkit_dir.name
        if toolkit in _EXCLUDED_TOOLKITS:
            continue
        tools = load_toolkit_tools(output_dir, toolkit)
        if len(tools) < depth:
            continue

        need = None
        if max_per_toolkit is not None:
            need = max_per_toolkit - generated_counts.get(toolkit, 0)
            if need <= 0:
                continue

        by_name = {t["name"]: t for t in tools}
        all_names = tuple(sorted(by_name))
        rng = random.Random(f"{seed}:{toolkit}")
        pool = _toolkit_pool(all_names, depth, max_per_toolkit, rng)
        new = [combo for combo in pool if frozenset(combo) not in existing]
        if need is not None:
            new = new[:need]
        for combo in new:
            combinations.append(Combination(
                toolkit=toolkit,
                tools=combo,
                all_tools=all_names,
                specs=tuple(by_name[name] for name in combo),
                traceid=_combo_traceid(toolkit, combo),
            ))

    random.Random(seed).shuffle(combinations)
    return combinations
