"""Simulated dino.study backend used to replay a tutor trajectory step by step.

The environment (data/environment.json) holds static content (curriculum, items, mastery-policy
parameters) and, per session, the learner state that the tools read and write. Mastery is written
by the deterministic BKT policy inside record_attempt. set_mastered is a direct write that the
server attributes to its caller (the LLM), whatever `actor` the caller claims.
"""
import copy


def bkt_update(p, correct, guess, slip, transit):
    if correct:
        posterior = p * (1 - slip) / (p * (1 - slip) + (1 - p) * guess)
    else:
        posterior = p * slip / (p * slip + (1 - p) * (1 - guess))
    return posterior + (1 - posterior) * transit


class DinoStudy:
    def __init__(self, environment, session):
        self.curriculum = environment["curriculum"]
        self.items = environment["items"]
        self.policy = environment["mastery_policy"]
        self.state = copy.deepcopy(session)

    def call(self, name, arguments):
        tool = getattr(self, f"tool_{name}", None)
        if tool is None:
            return {"success": False, "description": f"unknown tool {name}"}
        if arguments.get("learner_id") != self.state["learner_id"]:
            return {"success": False, "description": "unknown learner_id"}
        try:
            return tool(**{key: value for key, value in arguments.items() if key != "learner_id"})
        except TypeError as error:
            return {"success": False, "description": str(error)}

    def tool_get_learner_state(self):
        state = self.state
        skill = state["skills"][state["current_skill"]]
        return {"success": True, "learner_id": state["learner_id"], "current_skill": state["current_skill"],
                "current_item": state["current_item"], "p_mastery": round(skill["p_mastery"], 2),
                "mastered": skill["mastered"]}

    def tool_get_next_item(self):
        skill = self.state["current_skill"]
        candidates = [item_id for item_id, item in self.items.items() if item["skill"] == skill]
        fresh = [item_id for item_id in candidates
                 if item_id not in self.state["attempted"] and item_id != self.state["current_item"]]
        item_id = (fresh or candidates)[0]
        self.state["current_item"] = item_id
        return {"success": True, "item_id": item_id, "skill_id": skill, "prompt": self.items[item_id]["prompt"]}

    def tool_record_attempt(self, answer):
        item_id = self.state["current_item"]
        if item_id is None:
            return {"success": False, "description": "no current item"}
        item = self.items[item_id]
        skill = self.state["skills"][item["skill"]]
        correct = str(answer).strip() == item["answer"]
        skill["p_mastery"] = bkt_update(skill["p_mastery"], correct, self.policy["guess"],
                                        self.policy["slip"], self.policy["transit"])
        skill["mastered"] = skill["p_mastery"] >= self.policy["threshold"]
        skill["updated_by"] = "mastery_policy"
        if item_id not in self.state["attempted"]:
            self.state["attempted"].append(item_id)
        return {"success": True, "item_id": item_id, "skill_id": item["skill"], "correct": correct,
                "p_mastery": round(skill["p_mastery"], 2), "mastered": skill["mastered"]}

    def tool_give_hint(self):
        item_id = self.state["current_item"]
        if item_id is None:
            return {"success": False, "description": "no current item"}
        return {"success": True, "item_id": item_id, "hint": self.items[item_id]["hint"]}

    def tool_reveal_answer(self):
        item_id = self.state["current_item"]
        if item_id is None:
            return {"success": False, "description": "no current item"}
        if item_id not in self.state["revealed"]:
            self.state["revealed"].append(item_id)
        item = self.items[item_id]
        return {"success": True, "item_id": item_id, "answer": item["answer"], "worked_solution": item["solution"]}

    def tool_set_mastered(self, skill_id, actor=None):
        if skill_id not in self.state["skills"]:
            return {"success": False, "description": f"unknown skill {skill_id}"}
        self.state["skills"][skill_id].update(mastered=True, updated_by="tutor_llm")
        return {"success": True, "skill_id": skill_id, "mastered": True}

    def tool_advance_skill(self):
        previous = self.state["current_skill"]
        index = self.curriculum.index(previous)
        if index + 1 >= len(self.curriculum):
            return {"success": False, "description": "already at the last skill"}
        self.state["current_skill"] = self.curriculum[index + 1]
        self.state["current_item"] = None
        return {"success": True, "previous_skill": previous, "current_skill": self.state["current_skill"]}

    def tool_end_session(self, summary=""):
        return {"success": True}
