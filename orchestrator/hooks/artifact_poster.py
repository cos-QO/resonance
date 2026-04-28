"""
Hook: artifact_poster
Fires on SubagentStop. If the run state has new artifacts that haven't
been posted to Linear yet, posts them as a comment.

Requires LINEAR_API_KEY and ISSUE_ID environment variables.
"""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator import state as run_state
from orchestrator.events import write as write_event


def main() -> int:
    payload_raw = sys.stdin.read().strip()
    if not payload_raw:
        return 0

    try:
        payload = json.loads(payload_raw)
    except json.JSONDecodeError:
        return 0

    if payload.get("hook_type") != "SubagentStop":
        return 0

    issue_id = os.environ.get("ISSUE_ID")
    if not issue_id:
        return 0

    run = run_state.get_run(issue_id)
    if not run:
        return 0

    artifacts = run.get("artifacts", {})
    posted = run.get("_artifacts_posted", {})

    new_artifacts = {k: v for k, v in artifacts.items() if k not in posted}
    if not new_artifacts:
        return 0

    api_key = os.environ.get("LINEAR_API_KEY")
    if not api_key:
        return 0

    # Post to Linear — import here to avoid circular dependency at module load
    try:
        from orchestrator.linear_client import LinearClient
        client = LinearClient(api_key)

        linear_uuid = run.get("linear_uuid")
        if not linear_uuid:
            return 0

        lines = ["🔧 New artifacts available:", ""]
        for key, value in new_artifacts.items():
            lines.append(f"- **{key}**: {value}")
        client.post_comment(linear_uuid, "\n".join(lines))
        client.close()

        # Mark as posted
        posted.update(new_artifacts)
        run_state.update_run(issue_id, _artifacts_posted=posted)
        write_event(issue_id, "artifacts_posted", artifacts=list(new_artifacts.keys()))
    except Exception as e:
        # Non-fatal — just log
        write_event(issue_id, "artifact_post_failed", error=str(e))

    return 0


if __name__ == "__main__":
    sys.exit(main())
