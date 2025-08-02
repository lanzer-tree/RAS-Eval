from src.utils.eval_utils import (
    weakness_count,
    failure_mode_analysis,
    robustness_analysis_for_scenario,
    calculate_score,
    multi_failure_mode_analysis
)
from colorama import Fore


def main():
    task_path = "data/tasks/tasks.json"
    attacks_path = "data/tasks/attack_template.json"
    attack_tasks_path = "data/tasks/attack_tasks.json"
    asb_attacks_path = "data/tasks/asb_attack_template.json"
    asb_attack_tasks_path = "data/tasks/asb_attack_tasks.json"
    glm4_flash_response_path = "data/logs/glm-4-flash.jsonl"
    attacked_glm4_flash_response_path = "data/attacked/glm-4-flash.jsonl"
    response_paths = [
        glm4_flash_response_path,
        "data/logs/llama3.2-3b.jsonl",
        "data/logs/qwen-max.jsonl",
        "data/logs/qwen-plus.jsonl",
        "data/logs/qwen2.5-1.5b-instruct.jsonl",
        "data/logs/qwen2.5-7b-instruct.jsonl",
    ]
    print(f"{Fore.GREEN}Overview of vulnerabilities{Fore.RESET}")
    weakness_count(attacks_path, attack_tasks_path, asb_attacks_path, asb_attack_tasks_path)
    print(f"{Fore.GREEN}Distribution of Failure Modes{Fore.RESET}")
    multi_failure_mode_analysis(response_paths, task_path, attack_tasks_path)
    failure_mode_analysis(attacked_glm4_flash_response_path, task_path, attack_tasks_path, plot=True)
    print(f"{Fore.GREEN}Comparison of agent performance in different scenarios before and after attack{Fore.RESET}")
    robustness_analysis_for_scenario(glm4_flash_response_path, attacked_glm4_flash_response_path, task_path, attack_tasks_path)
    print(f"{Fore.GREEN}The average of different metrics for the agents driven by different backbone models without attacks{Fore.RESET}")
    calculate_score(response_paths, task_path, plot=True)


if __name__ == "__main__":
    main()