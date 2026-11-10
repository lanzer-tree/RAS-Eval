"""Select failed RAS-Eval attack samples for quick attack-refine smoke tests."""
from __future__ import annotations

import json
from argparse import ArgumentParser
from pathlib import Path
from typing import Any


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def select_failed_samples(
    dataset_paths: list[Path],
    eval_path: Path,
    output_path: Path,
    per_attack: int,
) -> list[dict[str, Any]]:
    samples: dict[int, dict[str, Any]] = {}
    for dataset_path in dataset_paths:
        for sample in _load_jsonl(dataset_path):
            samples[int(sample["traceid"])] = sample

    failed = [record for record in _load_jsonl(eval_path) if not record.get("attack_success")]
    grouped: dict[str, list[dict[str, Any]]] = {"toma": [], "tpa": []}
    for record in failed:
        sample = samples.get(int(record["traceid"]))
        if not sample:
            continue
        attack_type = sample.get("meta", {}).get("attack_type", "")
        if attack_type in grouped:
            grouped[attack_type].append(record)

    selected: list[dict[str, Any]] = []
    for attack_type, records in grouped.items():
        records.sort(key=lambda item: (-float(item.get("tcr", 0.0)), int(item["traceid"])))
        seen_criteria: set[tuple[str, ...]] = set()
        chosen: list[dict[str, Any]] = []
        for record in records:
            criteria = tuple(record.get("criteria_tools") or [])
            if criteria in seen_criteria:
                continue
            chosen.append(record)
            seen_criteria.add(criteria)
            if len(chosen) >= per_attack:
                break
        if len(chosen) < per_attack:
            chosen_ids = {int(item["traceid"]) for item in chosen}
            for record in records:
                if int(record["traceid"]) not in chosen_ids:
                    chosen.append(record)
                if len(chosen) >= per_attack:
                    break
        if len(chosen) < per_attack:
            print(f"[WARN] only found {len(chosen)} failed {attack_type} sample(s)")
        selected.extend(samples[int(record["traceid"])] for record in chosen)

    selected.sort(key=lambda sample: int(sample["traceid"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as file:
        for sample in selected:
            file.write(json.dumps(sample, ensure_ascii=False) + "\n")
    return selected


def main() -> None:
    parser = ArgumentParser()
    parser.add_argument("--dataset_path", type=Path, action="append", required=True)
    parser.add_argument("--eval_path", type=Path, required=True)
    parser.add_argument("--output_path", type=Path, required=True)
    parser.add_argument("--per_attack", type=int, default=5)
    args = parser.parse_args()
    selected = select_failed_samples(args.dataset_path, args.eval_path, args.output_path, args.per_attack)
    counts: dict[str, int] = {}
    for sample in selected:
        attack_type = sample.get("meta", {}).get("attack_type", "")
        counts[attack_type] = counts.get(attack_type, 0) + 1
    print(f"Wrote {len(selected)} sample(s) to {args.output_path}: {counts}")


if __name__ == "__main__":
    main()
