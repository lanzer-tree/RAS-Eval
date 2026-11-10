#!/usr/bin/env bash
set -euo pipefail

# Prompt-injection detector defense: per-sample inference + LTL runtime
# verification, with the prompt_detector opencode plugin scanning tool
# descriptions before the task and tool outputs during the task, appending a
# defense note when an injection is detected. It is an opencode plugin, so only
# the opencode framework applies. Detection uses the agent's own model
# (deepseek-v4-pro) via the .env OPENAI_API_KEY / OPENAI_BASE_URL.


OUTPUT_DIR="${OUTPUT_DIR:-data/output/prompt_detector_runtime_verification}"

DATASETS=(
    ras_eval_next_cia_skill_small_attack_v2:data/input/ras_eval_next_cia_skill_small_attack_v2.jsonl
    ras_eval_next_cia_tool_small_attack:data/input/ras_eval_next_cia_tool_small_attack.jsonl
    ras_eval_next_toma_small_attack_v2:data/input/ras_eval_next_toma_small_attack_v2.jsonl
    ras_eval_next_tpa_small_attack_v2:data/input/ras_eval_next_tpa_small_attack_v2.jsonl
)

MODELS=(
    dashscope/deepseek-v4-pro
    dashscope/glm-5.2
)

mkdir -p "${OUTPUT_DIR}"
for model in "${MODELS[@]}"; do
    for item in "${DATASETS[@]}"; do
        name="${item%%:*}"
        input_path="${item#*:}"
        python entries/defense/prompt_detector_runtime_verification.py \
            --framework opencode \
            --model "${model}" \
            --sandbox "docker" \
            --os "mac" \
            --input_path "${input_path}" \
            --output_path "${OUTPUT_DIR}/${model}_opencode_${name}.jsonl" \
            --parallel 2 \
            --qps 1000.0 \
            --timeout 900 \
            --image "ras-eval-agent:latest" \
            --skip_exist_traceid 
done
