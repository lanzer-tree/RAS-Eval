# Specification-based Security Evaluation of Real-World Agents Tool-Calling under Long-Horizon Context Tasks

## Prerequisites

- [uv](https://docs.astral.sh/uv/) — Python environment and dependency management.
- A sandbox runtime, **install one of**:
  - [Docker](https://www.docker.com/)
  - [Apptainer](https://apptainer.org/)

## Image Build

build one of docker image and apptainer image

### Docker Image Build

```bash
cd docker
```

linux/amd64：

```bash
bash build.sh                
```

linux/mac/arm64：

```bash
PLATFORM=linux/arm64 IMAGE_TAG=ras-eval-arm:latest bash build.sh
```

### Apptainer Image Build

```bash
cd docker
```

linux/amd64：

```bash
EXPORT_TAR=1 bash build.sh
```

linux/mac/arm64：

```bash
EXPORT_TAR=1 PLATFORM=linux/arm64 IMAGE_TAG=ras-eval-arm:latest bash build.sh
```

## Environment Setup

Create `.env` in the repository root:

```bash
# LLM inference endpoint (OpenAI Chat-Completion)
OPENAI_API_KEY="sk-xxx"
OPENAI_BASE_URL="https://..."

# toolkit APIs (required by evaluation tasks)
AMAP_KEY="xxx"            # Amap - https://lbs.amap.com/
TAVILY_API_KEY="xxx"      # Tavily - https://www.tavily.com/
TUSHARE_TOKEN="xxx"       # Tushare - https://tushare.pro/
```

Install Python dependencies:

```bash
uv sync
```

## Run Evaluation

`entries/runtime_verification.py` runs the agent under test and checks the LTL specifications with nuXmv after every tool call.

**Docker**

```bash
uv run entries/runtime_verification.py \
    --input_path data/input/ras_eval_toma.jsonl \
    --output_path data/output/deepseek-v4-pro/toma_opencode.jsonl \
    --framework opencode \
    --model provider/deepseek-v4-pro \
    --api_key sk-xxx \
    --base_url https://... \
    --sandbox docker \
    --os mac \
    --image ras-eval-arm:latest \
    --parallel 2 \
    --qps 1.0 \
    --request_qps 1.0 \
    --request_max_retries 5 \
    --timeout 900 \
    --limit 5 \
    --skip_exist_traceid
```

**Apptainer**

```bash
uv run entries/runtime_verification.py \
    --input_path data/input/ras_eval_toma.jsonl \
    --output_path data/output/deepseek-v4-pro/toma_opencode.jsonl \
    --framework opencode \
    --model provider/deepseek-v4-pro \
    --sandbox apptainer \
    --os linux \
    --apptainer_path /usr/local/bin/apptainer \  # path to your installed apptainer
    --image docker/ras-eval-amd--latest.sif \ # path to your saved image
    --parallel 2 \
    --qps 1.0 \
    --request_qps 1.0 \
    --request_max_retries 5 \
    --timeout 900 \
    --limit 5 \
    --skip_exist_traceid
```

Parameter notes:
- `--framework`: `opencode` | `autogen` | `langchain` | `mcp` | `openai-agent` | `qwen-agent` | `hermes` | `openclaw` | `deepseek-harness` | `pi`.
- `--api_key` / `--base_url` are optional and fall back to `OPENAI_API_KEY` / `OPENAI_BASE_URL` in `.env`.
- `--limit N` caps the sample count; `--traceid ID` runs one sample instead.
- `--apptainer_path` is used only by the Apptainer backend.
- In `--model provider/deepseek-v4-pro`, `provider` is a placeholder — it can be any string (e.g. your actual provider name or an arbitrary prefix).

## Datset

Some names are different with the paper, the names will be fixed in the future:

**Indirect Prompt Injection**: data/input/ras_eval_toma.jsonl (toma)
**Tool Poisoning Attack**: data/input/ras_eval_tpa.jsonl (tpa)
**Skill Code Injection**: data/input/ras_eval_cia_skill.jsonl (cia)
**Tool Code Injection**: data/input/ras_eval_cia_tool.jsonl (cia_tool)

## Run Data Construction

### 1. Normal Task Generation


```bash
touch data/output/seed.jsonl       # empty seed for a fresh run

uv run entries/flywheel_infer.py \
    --task generate \
    --mode base \
    --framework opencode \
    --model provider/deepseek-v4-pro \
    --api_key sk-xxx \
    --base_url https://... \
    --input_path data/output/seed.jsonl \
    --output_dir data/output/flywheel-generate \
    --sandbox docker \
    --os mac \
    --image ras-eval-arm:latest \
    --depth 9 \
    --limit 50 \
    --max_per_toolkit 5 \
    --disable_native_tools \
    --parallel 8 \
    --qps 1.0 \
    --timeout 900
```

Output: `data/output/flywheel-generate/dataset/generated.jsonl`.

### 2. Specification Annotation
```bash
uv run entries/flywheel_infer.py \
    --task annotate \
    --mode base \
    --framework opencode \
    --benchmark ras-eval-next \
    --model provider/deepseek-v4-pro \
    --api_key sk-xxx \
    --base_url https://... \
    --input_path data/output/flywheel-generate/dataset/generated.jsonl \
    --output_dir data/output/flywheel-annotate \
    --sandbox docker \
    --os mac \
    --image ras-eval-arm:latest \
    --max_iterations 10 \
    --limit 50 \
    --disable_native_tools \
    --parallel 8 \
    --qps 1.0 \
    --timeout 3000 \
    --skip_exist_traceid
```

`--mode base` annotates completion + safety specs; `--mode attack` annotates security specs and requires `--benchmark agentdojo` or `skill_inject`. Output: `data/output/flywheel-annotate/dataset/annotated.jsonl`.

### 3. Attack Task Generation 

```bash
uv run entries/flywheel_infer.py \
    --task generate \
    --mode attack \
    --framework opencode \
    --attack_type toma \
    --attack_model provider/deepseek-v4-pro \
    --target_model provider/deepseek-v4-pro \
    --api_key sk-xxx --base_url https://... \
    --target_llm_api_key sk-xxx \
    --target_llm_base_url https://... \
    --input_path data/output/flywheel-annotate/dataset/annotated.jsonl \
    --output_dir data/output/flywheel-attack \
    --sandbox docker \
    --os mac \
    --image ras-eval-arm:latest \
    --number_target_tool 1 \
    --max_iterations 6 \
    --max_restart 3 \
    --limit 50 \
    --parallel 2 \
    --qps 1.0 \
    --timeout 1200 \
    --skip_exist_traceid
```

`--attack_type`: `toma` | `tpa` | `cia` | `cia-tool`. `--model` is the attack optimizer fallback when `--attack_model` is omitted. Security specs are drafted by the attack pipeline itself. Output: `data/output/flywheel-attack/dataset/attack_generated.jsonl` — this is the final dataset, ready to be fed to `entries/runtime_verification.py` as `--input_path` (see Run Evaluation).