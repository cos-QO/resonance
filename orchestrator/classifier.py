"""
Classify a Linear issue into a task type using its labels.
Returns (task_type, task_config) or raises ValueError for unsupported types.

'plan' is checked first — plan issues are routed to the Planning Agent,
not the normal execution path.
"""
from .config import Config


def classify(issue: dict, config: Config) -> tuple[str, dict]:
    """
    Match issue labels against WORKFLOW.md task_types.
    Priority order: pep → plan → all other task types.
    Raises ValueError if no task type matches.
    """
    label_names = {lbl["name"].lower() for lbl in issue.get("labels", {}).get("nodes", [])}

    # PEP issues route to the PEP Reader Agent (highest priority)
    pep_cfg = config.workflow.get("task_types", {}).get("pep")
    if pep_cfg:
        pep_requires = {l.lower() for l in pep_cfg.get("detection", {}).get("labels", ["pep"])}
        if pep_requires.issubset(label_names):
            return "pep", {**pep_cfg, "_name": "pep"}

    # Core Plan issues route to the Block Decomposer Agent
    core_plan_cfg = config.workflow.get("task_types", {}).get("core_plan")
    if core_plan_cfg:
        cp_requires = {l.lower() for l in core_plan_cfg.get("detection", {}).get("labels", ["core-plan"])}
        if cp_requires.issubset(label_names):
            return "core_plan", {**core_plan_cfg, "_name": "core_plan"}

    # Block issues route to the Execution Agent
    block_cfg = config.workflow.get("task_types", {}).get("block")
    if block_cfg:
        block_requires = {l.lower() for l in block_cfg.get("detection", {}).get("labels", ["block"])}
        if block_requires.issubset(label_names):
            return "block", {**block_cfg, "_name": "block"}

    # Plan issues route to the Planning Agent (legacy)
    plan_cfg = config.workflow.get("task_types", {}).get("plan")
    if plan_cfg:
        plan_requires = {l.lower() for l in plan_cfg.get("detection", {}).get("labels", ["plan"])}
        if plan_requires.issubset(label_names):
            return "plan", {**plan_cfg, "_name": "plan"}

    for task_type, task_cfg in config.workflow["task_types"].items():
        if task_type == "plan":
            continue
        detection = task_cfg.get("detection", {})
        requires  = {l.lower() for l in detection.get("labels", [])}
        excludes  = {l.lower() for l in detection.get("excludes", [])}

        if not requires.issubset(label_names):
            continue
        if excludes & label_names:
            continue

        return task_type, {**task_cfg, "_name": task_type}

    raise ValueError(
        f"No task type matched labels {label_names} for issue {issue.get('identifier', issue['id'])}"
    )
