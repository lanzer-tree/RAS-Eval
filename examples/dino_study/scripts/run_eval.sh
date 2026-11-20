#!/usr/bin/env bash
# Replay the static dino.study trajectories in the simulated environment and check the LTL specs
# after every assistant and tool message (no LLM, no Docker).
# Run from anywhere; paths are resolved relative to the repository root.
set -euo pipefail
cd "$(dirname "$0")/../../.."

uv run examples/dino_study/src/evaluate.py \
    --specs_path examples/dino_study/data/specs.json \
    --environment_path examples/dino_study/data/environment.json \
    --input_path examples/dino_study/data/responses.jsonl \
    --output_path examples/dino_study/data/results.jsonl \
    --timeout 60
