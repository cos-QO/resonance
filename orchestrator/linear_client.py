"""
Linear GraphQL API client.
All state transitions and comments flow through here.
Uses httpx for sync HTTP (orchestrator is single-threaded at the network layer).
"""
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

LINEAR_API = "https://api.linear.app/graphql"

# Required workflow states and their Linear state types
REQUIRED_STATES = [
    {"name": "Plan Approved",         "color": "#4CAF50", "type": "unstarted"},
    {"name": "In Progress",           "color": "#2196F3", "type": "started"},
    {"name": "Agent Feedback Needed", "color": "#FF9800", "type": "started"},
    {"name": "Human Review",          "color": "#9C27B0", "type": "started"},
]

# Required issue labels
REQUIRED_LABELS = [
    {"name": "design",    "color": "#F06292"},
    {"name": "frontend",  "color": "#4FC3F7"},
    {"name": "bug",       "color": "#EF5350"},
]


class LinearClient:
    def __init__(self, api_key: str):
        self._headers = {
            "Authorization": api_key,
            "Content-Type": "application/json",
        }
        self._client = httpx.Client(headers=self._headers, timeout=30)
        self._state_cache: dict[str, str] = {}  # name → id

    def _query(self, query: str, variables: Optional[dict] = None) -> dict:
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        resp = self._client.post(LINEAR_API, json=payload)
        resp.raise_for_status()
        body = resp.json()
        if "errors" in body:
            raise RuntimeError(f"Linear GraphQL error: {body['errors']}")
        return body["data"]

    # ── Auth / viewer ─────────────────────────────────────────────────────────

    def get_viewer(self) -> dict:
        """Validate API key and return the authenticated user."""
        data = self._query("query { viewer { id name email } }")
        return data["viewer"]

    # ── Projects ──────────────────────────────────────────────────────────────

    def get_projects(self) -> list[dict]:
        """List all projects the API key has access to."""
        data = self._query(
            """
            query {
              projects(first: 50) {
                nodes { id name identifier }
              }
            }
            """
        )
        return data["projects"]["nodes"]

    def get_project(self, project_id: str) -> Optional[dict]:
        """Get a project with its associated teams."""
        data = self._query(
            """
            query Project($id: String!) {
              project(id: $id) {
                id
                name
                identifier
                teams { nodes { id name } }
              }
            }
            """,
            {"id": project_id},
        )
        return data.get("project")

    # ── Issues ────────────────────────────────────────────────────────────────

    def get_eligible_issues(self, project_id: str, state_name: str) -> list[dict]:
        """Return all issues in the project that are in `state_name`."""
        data = self._query(
            """
            query EligibleIssues($projectId: String!, $stateName: String!) {
              issues(
                filter: {
                  project: { id: { eq: $projectId } }
                  state: { name: { eq: $stateName } }
                }
                first: 50
              ) {
                nodes {
                  id
                  identifier
                  title
                  description
                  state { id name }
                  labels { nodes { id name } }
                  team { id name }
                  assignee { id name }
                  url
                }
              }
            }
            """,
            {"projectId": project_id, "stateName": state_name},
        )
        return data["issues"]["nodes"]

    def get_issue(self, issue_id: str) -> Optional[dict]:
        data = self._query(
            """
            query Issue($id: String!) {
              issue(id: $id) {
                id
                identifier
                title
                description
                state { id name }
                labels { nodes { id name } }
                team { id name }
                url
              }
            }
            """,
            {"id": issue_id},
        )
        return data.get("issue")

    # ── State transitions ─────────────────────────────────────────────────────

    def get_state_id(self, team_id: str, state_name: str) -> str:
        """Resolve a state name to its ID, with team-scoped caching."""
        cache_key = f"{team_id}:{state_name}"
        if cache_key not in self._state_cache:
            data = self._query(
                """
                query TeamStates($teamId: String!) {
                  team(id: $teamId) {
                    states { nodes { id name } }
                  }
                }
                """,
                {"teamId": team_id},
            )
            for s in data["team"]["states"]["nodes"]:
                self._state_cache[f"{team_id}:{s['name']}"] = s["id"]
        if cache_key not in self._state_cache:
            raise ValueError(f"State '{state_name}' not found in team {team_id}")
        return self._state_cache[cache_key]

    def get_team_states(self, team_id: str) -> list[dict]:
        data = self._query(
            """
            query TeamStates($teamId: String!) {
              team(id: $teamId) {
                states { nodes { id name type } }
              }
            }
            """,
            {"teamId": team_id},
        )
        return data["team"]["states"]["nodes"]

    def set_issue_state(self, issue_id: str, team_id: str, state_name: str) -> None:
        state_id = self.get_state_id(team_id, state_name)
        self._query(
            """
            mutation SetState($issueId: String!, $stateId: String!) {
              issueUpdate(id: $issueId, input: { stateId: $stateId }) {
                success
                issue { id state { name } }
              }
            }
            """,
            {"issueId": issue_id, "stateId": state_id},
        )
        logger.info("issue=%s state→%s", issue_id, state_name)

    def create_state(self, team_id: str, name: str, color: str, state_type: str) -> dict:
        data = self._query(
            """
            mutation CreateState($teamId: String!, $name: String!, $color: String!, $type: String!) {
              workflowStateCreate(input: {
                teamId: $teamId, name: $name, color: $color, type: $type
              }) {
                success
                workflowState { id name }
              }
            }
            """,
            {"teamId": team_id, "name": name, "color": color, "type": state_type},
        )
        return data["workflowStateCreate"]["workflowState"]

    # ── Comments ──────────────────────────────────────────────────────────────

    def post_comment(self, issue_id: str, body: str) -> None:
        self._query(
            """
            mutation PostComment($issueId: String!, $body: String!) {
              commentCreate(input: { issueId: $issueId, body: $body }) {
                success
                comment { id }
              }
            }
            """,
            {"issueId": issue_id, "body": body},
        )
        logger.debug("comment posted issue=%s", issue_id)

    # ── Labels ────────────────────────────────────────────────────────────────

    def get_label_names(self, issue: dict) -> list[str]:
        return [lbl["name"].lower() for lbl in issue.get("labels", {}).get("nodes", [])]

    def get_team_labels(self, team_id: str) -> list[dict]:
        data = self._query(
            """
            query TeamLabels($teamId: String!) {
              team(id: $teamId) {
                labels { nodes { id name color } }
              }
            }
            """,
            {"teamId": team_id},
        )
        return data["team"]["labels"]["nodes"]

    def create_label(self, team_id: str, name: str, color: str) -> dict:
        data = self._query(
            """
            mutation CreateLabel($teamId: String!, $name: String!, $color: String!) {
              issueLabelCreate(input: {
                teamId: $teamId, name: $name, color: $color
              }) {
                success
                issueLabel { id name }
              }
            }
            """,
            {"teamId": team_id, "name": name, "color": color},
        )
        return data["issueLabelCreate"]["issueLabel"]

    def close(self) -> None:
        self._client.close()
