#!/usr/bin/env bash
set -euo pipefail

# scan_repair runtime guardrail: per-sample inference + LTL runtime verification.
# Before each task a standalone opencode subagent (same model) scans the
# task-local tool/skill code and repairs data-leakage risks in place, then the
# main agent runs against the repaired code. scan_repair is host-side and only
# the opencode framework applies.


OUTPUT_DIR="${OUTPUT_DIR:-data/output/scan_repair_runtime_verification}"

DATASETS=(
    ras_eval_next_cia_skill_small_attack_v2:data/input/ras_eval_next_cia_skill_small_attack_v2.jsonl
    ras_eval_next_cia_tool_small_attack:data/input/ras_eval_next_cia_tool_small_attack.jsonl
    ras_eval_next_toma_small_attack_v2:data/input/ras_eval_next_toma_small_attack_v2.jsonl
    ras_eval_next_tpa_small_attack_v2:data/input/ras_eval_next_tpa_small_attack_v2.jsonl
)

mkdir -p "${OUTPUT_DIR}"
for item in "${DATASETS[@]}"; do
    name="${item%%:*}"
    input_path="${item#*:}"
    uv run entries/defense/scan_repair_runtime_verification.py \
        --framework opencode \
        --model "dashscope-inc/deepseek-v4-pro" \
        --sandbox "docker" \
        --os "mac" \
        --input_path "${input_path}" \
        --output_path "data/output/scan_repair_runtime_verification/deepseek-v4-pro_opencode_${name}.jsonl" \
        --parallel 2 \
        --qps 1000.0 \
        --timeout 800 \
        --image "ras-eval-agent:latest" \
        --skip_exist_traceid \
        --limit 8
done
