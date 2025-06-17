from src.utils.test_utils import load_environment, load_agent, load_attack
from src.attack.injection import AttackAgent
import json
from typing import Optional
from tqdm import tqdm


tasks_path = "data/tasks/tasks.json"
attack_tasks_path = "data/tasks/attack_tasks.json"


def test(index: int, model: str, log_dir: Optional[str] = None):
    with open(tasks_path, 'r') as file:
        tasks = json.load(file)
        task = tasks[index]
    # print(json.dumps(task, indent=4))
    prompt = task['prompt']
    agent = load_agent(task, model)
    load_environment(task)
    response = agent.run(prompt)
    print(json.dumps(response, indent=4))
    if log_dir is not None:
        with open(log_dir, 'a') as file:
            file.write(json.dumps(response) + '\n')


def test_attack(index: int, model: str, log_dir: Optional[str] = None) -> None:
    with open(attack_tasks_path, 'r') as file:
        attack_tasks = json.load(file)
        attack_task = attack_tasks[index]
    with open(tasks_path, 'r') as file:
        tasks = json.load(file)
        task = tasks[attack_task["target_index"]]
    attack_agent = AttackAgent()
    agent = load_agent(task, model)
    load_attack(attack_agent, attack_task)
    load_environment(task)
    response = agent.run(task["prompt"])
    print(json.dumps(response, indent=4))
    attack_agent.rollback()
    if log_dir is not None:
        with open(log_dir, 'a') as file:
            file.write(json.dumps(response) + '\n')


def test_all(model: str, log_dir: Optional[str] = None, start_index: int = 0):
    with open(tasks_path, 'r') as file:
        tasks = json.load(file)
    for index, _ in tqdm(enumerate(tasks[start_index:])):
        test(index, model, log_dir)


def test_all_attacks(model: str, log_dir: Optional[str] = None, start_index: int = 0):
    with open(attack_tasks_path, 'r') as file:
        attack_tasks = json.load(file)
    for index, _ in tqdm(enumerate(attack_tasks[start_index:])):
        test_attack(index, model, log_dir)


if __name__ == '__main__':
    # test(
    #     index = 42,
    #     model = "zhipu/glm-4-flash",
    #     log_dir='data/logs/glm-4-flash.jsonl',
    # )

    # test_attack(
    #     index = 42,
    #     model = "zhipu/glm-4-flash",
    #     log_dir='data/logs/glm-4-flash.jsonl',
    # )

    test_all(
        model='zhipu/glm-4-flash', 
        log_dir='data/logs/glm-4-flash.jsonl',
        start_index=0
    )

    test_all_attacks(
        model='zhipu/glm-4-flash', 
        log_dir='data/attacked/glm-4-flash.jsonl',
        start_index=0
    )

