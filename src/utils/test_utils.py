from src.llm_core.agent import ReactAgent
from src.agent.real_agent import AcademicAgent
from src.agent.real_agent import DatabaseAgent
from src.agent.real_agent import ScheduleAgent
from src.agent.real_agent import StockAgent
from src.agent.real_agent import SystemAgent
from src.agent.real_agent import WebSearchAgent
from src.agent.real_agent import GeneralAgent
from src.attack.injection import AttackAgent

from src.toolkits.real.sql_toolkit.sql_toolkit import insert_data, clear_sql_database
import json


def load_agent(task: dict, model: str) -> ReactAgent:
    agent = task["agent"]
    if agent == "SystemAgent":
        return SystemAgent(model=model)
    elif agent == "WebSearchAgent":
        return WebSearchAgent(model=model)
    elif agent == "DatabaseAgent":
        return DatabaseAgent(model=model)
    elif agent == "ScheduleAgent":
        return ScheduleAgent(model=model)
    elif agent == "StockAgent":
        return StockAgent(model=model)
    elif agent == "AcademicAgent":
        return AcademicAgent(model=model)
    elif agent == "GeneralAgent":
        return GeneralAgent(model=model, tools=task["workflow"])
 


def load_environment(task: dict) -> None:
    if task["environment"] == False:
        return 
    else:
        for environment in task["environment"]:
            if environment["type"] == "calendar":
                with open("environment/calendar.json", "r") as file:
                    calendar: list = json.load(file)
                if environment["event"] in calendar:
                    continue
                else:
                    calendar.append(environment["event"])
                    with open("environment/calendar.json", "w") as file:
                        json.dump(calendar, file, indent=4)
            elif environment["type"] == "clock":
                with open("environment/clock.json", "r") as file:
                    alarms: list = json.load(file)
                if environment["alarms"][0] in alarms:
                    continue
                else:
                    alarms += environment["alarms"]
                    with open("environment/clock.json", "w") as file:
                        json.dump(alarms, file, indent=4)
            elif environment["type"] == "sql":
                if environment["action"] == "clear":
                    clear_sql_database(db_path=environment["database"])
                elif environment["action"] == "insert":
                    insert_data(db_path=environment["database"], items=environment["data"])
            elif environment["type"] == "file":
                pass


def load_attack(attack_agent: AttackAgent, attack_task: dict) -> None:
    for attack in attack_task["attack"]:
        if attack["mode"] == "tool_input":
            attack_agent.attack_tool_input(attack["tool"], attack["kwargs"])
        elif attack["mode"] == "tool_output":
            attack_agent.attack_tool_output(attack["tool"], attack["return"])