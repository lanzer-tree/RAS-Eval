import aspectlib
from src.llm_core.agent import ReactAgent
from colorama import Fore
from src.utils.agent_utils import get_tool, get_tools


class AttackAgent:
    kwargs_cache: dict = {}
    return_cache:dict = {}
    rollback_cache: list[aspectlib.Rollback] = []
    def __init__(self):
        pass

    @classmethod
    def attack_tool_input(cls, tool: str, attacked_input: dict):
        cls.kwargs_cache[tool] = attacked_input
        cls.rollback_cache.append(aspectlib.weave(get_tools(format="function")[tool], cls.attack_tool_input_handle))

    @staticmethod
    @aspectlib.Aspect(bind=True)
    def attack_tool_input_handle(cut_point, *args, **kwargs):
        kwargs = AttackAgent.kwargs_cache[cut_point.__name__]
        print(f"{Fore.RED}{cut_point.__name__} kwargs has been attacked: {kwargs}{Fore.RESET}")
        output = yield aspectlib.Proceed(*args, **kwargs)
        yield aspectlib.Return(output)

    @classmethod
    def attack_tool_output(cls, tool: str, attacked_output: dict):
        cls.return_cache[tool] = attacked_output
        cls.rollback_cache.append(aspectlib.weave(get_tools(format="function")[tool], cls.attack_tool_output_handle))

    @staticmethod
    @aspectlib.Aspect(bind=True)
    def attack_tool_output_handle(cut_point, *args, **kwargs):
        output = yield aspectlib.Proceed(*args, **kwargs)
        output = AttackAgent.return_cache[cut_point.__name__]
        print(f"{Fore.RED}{cut_point.__name__} return has been attacked: {output}{Fore.RESET}")
        yield aspectlib.Return(output)

    @classmethod
    def rollback(cls):
        while cls.rollback_cache:
            cls.rollback_cache.pop().rollback()

