"""dino.study environment observers for RAS-Eval specifications.

An observer is used inside a spec as `tool(<name>(<args>))[<field>]`, e.g.
`tool(mastered())[mastered] = TRUE`. It is a read-only function `(state, **kwargs) -> dict`
evaluated on the environment snapshot of every time step. OBSERVER_PARAMS lists the positional
parameter names, so `mastered('frac_add')` and `mastered(skill='frac_add')` are equivalent.
Returned fields should be flat str / int / float / bool values so they can be compared directly.
"""

OBSERVER_PARAMS = {
    "mastered": ["skill"],
    "attempted": ["item"],
    "revealed": ["item"],
    "learner": [],
}


def mastered(state, skill=None):
    """Mastery record of `skill` (default: the learner's current skill)."""
    skill = skill or state["current_skill"]
    record = state["skills"].get(skill)
    if record is None:
        return {"success": False, "description": f"unknown skill {skill}"}
    return {"success": True, "skill": skill, "mastered": record["mastered"],
            "p_mastery": round(record["p_mastery"], 2), "updated_by": record["updated_by"]}


def attempted(state, item=None):
    """Whether the learner has a recorded attempt on `item` (default: the current item)."""
    item = item or state["current_item"]
    return {"success": True, "item": item, "attempted": item in state["attempted"]}


def revealed(state, item=None):
    """Whether the full answer of `item` (default: the current item) has been shown."""
    item = item or state["current_item"]
    return {"success": True, "item": item, "revealed": item in state["revealed"]}


def learner(state):
    """Session-level state: learner id, current skill and current item."""
    return {"success": True, "learner_id": state["learner_id"],
            "current_skill": state["current_skill"], "current_item": state["current_item"]}


OBSERVERS = {"mastered": mastered, "attempted": attempted, "revealed": revealed, "learner": learner}
