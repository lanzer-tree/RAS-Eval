#!/usr/bin/env bash
set -euo pipefail

source "$(conda info --base)/etc/profile.d/conda.sh"
conda activate py12

PORT="${PORT:-8200}"
GPUS="${GPUS:-0,1}"
STARTUP_TIMEOUT="${STARTUP_TIMEOUT:-1800}"
PARALLEL="${PARALLEL:-16}"
QPS="${QPS:-1000.0}"
TIMEOUT="${TIMEOUT:-1500}"
AGENTDOG_TIMEOUT="${AGENTDOG_TIMEOUT:-30}"
LIMIT="${LIMIT:-8}"
MODEL="${MODEL:-dashscope-inc/deepseek-v4-pro}"
AGENTDOG_MODEL="${AGENTDOG_MODEL:-AgentDoG1.5-Qwen3.5-4B}"
AGENTDOG_PATH="${AGENTDOG_PATH:-/tmp/download/AI45Research/AgentDoG1.5-Qwen3.5-4B}"
OUTPUT_DIR="${OUTPUT_DIR:-data/output/eval/deepseek-v4-pro/agentdog}"
IMAGE="${IMAGE:-docker/daedalus-amd-v3.sif}"
APPTAINER_PATH="${APPTAINER_PATH:-bin/apptainer}"

DATASETS=(
    "cia_skill:data/input/ras_eval_next_cia_skill_small_attack_v2.jsonl"
    "cia_tool:data/input/ras_eval_next_cia_tool_small_attack.jsonl"
    "toma:data/input/ras_eval_next_toma_small_attack_v2.jsonl"
    "tpa:data/input/ras_eval_next_tpa_small_attack_v2.jsonl"
)

mkdir -p "${OUTPUT_DIR}"
VLLM_PID=""

stop_vllm() {
    [ -n "${VLLM_PID}" ] || return 0
    echo "=== stopping AgentDoG vLLM"
    kill -INT -"${VLLM_PID}" 2>/dev/null || true
    for _ in $(seq 30); do
        kill -0 -"${VLLM_PID}" 2>/dev/null || break
        sleep 1
    done
    kill -KILL -"${VLLM_PID}" 2>/dev/null || true
    wait "${VLLM_PID}" 2>/dev/null || true
    VLLM_PID=""
}

trap stop_vllm EXIT
trap 'exit 130' INT TERM

if curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null; then
    echo "Port ${PORT} already serves a healthy endpoint; refusing to replace it." >&2
    exit 1
fi

set -m
CUDA_VISIBLE_DEVICES="${GPUS}" TOKENIZERS_PARALLELISM=false \
    vllm serve "${AGENTDOG_PATH}" \
    --served-model-name "${AGENTDOG_MODEL}" \
    --host 127.0.0.1 \
    --port "${PORT}" \
    --max-model-len 131072 \
    --data-parallel-size 2 \
    --data-parallel-backend mp \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.9 \
    --max-num-seqs 64 \
    --enable-prefix-caching \
    --async-scheduling \
    --trust-remote-code >"${OUTPUT_DIR}/agentdog_vllm.log" 2>&1 &
VLLM_PID=$!
set +m

waited=0
until curl -sf "http://127.0.0.1:${PORT}/health" >/dev/null; do
    kill -0 "${VLLM_PID}" 2>/dev/null || {
        echo "AgentDoG vLLM exited; see ${OUTPUT_DIR}/agentdog_vllm.log" >&2
        exit 1
    }
    [ "${waited}" -lt "${STARTUP_TIMEOUT}" ] || {
        echo "AgentDoG vLLM was not ready within ${STARTUP_TIMEOUT}s" >&2
        exit 1
    }
    sleep 5
    waited=$((waited + 5))
done

echo "=== AgentDoG vLLM ready in ${waited}s"
FAILURES=()
for item in "${DATASETS[@]}"; do
    name="${item%%:*}"
    input_path="${item#*:}"
    output_path="${OUTPUT_DIR}/deepseek-v4-pro_opencode_${name}.jsonl"
    echo "=== deepseek-v4-pro :: opencode :: ${name}"
    args=(
        python entries/defense/agentdog_runtime_verification.py
        --framework opencode
        --model "${MODEL}"
        --sandbox apptainer
        --os linux
        --apptainer_path "${APPTAINER_PATH}"
        --image "${IMAGE}"
        --input_path "${input_path}"
        --output_path "${output_path}"
        --parallel "${PARALLEL}"
        --qps "${QPS}"
        --timeout "${TIMEOUT}"
        --agentdog_base_url "http://127.0.0.1:${PORT}/v1"
        --agentdog_model "${AGENTDOG_MODEL}"
        --agentdog_timeout "${AGENTDOG_TIMEOUT}"
        --skip_exist_traceid
    )
    if [ "${LIMIT}" -gt 0 ]; then
        args+=(--limit "${LIMIT}")
    fi
    set +e
    "${args[@]}"
    status=$?
    set -e
    if [ "${status}" -ne 0 ]; then
        FAILURES+=("${name} (exit ${status})")
        continue
    fi
    if [ "${LIMIT}" -gt 0 ]; then
        count="$(python -c 'import json, sys; rows=[json.loads(line) for line in open(sys.argv[1], encoding="utf-8") if line.strip()]; print(len({row["traceid"] for row in rows}))' "${output_path}")"
        if [ "${count}" -ne "${LIMIT}" ]; then
            FAILURES+=("${name} (${count}/${LIMIT} unique results)")
        fi
    fi
done

if [ "${#FAILURES[@]}" -gt 0 ]; then
    printf 'FAILED: %s\n' "${FAILURES[@]}" >&2
    exit 1
fi
