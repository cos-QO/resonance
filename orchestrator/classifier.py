"""
Classify a Linear issue into a task type using its labels.
Returns (task_type, task_config) or raises ValueError for unsupported types.
"""
from .config import Config


def classify(issue: dict, config: Config) -> tuple[str, dict]:
    """
    Match issue labels against WORKFLOW.md task_types.
    Raises ValueError if no task type matches.
    """
    label_names = {lbl["name"].lower() for lbl in issue.get("labels", {}).get("nodes", [])}

    for task_type, task_cfg in config.workflow["task_types"].items():
        detection = task_cfg.get("detection", {})
        requires = {l.lower() for l in detection.get("labels", [])}
        excludes = {l.lower() for l in detection.get("excludes", [])}

        if not requires.issubset(label_names):
            continue
        if excludes & label_names:
            continue

        return task_type, task_cfg

    raise ValueError(
        f"No task type matched labels {label_names} for issue {issue.get('identifier', issue['id'])}"
    )
