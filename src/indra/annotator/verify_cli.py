
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verifier import verify_task


def truncate_events(response, k):
    kept, remaining = [], k
    for message in response:
        if remaining <= 0:
            break
        if message.get("role") == "assistant" and message.get("tool_calls"):
            calls = message["tool_calls"][:remaining]
            remaining -= len(calls)
            kept.append({**message, "tool_calls": calls})
        elif message.get("role") == "tool":
            kept.append(message)
            remaining -= 1
        else:
            kept.append(message)
    return kept


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--response", required=True, help="trajectory message list JSON file")
    parser.add_argument("--specs", required=True, help="specification JSON file")
    parser.add_argument("--env_dir", required=True, help="environment observer root directory")
    parser.add_argument("--nuxmv", required=True, help="nuXmv executable path")
    parser.add_argument("--prefix", type=int, default=None, help="truncate to the first K tool events")
    parser.add_argument("--verbose", action="store_true", help="output nuXmv model and raw output to stderr")
    args = parser.parse_args()

    with open(args.response, encoding="utf-8") as file:
        response = json.load(file)
    if args.prefix is not None:
        response = truncate_events(response, args.prefix)
    with open(args.specs, encoding="utf-8") as file:
        specs_data = json.load(file)

    if isinstance(specs_data, dict):
        groups = [(key, [item["formal_spec"] for item in specs_data.get(key, [])])
                  for key in ("completion_specifications", "safety_specifications", "security_specifications")]
    else:
        groups = [("results", list(specs_data))]

    flat = [spec for _, specs in groups for spec in specs]
    outcome = verify_task(response, flat, args.env_dir, args.nuxmv)
    if args.verbose:
        print(outcome["model"], file=sys.stderr)
        print(outcome["output"], file=sys.stderr)

    report, cursor = {}, 0
    for key, specs in groups:
        report[key] = [
            {"formal_spec": spec, "result": outcome["results"][cursor + offset]}
            for offset, spec in enumerate(specs)
        ]
        cursor += len(specs)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
