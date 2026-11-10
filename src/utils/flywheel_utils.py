import difflib
import shutil
from argparse import ArgumentParser
from pathlib import Path
import json

IGNORE_TOOLKITS = [
    "amap_toolkit",
    "arxiv_toolkit",
    "attack_toolkit",
    "calendar_toolkit",
    "clock_toolkit",
    "system_toolkit",
    "tavily_toolkit",
    "tpa_toolkit",
    "weather_toolkit",
    "system_toolkit",
    "stock_toolkit"
]

def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--dataset_save_path",
        type=Path,
        required=True,
        help="Dataset save path",
    )
    parser.add_argument(
        "--skip_permission",
        action="store_true",
        help="Skip permission check",
    )
    parser.add_argument(
        "--merge_dataset_only",
        action="store_true",
        help="Skip permission check",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        required=False,
        default=None,
        help="Flywheel output directory (e.g. data/output/flywheel)",
    )
    parser.add_argument(
        "--merged_dataset_path",
        type=Path,
        required=False,
        default=None,
        help="Dataset save path",
    ) 
    args = parser.parse_args()

    if args.merge_dataset_only:
        assert args.merged_dataset_path is not None
        if args.dataset_save_path.exists():
            with open(args.dataset_save_path, "r", encoding="utf-8") as f:
                dataset = [json.loads(line) for line in f]
        else:
            dataset = []

        with open(args.merged_dataset_path, "r", encoding="utf-8") as f:
            generated_dataset = [json.loads(line) for line in f]

        num = len(dataset)

        for data in generated_dataset:
            data["traceid"] = num
            dataset.append(data)
            num += 1

        with open(args.dataset_save_path, "w", encoding="utf-8") as f:
            for data in dataset:
                f.write(json.dumps(data, ensure_ascii=False) + "\n")

        print(f"\ndataset save: {args.dataset_save_path}\n num: {len(dataset)}")
        return

    repo_root = Path(__file__).resolve().parents[2]
    mappings = [
        (args.output_dir / "toolkits", repo_root / "src" / "toolkits" / "ras_eval"),
        (args.output_dir / "environment", repo_root / "data" / "ras_eval" / "environment"),
    ]
    generated_dataset_path = args.output_dir / "dataset" / "generated.jsonl"
    progress_dataset_path = args.output_dir / "dataset" / "progress.jsonl"

    merged, skipped = 0, 0
    for src_dir, dst_dir in mappings:
        if not src_dir.is_dir():
            continue
        for src_file in sorted(p for p in src_dir.rglob("*") if p.is_file()):
            dst_file = dst_dir / src_file.relative_to(src_dir)
            src_bytes = src_file.read_bytes()
            if dst_file.exists():
                dst_bytes = dst_file.read_bytes()
                if src_bytes == dst_bytes:
                    continue
                print(f"\n[diff] {src_file} -> {dst_file}")
                try:
                    diff = difflib.unified_diff(
                        dst_bytes.decode("utf-8").splitlines(keepends=True),
                        src_bytes.decode("utf-8").splitlines(keepends=True),
                        fromfile=str(dst_file),
                        tofile=str(src_file),
                    )
                    print("".join(diff), end="")
                except UnicodeDecodeError:
                    print("(binary file differs)")
            else:
                print(f"\n[new] {src_file} -> {dst_file}")
            if ".pyc" in dst_file.name:
                answer = "n"
            elif any(keyword in src_file.name for keyword in IGNORE_TOOLKITS):
                answer = "n"
            elif args.skip_permission:
                answer = "y"
            else:
                try:
                    answer = input("Merge into repo? [y/n]: ").strip().lower()
                except EOFError:
                    print("(stdin closed, treat as n)")
                    answer = "n"
            
            if answer == "y":
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(src_file, dst_file)
                print(f"merged: {dst_file}")
                merged += 1
            else:
                print(f"skipped: {dst_file}")
                skipped += 1

    print(f"\n{args.output_dir} check completed: merged {merged}, skipped {skipped}")


    if args.dataset_save_path.exists():
        with open(args.dataset_save_path, "r", encoding="utf-8") as f:
            dataset = [json.loads(line) for line in f]
    else:
        dataset = []

    with open(generated_dataset_path, "r", encoding="utf-8") as f:
        generated_dataset = [json.loads(line) for line in f]

    num = len(dataset)

    for data in generated_dataset:
        data["traceid"] = num
        dataset.append(data)
        num += 1

    with open(args.dataset_save_path, "w", encoding="utf-8") as f:
        for data in dataset:
            f.write(json.dumps(data) + "\n")

    print(f"\ndataset save: {args.dataset_save_path}\n num: {len(dataset)}")


if __name__ == "__main__":
    main()
