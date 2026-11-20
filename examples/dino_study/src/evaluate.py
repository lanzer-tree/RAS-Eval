"""Replay dino.study tutor trajectories in a simulated environment and check RAS-Eval LTL specs.

Every trajectory starts from its session in data/environment.json and is replayed message by
message. An assistant message appends its tool calls to the trace (the environment is still the
one before execution); a tool message executes the matching call in the simulator and appends
the return (the environment is now the one after execution). After every assistant and tool
message all specifications are model-checked with nuXmv on the trace so far, where the custom
observers of observers.py are evaluated on the environment snapshot of each time step.
No LLM, sandbox or Docker is needed.
"""
import argparse
import copy
import importlib.util
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from observers import OBSERVER_PARAMS, OBSERVERS
from simulator import DinoStudy

REPO_ROOT = Path(__file__).resolve().parents[3]
VERIFIER_PATH = REPO_ROOT / "src" / "evaluator" / "spec" / "verifier.py"
SPEC_GROUPS = ("safety_specifications", "security_specifications", "completion_specifications")

# Load the RAS-Eval verifier by file path so that the package __init__ (sandbox, docker, ...)
# is not imported. It only depends on the Python standard library.
_module_spec = importlib.util.spec_from_file_location("ras_eval_verifier", VERIFIER_PATH)
verifier = importlib.util.module_from_spec(_module_spec)
_module_spec.loader.exec_module(verifier)

# Replace the file-system observers (read, glob, grep, bash) by the dino.study observers, so that
# `tool(mastered())[mastered]` is accepted by the spec parser and evaluated on the learner state.
verifier.OBSERVER_PARAMS.clear()
verifier.OBSERVER_PARAMS.update(OBSERVER_PARAMS)
verifier.OBSERVERS.clear()
verifier.OBSERVERS.update(OBSERVERS)


def default_nuxmv():
    if os.environ.get("NUXMV_BIN"):
        return os.environ["NUXMV_BIN"]
    system = platform.system()
    if system == "Darwin":
        return str(REPO_ROOT / "bin" / "nuXmv" / "bin" / "nuXmv")
    if system == "Linux":
        return str(REPO_ROOT / "bin" / "nuXmv-2.2.0-linux64" / "usr" / "local" / "bin" / "nuXmv-portable.sh")
    raise SystemExit(f"no bundled nuXmv for {system}; download it from https://nuxmv.fbk.eu and pass --nuxmv")


class Specs:
    """All specifications compiled once into nuXmv LTL over shared atoms p0, p1, ..."""

    def __init__(self, path):
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        self.ids, self.ltl, self.errors, self.atom_index = [], {}, {}, {}
        for group in SPEC_GROUPS:
            for spec in data.get(group) or []:
                self.ids.append(spec["id"])
                try:
                    self.ltl[spec["id"]] = verifier.parse_spec(spec["formal_spec"], self.atom_index)
                except Exception as error:
                    self.errors[spec["id"]] = f"error: {error}"

    def build_model(self, events, states):
        """Step t = 1..len(events) is events[t-1]; t = 0 is before the first event and t = sink
        repeats forever after the last one. The environment at step t is the snapshot after the
        last tool return at or before t, so a call sees the state before it runs and a return
        sees the state after it ran. This also holds for parallel tool calls."""
        sink = len(events) + 1
        snapshot = [0]
        for kind, _, _ in events:
            snapshot.append(snapshot[-1] + (kind == "return"))
        snapshot.append(snapshot[-1])
        caches = [{} for _ in states]
        lines = [
            "MODULE main",
            "VAR",
            f"    t : 0..{sink};",
            "ASSIGN",
            "    init(t) := 0;",
            f"    next(t) := case t < {sink} : t + 1; TRUE : t; esac;",
            "DEFINE",
        ]
        for atom, idx in self.atom_index.items():
            if atom[1][0] == "env":
                times = [t for t in range(sink + 1)
                         if verifier.eval_env_atom(atom, states[snapshot[t]], caches[snapshot[t]])]
            else:
                times = [t for t, event in enumerate(events, 1) if verifier.eval_event_atom(atom, event)]
            lines.append(f"    p{idx} := {' | '.join(f'(t = {t})' for t in times) or 'FALSE'};")
        lines += [f"LTLSPEC {self.ltl[spec_id]}" for spec_id in self.ids if spec_id in self.ltl]
        return "\n".join(lines) + "\n"

    def check(self, events, states, nuxmv, timeout):
        verdicts = dict(self.errors)
        checked = [spec_id for spec_id in self.ids if spec_id in self.ltl]
        if checked:
            script = "go\n" + "".join(f"check_ltlspec -n {i}\n" for i in range(len(checked))) + "quit\n"
            with tempfile.TemporaryDirectory() as tmpdir:
                path = os.path.join(tmpdir, "trace.xmv")
                Path(path).write_text(self.build_model(events, states), encoding="utf-8")
                try:
                    process = subprocess.run([nuxmv, "-int", path], input=script,
                                             capture_output=True, text=True, timeout=timeout)
                    output = process.stdout + process.stderr
                except subprocess.TimeoutExpired:
                    output = "nuXmv timeout"
            results = re.findall(r"-- specification .* is (true|false)\s*$", output, re.MULTILINE)
            for i, spec_id in enumerate(checked):
                if len(results) == len(checked):
                    verdicts[spec_id] = "sat" if results[i] == "true" else "unsat"
                else:
                    verdicts[spec_id] = f"error: nuXmv output anomaly ({len(results)}/{len(checked)} results)"
        return {spec_id: verdicts[spec_id] for spec_id in self.ids}


def as_text(value):
    return value if isinstance(value, str) else json.dumps(value if value is not None else {}, ensure_ascii=False)


def as_json(text):
    try:
        return json.loads(text)
    except (TypeError, ValueError):
        return text


def replay(trace, environment, specs, nuxmv, timeout):
    traceid = trace["traceid"]
    simulator = DinoStudy(environment, environment["sessions"][str(traceid)])
    events, states, pending, responses = [], [copy.deepcopy(simulator.state)], {}, []
    for message in trace["responses"]:
        message = dict(message)
        role = message.get("role")
        if role == "assistant":
            for call in message.get("tool_calls") or []:
                name, arguments = call["function"]["name"], as_text(call["function"].get("arguments"))
                pending[call.get("id")] = (name, arguments)
                events.append(("call", name, arguments))
        elif role == "tool":
            name, arguments = pending.pop(message.get("tool_call_id"))
            arguments = as_json(arguments)
            observed = simulator.call(name, arguments if isinstance(arguments, dict) else {})
            content = as_text(message.get("content"))
            if as_json(content) != observed:
                print(f"warning: trace {traceid} {name}: logged return differs from the simulator {observed}",
                      file=sys.stderr)
            states.append(copy.deepcopy(simulator.state))
            events.append(("return", name, content))
        else:
            responses.append(message)
            continue
        message["verdicts"] = specs.check(events, states, nuxmv, timeout)
        responses.append(message)
    return {"traceid": traceid, "responses": responses}


def main():
    here = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--specs_path", default=str(here / "data" / "specs.json"))
    parser.add_argument("--environment_path", default=str(here / "data" / "environment.json"))
    parser.add_argument("--input_path", default=str(here / "data" / "responses.jsonl"))
    parser.add_argument("--output_path", default=str(here / "data" / "results.jsonl"))
    parser.add_argument("--nuxmv", default=None, help="nuXmv binary (default: $NUXMV_BIN or the one bundled in bin/)")
    parser.add_argument("--timeout", type=int, default=60, help="nuXmv timeout in seconds per check")
    args = parser.parse_args()
    nuxmv = args.nuxmv or default_nuxmv()

    specs = Specs(args.specs_path)
    environment = json.loads(Path(args.environment_path).read_text(encoding="utf-8"))
    traces = [json.loads(line) for line in Path(args.input_path).read_text(encoding="utf-8").splitlines() if line.strip()]

    rows = [replay(trace, environment, specs, nuxmv, args.timeout) for trace in traces]
    Path(args.output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output_path, "w", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, ensure_ascii=False) + "\n")

    width = max(len(spec_id) for spec_id in specs.ids)
    print("final verdicts")
    print("traceid  " + "  ".join(f"{spec_id:>{width}}" for spec_id in specs.ids))
    for row in rows:
        judged = [message["verdicts"] for message in row["responses"] if "verdicts" in message]
        final = judged[-1] if judged else specs.check([], [environment["sessions"][str(row["traceid"])]], nuxmv, args.timeout)
        print(f"{row['traceid']:>7}  " + "  ".join(f"{final[spec_id]:>{width}}" for spec_id in specs.ids))
    print(f"results written to {args.output_path}")


if __name__ == "__main__":
    main()
