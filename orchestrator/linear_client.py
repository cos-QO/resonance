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

# Resonance-specific states to create (with role, default name, color, type, description).
# In Progress and Todo are standard Linear states — we verify but don't create them.
STATES_TO_CREATE = [
    {
        "role": "eligibility",
        "default": "Plan Approved",
        "color": "#4CAF50",
        "type": "unstarted",
        "description": "move issues here to authorize agent work",
    },
    {
        "role": "feedback",
        "default": "Agent Feedback Needed",
        "color": "#FF9800",
        "type": "started",
        "description": "set when agent needs human input",
    },
    {
        "role": "review",
        "default": "Human Review",
        "color": "#9C27B0",
        "type": "started",
        "description": "set when agent finishes — ready for PR review",
    },
]

# Standard Linear states that always exist — Resonance uses but does not create them.
STATES_STANDARD = [
    {"role": "in_progress", "default": "In Progress"},
    {"role": "return",      "default": "Todo"},
]

# Required issue labels — created by resonance setup if missing
REQUIRED_LABELS = [
    {"name": "RES",      "color": "#FF6B35"},  # Resonance-managed marker
    {"name": "pep",      "color": "#7C3AED"},  # Product Execution Prompt — triggers PEP Reader Agent
    {"name": "plan",     "color": "#7C4DFF"},
    {"name": "design",   "color": "#F06292"},
    {"name": "frontend", "color": "#4FC3F7"},
    {"name": "backend",  "color": "#26A69A"},
    {"name": "bug",      "color": "#EF5350"},
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
        if resp.status_code >= 400:
            try:
                detail = resp.json()
            except Exception:
                detail = resp.text
            raise RuntimeError(f"Linear API {resp.status_code}: {detail}")
        body = resp.json()
        if "errors" in body:
            raise RuntimeError(f"Linear GraphQL error: {body['errors']}")
        return body["data"]

    # ── Auth / viewer ─────────────────────────────────────────────────────────

    def get_viewer(self) -> dict:
        """Validate API key and return the authenticated user."""
        data = self._query("query { viewer { id name email } }")
        return data["viewer"]

    # ── Teams ─────────────────────────────────────────────────────────────────

    def get_teams(self) -> list[dict]:
        """List all teams in the workspace."""
        data = self._query(
            """
            query {
              teams(first: 50) {
                nodes { id name key }
              }
            }
            """
        )
        return data["teams"]["nodes"]

    def get_team(self, team_id: str) -> Optional[dict]:
        """Get a team by UUID."""
        data = self._query(
            """
            query Team($id: String!) {
              team(id: $id) { id name key }
            }
            """,
            {"id": team_id},
        )
        return data.get("team")

    # ── Issues ────────────────────────────────────────────────────────────────

    def get_pipeline_issues(
        self,
        team_id: str,
        state_names: list[str],
        project_id: Optional[str] = None,
    ) -> list[dict]:
        """Return all issues in any of the given states (full pipeline view).

        If project_id is provided, scopes the query to that project only.
        """
        _ISSUE_FIELDS = """
            id identifier title updatedAt
            state { name }
            labels { nodes { name } }
            assignee { name }
        """
        if project_id:
            data = self._query(
                f"""
                query PipelineIssues($projectId: String!, $states: [String!]) {{
                  project(id: $projectId) {{
                    issues(
                      filter: {{ state: {{ name: {{ in: $states }} }} }}
                      first: 50
                    ) {{
                      nodes {{ {_ISSUE_FIELDS} }}
                    }}
                  }}
                }}
                """,
                {"projectId": project_id, "states": state_names},
            )
            return data["project"]["issues"]["nodes"]
        else:
            data = self._query(
                f"""
                query PipelineIssues($teamId: String!, $states: [String!]) {{
                  team(id: $teamId) {{
                    issues(
                      filter: {{ state: {{ name: {{ in: $states }} }} }}
                      first: 50
                    ) {{
                      nodes {{ {_ISSUE_FIELDS} }}
                    }}
                  }}
                }}
                """,
                {"teamId": team_id, "states": state_names},
            )
            return data["team"]["issues"]["nodes"]

    def get_eligible_issues(
        self,
        team_id: str,
        state_name: str,
        project_id: Optional[str] = None,
    ) -> list[dict]:
        """Return all issues in `state_name`.

        If project_id is provided, scopes the query to that project only.
        """
        _ISSUE_FIELDS = """
            id
            identifier
            title
            description
            state { id name }
            labels { nodes { id name } }
            team { id name }
            assignee { id name }
            url
        """
        if project_id:
            data = self._query(
                f"""
                query EligibleIssues($projectId: String!, $stateName: String!) {{
                  project(id: $projectId) {{
                    issues(
                      filter: {{ state: {{ name: {{ eq: $stateName }} }} }}
                      first: 50
                    ) {{
                      nodes {{ {_ISSUE_FIELDS} }}
                    }}
                  }}
                }}
                """,
                {"projectId": project_id, "stateName": state_name},
            )
            return data["project"]["issues"]["nodes"]
        else:
            data = self._query(
                f"""
                query EligibleIssues($teamId: String!, $stateName: String!) {{
                  team(id: $teamId) {{
                    issues(
                      filter: {{ state: {{ name: {{ eq: $stateName }} }} }}
                      first: 50
                    ) {{
                      nodes {{ {_ISSUE_FIELDS} }}
                    }}
                  }}
                }}
                """,
                {"teamId": team_id, "stateName": state_name},
            )
            return data["team"]["issues"]["nodes"]

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
                inverseRelations {
                  nodes {
                    type
                    relatedIssue { id identifier state { name } }
                  }
                }
              }
            }
            """,
            {"id": issue_id},
        )
        return data.get("issue")

    def get_issue_with_comments(self, issue_id: str) -> Optional[dict]:
        """Fetch issue including all comments — used when resuming after Human Review."""
        data = self._query(
            """
            query IssueWithComments($id: String!) {
              issue(id: $id) {
                id
                identifier
                title
                description
                state { id name }
                labels { nodes { id name } }
                team { id name }
                url
                comments(first: 50, orderBy: createdAt) {
                  nodes {
                    id
                    body
                    createdAt
                    user { name email }
                  }
                }
              }
            }
            """,
            {"id": issue_id},
        )
        return data.get("issue")

    def update_issue(
        self,
        issue_id: str,
        description: Optional[str] = None,
        title: Optional[str] = None,
    ) -> None:
        """Update issue fields (description, title)."""
        input_fields: dict = {}
        if description is not None:
            input_fields["description"] = description
        if title is not None:
            input_fields["title"] = title
        if not input_fields:
            return
        self._query(
            """
            mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {
              issueUpdate(id: $id, input: $input) {
                success
              }
            }
            """,
            {"id": issue_id, "input": input_fields},
        )
        logger.debug("issue updated id=%s fields=%s", issue_id, list(input_fields))

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

    def add_issue_label(self, issue_id: str, team_id: str, label_name: str) -> None:
        """Add a label to an existing issue, preserving existing labels."""
        # Get current label IDs
        issue = self.get_issue(issue_id)
        if not issue:
            return
        current_ids = [lbl["id"] for lbl in issue.get("labels", {}).get("nodes", [])]
        # Resolve the new label
        new_ids = self._resolve_label_ids(team_id, [label_name])
        if not new_ids:
            logger.warning("label '%s' not found — cannot add to issue %s", label_name, issue_id)
            return
        combined = list(dict.fromkeys(current_ids + new_ids))  # dedup preserving order
        self._query(
            """
            mutation AddLabel($issueId: String!, $labelIds: [String!]!) {
              issueUpdate(id: $issueId, input: { labelIds: $labelIds }) {
                success
              }
            }
            """,
            {"issueId": issue_id, "labelIds": combined},
        )
        logger.debug("added label '%s' to issue %s", label_name, issue_id)

    # ── Projects ──────────────────────────────────────────────────────────────

    def get_projects(self, team_id: str) -> list[dict]:
        """List all projects in a team."""
        data = self._query(
            """
            query TeamProjects($teamId: String!) {
              team(id: $teamId) {
                projects(first: 50) {
                  nodes { id name description url }
                }
              }
            }
            """,
            {"teamId": team_id},
        )
        return data["team"]["projects"]["nodes"]

    def get_project(self, project_id: str) -> Optional[dict]:
        """Get a project by UUID."""
        data = self._query(
            """
            query Project($id: String!) {
              project(id: $id) { id name description url }
            }
            """,
            {"id": project_id},
        )
        return data.get("project")

    # ── Milestones ────────────────────────────────────────────────────────────

    def get_milestones(self, project_id: str) -> list[dict]:
        """List milestones for a project."""
        data = self._query(
            """
            query ProjectMilestones($projectId: String!) {
              project(id: $projectId) {
                projectMilestones {
                  nodes { id name description }
                }
              }
            }
            """,
            {"projectId": project_id},
        )
        return data["project"]["projectMilestones"]["nodes"]

    def create_milestone(
        self,
        project_id: str,
        name: str,
        description: str = "",
        target_date: Optional[str] = None,
    ) -> dict:
        """Create a project milestone. Returns {id, name}."""
        variables: dict = {"projectId": project_id, "name": name}
        if description:
            variables["description"] = description
        if target_date:
            variables["targetDate"] = target_date

        data = self._query(
            """
            mutation CreateMilestone(
              $projectId: String!,
              $name: String!,
              $description: String,
              $targetDate: TimelessDate
            ) {
              projectMilestoneCreate(input: {
                projectId: $projectId
                name: $name
                description: $description
                targetDate: $targetDate
              }) {
                success
                projectMilestone { id name }
              }
            }
            """,
            variables,
        )
        return data["projectMilestoneCreate"]["projectMilestone"]

    # ── Issue creation ────────────────────────────────────────────────────────

    def _resolve_label_ids(self, team_id: str, label_names: list[str]) -> list[str]:
        """Resolve label names to IDs for the given team."""
        labels = self.get_team_labels(team_id)
        name_to_id = {l["name"].lower(): l["id"] for l in labels}
        ids = []
        for name in label_names:
            label_id = name_to_id.get(name.lower())
            if label_id:
                ids.append(label_id)
            else:
                logger.warning("label '%s' not found in team %s — skipping", name, team_id)
        return ids

    def create_issue(
        self,
        team_id: str,
        title: str,
        description: str = "",
        project_id: Optional[str] = None,
        state_name: Optional[str] = None,
        priority: int = 0,
        label_names: Optional[list[str]] = None,
        parent_id: Optional[str] = None,
        milestone_id: Optional[str] = None,
    ) -> dict:
        """Create a Linear issue. Returns {id, identifier, title, url}."""
        variables: dict = {"teamId": team_id, "title": title}
        if description:
            variables["description"] = description
        if project_id:
            variables["projectId"] = project_id
        if state_name:
            variables["stateId"] = self.get_state_id(team_id, state_name)
        if priority:
            variables["priority"] = priority
        if parent_id:
            variables["parentId"] = parent_id
        if milestone_id:
            variables["projectMilestoneId"] = milestone_id
        if label_names:
            label_ids = self._resolve_label_ids(team_id, label_names)
            if label_ids:
                variables["labelIds"] = label_ids

        data = self._query(
            """
            mutation CreateIssue(
              $teamId: String!,
              $title: String!,
              $description: String,
              $projectId: String,
              $stateId: String,
              $priority: Int,
              $parentId: String,
              $projectMilestoneId: String,
              $labelIds: [String!]
            ) {
              issueCreate(input: {
                teamId: $teamId
                title: $title
                description: $description
                projectId: $projectId
                stateId: $stateId
                priority: $priority
                parentId: $parentId
                projectMilestoneId: $projectMilestoneId
                labelIds: $labelIds
              }) {
                success
                issue { id identifier title url }
              }
            }
            """,
            variables,
        )
        return data["issueCreate"]["issue"]

    def create_issue_relation(
        self,
        issue_id: str,
        related_issue_id: str,
        relation_type: str = "blocks",
    ) -> None:
        """Create a relation between two issues.

        relation_type='blocks' means issue_id blocks related_issue_id.
        To say B is blocked by A: create_issue_relation(A_id, B_id, 'blocks').
        """
        self._query(
            """
            mutation CreateRelation(
              $issueId: String!,
              $relatedIssueId: String!,
              $type: IssueRelationType!
            ) {
              issueRelationCreate(input: {
                issueId: $issueId
                relatedIssueId: $relatedIssueId
                type: $type
              }) {
                success
                issueRelation { id type }
              }
            }
            """,
            {"issueId": issue_id, "relatedIssueId": related_issue_id, "type": relation_type},
        )
        logger.debug("relation created %s blocks %s", issue_id, related_issue_id)

    def close(self) -> None:
        self._client.close()
