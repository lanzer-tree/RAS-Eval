import os
from argparse import ArgumentParser
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

def main():
    parser = ArgumentParser()
    parser.add_argument(
        "--input_path",
        type=Path,
        help="Input jsonl file path",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        help="Output directory",
    )
    parser.add_argument(
        "--task",
        type=str,
        choices=["generate", "refine", "annotate"],
        help="generate refers to generate data/environment/attacks. refine refers to repairing or optimizing an existing data/environment/attacks",
    )
    parser.add_argument(
        "--mode",
        type=str,
        choices=["base", "attack"],
        help="base refers to repairing/generating basic data and environment. attack refers to optimizing/generating injection attacks",
    )
    parser.add_argument(
        "--framework",
        type=str,
        choices=["opencode"],
        help="LLM agent framework",
    )
    parser.add_argument(
        "--benchmark",
        type=str,
        choices=["ras-eval-next", "agentdojo", "skill_inject"],
        default="ras-eval-next",
        help="Benchmark the samples come from (task=annotate)",
    )
    parser.add_argument(
        "--model",
        type=str,
        help="LLM model name (attack model for task=refine mode=attack)",
    )
    parser.add_argument(
        "--attack_model",
        type=str,
        default=None,
        help="Attack optimizer model name, format provider/model (defaults to --model)",
    )
    parser.add_argument(
        "--target_model",
        type=str,
        help="Target model name",
    )
    parser.add_argument(
        "--parallel",
        type=int,
        default=1,
        help="The maximum number of parallel running tasks",
    )
    parser.add_argument(
        "--qps",
        type=float,
        default=1.0,
        help="The qps limit of LLM API",
    )
    parser.add_argument(
        "--traceid",
        type=int,
        default=None,
        help="The selected traceid",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=900,
        help="Timeout seconds for one opencode run",
    )
    parser.add_argument(
        "--skip_exist_traceid",
        action="store_true",
        help="Skip exist traceid",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=None,
        help="Tool combination depth k (required for task=generate)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Max number of samples to add this run (task=generate)",
    )
    parser.add_argument(
        "--max_per_toolkit",
        type=int,
        default=None,
        help="Max number of samples to generate per toolkit (task=generate)",
    )
    parser.add_argument(
        "--disable_native_tools",
        action="store_true",
        help="Disable opencode built-in tools during generation inference (task=generate)",
    )
    parser.add_argument(
        "--number_target_tool",
        "--number-target-tool",
        dest="number_target_tool",
        type=int,
        default=1,
        help="Number of MCP target tools AttackAgent must choose for each attack-generation sample",
    )
    parser.add_argument(
        "--max_iterations",
        type=int,
        default=3,
        help="Max attack-refine rewrite attempts per failed sample",
    )
    parser.add_argument(
        "--max_restart",
        type=int,
        default=3,
        help="Max security-spec restarts per sample; each restart gets --max_iterations attempts (task=generate mode=attack, toma/tpa)",
    )
    parser.add_argument(
        "--sandbox",
        type=str,
        choices=["docker", "apptainer"],
        default="docker",
        help="The type of sandbox",
    )
    parser.add_argument(
        "--os",
        type=str,
        choices=["mac", "linux"],
        default="linux",
        help="Host OS (apptainer runs inside a lima VM on mac)",
    )
    parser.add_argument(
        "--apptainer_path",
        type=str,
        default=None,
        help="The path of apptainer executable (linux apptainer sandbox)",
    )
    parser.add_argument(
        "--image",
        type=str,
        default=None,
        help="The path of the apptainer image",
    )
    parser.add_argument(
        "--api_key",
        type=str,
        default=None,
        help="The api key of LLM (falls back to OPENAI_API_KEY in .env)",
    )
    parser.add_argument(
        "--base_url",
        type=str,
        default=None,
        help="The base url of the api (falls back to OPENAI_BASE_URL in .env)",
    )
    parser.add_argument(
        "--target_llm_api_key",
        type=str,
        default=None,
        help="The api key of LLM (falls back to OPENAI_API_KEY in .env)",
    )
    parser.add_argument(
        "--target_llm_base_url",
        type=str,
        default=None,
        help="The base url of the api (falls back to OPENAI_BASE_URL in .env)",
    )
    parser.add_argument(
        "--attack_type",
        type=str,
        choices=["toma", "tpa", "eia", "cia", "cia-tool", ""],
        default="",
        help="The attack type (toma, tpa, eia, cia, cia-tool, or none)",
    )
    args = parser.parse_args()
    # CLI-provided credentials take precedence: downstream runners read
    # OPENAI_API_KEY / OPENAI_BASE_URL from the environment and only fall
    # back to .env for unset variables.
    if not (args.task == "refine" and args.mode == "attack"):
        if args.api_key:
            os.environ["OPENAI_API_KEY"] = args.api_key
        if args.base_url:
            os.environ["OPENAI_BASE_URL"] = args.base_url

    if args.task == "refine" and args.mode == "base":
        from src.indra.refine.executor import RefineConfig
        from src.indra.refine.runner import run_refine

        config = RefineConfig(
            input_path=args.input_path,
            output_dir=args.output_dir,
            model=args.model,
            sandbox=args.sandbox,
            os=args.os,
            parallel=args.parallel,
            qps=args.qps,
            traceid=args.traceid,
            timeout=args.timeout,
            skip_exist_traceid=args.skip_exist_traceid,
            apptainer_path=args.apptainer_path,
            image=args.image,
            # The base pipeline validates that a task is solvable through its MCP
            # tools alone, so opencode's native tools stay denied.
            disable_native_tools=True,
        )
        results = run_refine(config)
        print(f"Refined {len(results)} sample(s). Output: {config.output_dir / 'dataset' / 'refined.jsonl'}")
    elif args.task == "refine" and args.mode == "attack":
        from src.indra.refine.attack_runner import AttackRefineConfig, run_attack_refine

        attack_model = args.attack_model or args.model
        target_model = args.target_model or args.model
        if not attack_model:
            parser.error("--model or --attack_model is required for task=refine mode=attack")
        if not target_model:
            parser.error("--target_model is required for task=refine mode=attack when --model is not provided")
        config = AttackRefineConfig(
            input_path=args.input_path,
            output_dir=args.output_dir,
            attack_model=attack_model,
            target_model=target_model,
            sandbox=args.sandbox,
            os=args.os,
            parallel=args.parallel,
            qps=args.qps,
            traceid=args.traceid,
            timeout=args.timeout,
            skip_exist_traceid=args.skip_exist_traceid,
            apptainer_path=args.apptainer_path,
            image=args.image,
            max_iterations=args.max_iterations,
            attack_type=args.attack_type,
            attack_api_key=args.api_key,
            attack_base_url=args.base_url,
            target_api_key=args.target_llm_api_key,
            target_base_url=args.target_llm_base_url,
        )
        results = run_attack_refine(config)
        print(f"Attack-refined {len(results)} sample(s). Output: {config.output_dir / 'dataset' / 'attack_refined.jsonl'}")
    elif args.task == "generate" and args.mode == "attack":
        from src.indra.generate import AttackGenerateConfig, run_attack_generate

        attack_model = args.attack_model or args.model
        target_model = args.target_model or args.model
        if not attack_model:
            parser.error("--model or --attack_model is required for task=generate mode=attack")
        if not target_model:
            parser.error("--target_model is required for task=generate mode=attack when --model is not provided")
        if args.attack_type not in {"toma", "tpa", "eia", "cia", "cia-tool"}:
            parser.error("--attack_type toma, --attack_type tpa, --attack_type eia, --attack_type cia, or --attack_type cia-tool is required for task=generate mode=attack")
        if args.number_target_tool < 1:
            parser.error("--number_target_tool must be >= 1")
        config = AttackGenerateConfig(
            input_path=args.input_path,
            output_dir=args.output_dir,
            attack_model=attack_model,
            target_model=target_model,
            sandbox=args.sandbox,
            os=args.os,
            parallel=args.parallel,
            qps=args.qps,
            traceid=args.traceid,
            timeout=args.timeout,
            skip_exist_traceid=args.skip_exist_traceid,
            apptainer_path=args.apptainer_path,
            image=args.image,
            max_iterations=args.max_iterations,
            max_restart=args.max_restart,
            number_target_tool=args.number_target_tool,
            attack_type=args.attack_type,
            limit=args.limit,
            attack_api_key=args.api_key,
            attack_base_url=args.base_url,
            target_api_key=args.target_llm_api_key,
            target_base_url=args.target_llm_base_url,
        )
        results = run_attack_generate(config)
        print(f"Attack-generated {len(results)} sample(s). Output: {config.output_dir / 'dataset' / 'attack_generated.jsonl'}")
    elif args.task == "generate" and args.mode == "base":
        if args.depth is None:
            parser.error("--depth is required for task=generate")
        from src.indra.generate import GenerateConfig, run_generate

        config = GenerateConfig(
            input_path=args.input_path,
            output_dir=args.output_dir,
            model=args.model,
            sandbox=args.sandbox,
            os=args.os,
            depth=args.depth,
            limit=args.limit,
            max_per_toolkit=args.max_per_toolkit,
            disable_native_tools=args.disable_native_tools,
            parallel=args.parallel,
            qps=args.qps,
            timeout=args.timeout,
            apptainer_path=args.apptainer_path,
            image=args.image,
        )
        added = run_generate(config)
        print(f"Generated {added} sample(s). Output: {config.output_dir / 'dataset' / 'generated.jsonl'}")
    elif args.task == "annotate":
        from src.indra.annotator import AnnotateConfig, run_annotate

        # mode=base annotates completion + safety specs; mode=attack annotates the
        # security spec of an existing attack dataset. ras-eval-next security specs
        # are produced by the attack-generation pipeline instead.
        if args.mode == "attack" and args.benchmark == "ras-eval-next":
            parser.error("task=annotate mode=attack requires --benchmark agentdojo or skill_inject")
        config = AnnotateConfig(
            input_path=args.input_path,
            output_dir=args.output_dir,
            model=args.model,
            sandbox=args.sandbox,
            os=args.os,
            benchmark=args.benchmark,
            mode=args.mode,
            parallel=args.parallel,
            qps=args.qps,
            traceid=args.traceid,
            timeout=args.timeout,
            skip_exist_traceid=args.skip_exist_traceid,
            apptainer_path=args.apptainer_path,
            image=args.image,
            max_iterations=args.max_iterations,
            limit=args.limit,
            disable_native_tools=args.disable_native_tools,
        )
        results = run_annotate(config)
        print(f"Annotated {len(results)} sample(s). Output: {config.output_dir / 'dataset' / 'annotated.jsonl'}")
    else:
        raise NotImplementedError(f"task={args.task} mode={args.mode} is not yet implemented.")


if __name__ == "__main__":
    main()