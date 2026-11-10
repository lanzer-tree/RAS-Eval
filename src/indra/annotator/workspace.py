"""Resource workspace management for the flywheel annotate (SpecAgent) pipeline.

Copies toolkits, environment data and the new-generation LTL verifier from the
repository into an isolated output directory so that sandbox mounts and
iterative verifier edits never touch the original sources. The old dataset's
``meta["specifications"]`` and the legacy verifier are deliberately NOT copied,
keeping the new annotation logic free of old-logic pollution.
"""
from __future__ import annotations

import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
TOOLKITS_SRC = REPO_ROOT / "src" / "toolkits" / "ras_eval"
AGENTDOJO_TOOLKITS_SRC = REPO_ROOT / "src" / "toolkits" / "agentdojo"
ENVIRONMENT_SRC = REPO_ROOT / "data" / "ras_eval" / "environment"
# VERIFIER_SRC = REPO_ROOT / "workspace" / "xmv_verifier" / "src" / "verifier.py"
VERIFIER_SRC = REPO_ROOT / "src" / "indra" / "annotator" / "verifier.py"
VERIFY_CLI_SRC = REPO_ROOT / "src" / "indra" / "annotator" / "verify_cli.py"
# SPEC_DOC_SRC = REPO_ROOT / "doc" / "agent_ltl_specification.md"
SPEC_DOC_SRC = REPO_ROOT / "src" / "indra" / "prompts" / "agent_ltl_specification.md"
NATIVE_TOOLS_DOC_SRC = REPO_ROOT / "src" / "indra" / "prompts" / "opencode_native_tools.md"
# AgentDojo's official rule-based checks: the SpecAgent reads them as the
# authoritative definition of task completion / attack success.
AGENTDOJO_OFFICIAL_SRC = {
    "utility_evaluator.py": REPO_ROOT / "src" / "evaluator" / "agentdojo" / "utility" / "evaluator.py",
    "attack_evaluator.py": REPO_ROOT / "src" / "evaluator" / "agentdojo" / "attack" / "evaluator.py",
}


def ensure_annotate_workspace(output_dir: Path, benchmark: str = "ras-eval-next") -> None:
    """Idempotently initialize the workspace under *output_dir*.

    Creates:
      {output_dir}/toolkits/    -- full copy of the benchmark's toolkit sources
                                   (skill_inject has none: its skills live in
                                   each sample's sandbox)
      {output_dir}/environment/ -- full copy of data/ras_eval/environment/
                                   (ras-eval-next only; AgentDojo environments
                                   are dumped per sample by its MCP server and
                                   skill_inject seeds a sandbox per sample)
      {output_dir}/official/    -- official evaluation sources (agentdojo only)
      {output_dir}/verifier/    -- verifier.py + verify.py CLI + LTL spec doc
      {output_dir}/dataset/     -- annotated/failed output JSONL
      {output_dir}/traces/      -- per-sample checkpoints (trajectory, env, agent)
    """
    output_dir = Path(output_dir)
    toolkits_dst = output_dir / "toolkits"
    environment_dst = output_dir / "environment"
    verifier_dst = output_dir / "verifier"

    if benchmark != "skill_inject" and not toolkits_dst.exists():
        shutil.copytree(AGENTDOJO_TOOLKITS_SRC if benchmark == "agentdojo" else TOOLKITS_SRC, toolkits_dst)

    if benchmark == "ras-eval-next" and not environment_dst.exists():
        shutil.copytree(ENVIRONMENT_SRC, environment_dst)

    if benchmark == "agentdojo":
        official_dst = output_dir / "official"
        official_dst.mkdir(parents=True, exist_ok=True)
        for name, source in AGENTDOJO_OFFICIAL_SRC.items():
            shutil.copy(source, official_dst / name)

    if not verifier_dst.exists():
        verifier_dst.mkdir(parents=True)
        shutil.copy(VERIFIER_SRC, verifier_dst / "verifier.py")
        shutil.copy(VERIFY_CLI_SRC, verifier_dst / "verify.py")
        shutil.copy(SPEC_DOC_SRC, verifier_dst / "agent_ltl_specification.md")
    # Reference doc added later than the first workspaces -- backfill if absent.
    if not (verifier_dst / "opencode_native_tools.md").exists():
        shutil.copy(NATIVE_TOOLS_DOC_SRC, verifier_dst / "opencode_native_tools.md")

    (output_dir / "dataset").mkdir(parents=True, exist_ok=True)
    (output_dir / "traces").mkdir(parents=True, exist_ok=True)
