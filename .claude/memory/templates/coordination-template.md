# Coordination Template (CO-XXXXXX-XXX-NN)

---
id: CO-YYYYMMDD-NNN-NN
type: coordination
created: YYYY-MM-DDTHH:MM:SSZ
updated: YYYY-MM-DDTHH:MM:SSZ
author: pm
status: <active|completed>
plan_ref: PL-YYYYMMDD-NNN
todo_ref: TD-YYYYMMDD-NNN
participating_agents: [agent1, agent2, agent3]
---

## Coordination Overview

coordination_purpose: <why coordination is needed>
coordination_type: <sequential|parallel|hybrid>
expected_duration: <time estimate>
actual_duration: <filled when complete>
complexity: <low|medium|high>

## Agent Roster

### Active Agents

agent_1:
  name: <agent name>
  role: <primary role>
  status: <idle|working|blocked|completed>
  current_task: <task ID or description>
  availability: <available|busy|upcoming>

agent_2:
  name: <agent name>
  role: <support role>
  status: <status>
  current_task: <task>
  availability: <availability>

agent_3:
  name: <agent name>
  role: <review role>
  status: <status>
  current_task: <task>
  availability: <availability>

## Coordination Timeline

### Scheduled Coordination Points

checkpoint_1:
  time: YYYY-MM-DDTHH:MM:SSZ
  type: <handoff|review|sync|decision>
  participants: [agent1, agent2]
  purpose: <checkpoint purpose>
  status: <pending|completed>
  outcome: <outcome when completed>

checkpoint_2:
  time: YYYY-MM-DDTHH:MM:SSZ
  type: <type>
  participants: [agents]
  purpose: <purpose>
  status: <status>
  outcome: <outcome>

### Completed Coordination Events

event_1:
  timestamp: YYYY-MM-DDTHH:MM:SSZ
  type: handoff
  from: agent1
  to: agent2
  deliverable: <what was handed off>
  validation: <confirmation of receipt>

event_2:
  timestamp: YYYY-MM-DDTHH:MM:SSZ
  type: decision
  participants: [pm, agent1]
  decision: <what was decided>
  rationale: <why>

## Active Handoffs

### In-Progress Handoffs

handoff_1:
  from: <agent>
  to: <agent>
  item: <what is being handed off>
  status: <preparing|ready|in_transit|received>
  expected_completion: YYYY-MM-DDTHH:MM:SSZ
  validation_criteria: <how to validate>

### Pending Handoffs

handoff_2:
  from: <agent>
  to: <agent>
  item: <what will be handed off>
  blocked_by: <what's blocking>
  expected_ready: YYYY-MM-DDTHH:MM:SSZ

## Communication Log

### Critical Communications

communication_1:
  timestamp: YYYY-MM-DDTHH:MM:SSZ
  from: <agent>
  to: <agent|pm|all>
  type: <issue|update|request|decision>
  message: <communication content>
  response_required: <yes|no>
  response: <response if provided>

communication_2:
  timestamp: YYYY-MM-DDTHH:MM:SSZ
  from: <agent>
  to: <recipients>
  type: <type>
  message: <content>
  response_required: <yes|no>
  response: <response>

## Decision Log

### Decisions Made

decision_1:
  timestamp: YYYY-MM-DDTHH:MM:SSZ
  decision: <what was decided>
  made_by: <who decided>
  rationale: <reasoning>
  impact: <impact on plan>
  communicated_to: [agent1, agent2]

decision_2:
  timestamp: YYYY-MM-DDTHH:MM:SSZ
  decision: <decision>
  made_by: <decider>
  rationale: <reasoning>
  impact: <impact>
  communicated_to: [agents]

### Pending Decisions

pending_1:
  decision_needed: <what needs to be decided>
  required_by: YYYY-MM-DDTHH:MM:SSZ
  decision_maker: <who will decide>
  blocking: [task1, task2]
  options: [option1, option2]

## Issue Tracking

### Active Issues

issue_1:
  id: ISS-001
  reported: YYYY-MM-DDTHH:MM:SSZ
  reporter: <agent>
  severity: <low|medium|high|critical>
  description: <issue description>
  impact: <impact description>
  assigned_to: <who is resolving>
  status: <investigating|in_progress|blocked>
  eta: YYYY-MM-DDTHH:MM:SSZ

issue_2:
  id: ISS-002
  reported: YYYY-MM-DDTHH:MM:SSZ
  reporter: <agent>
  severity: <severity>
  description: <description>
  impact: <impact>
  assigned_to: <resolver>
  status: <status>
  eta: <estimated resolution>

### Resolved Issues

resolved_1:
  id: ISS-000
  resolution: <how it was resolved>
  resolved_by: <who resolved>
  resolved_at: YYYY-MM-DDTHH:MM:SSZ
  verification: <how verified>

## Resource Management

### Resource Allocation

resource_1:
  type: <compute|storage|service|tool>
  allocated_to: <agent>
  amount: <quantity>
  duration: <how long needed>
  status: <allocated|in_use|released>

resource_2:
  type: <type>
  allocated_to: <agent>
  amount: <quantity>
  duration: <duration>
  status: <status>

### Resource Conflicts

conflict_1:
  resource: <resource name>
  requested_by: [agent1, agent2]
  resolution: <how resolved>
  priority_given_to: <agent>

## Workflow Status

### Parallel Work Streams

stream_1:
  name: <stream name>
  agents: [agent1, agent2]
  status: <active|completed|blocked>
  progress: <percentage>
  dependencies: [stream2]

stream_2:
  name: <stream name>
  agents: [agent3]
  status: <status>
  progress: <percentage>
  dependencies: []

### Sequential Steps

step_1:
  name: <step name>
  agent: <agent>
  status: completed
  duration: <actual duration>

step_2:
  name: <step name>
  agent: <agent>
  status: in_progress
  started: YYYY-MM-DDTHH:MM:SSZ
  expected_completion: YYYY-MM-DDTHH:MM:SSZ

step_3:
  name: <step name>
  agent: <agent>
  status: pending
  blocked_by: step_2
  expected_start: YYYY-MM-DDTHH:MM:SSZ

## Quality Gates

### Completed Gates

gate_1:
  name: <gate name>
  timestamp: YYYY-MM-DDTHH:MM:SSZ
  evaluator: <agent>
  result: passed
  notes: <any notes>

### Pending Gates

gate_2:
  name: <gate name>
  scheduled: YYYY-MM-DDTHH:MM:SSZ
  evaluator: <agent>
  criteria: <pass criteria>
  dependencies: [deliverable1]

## Performance Metrics

coordination_efficiency: <percentage>
handoff_success_rate: <percentage>
communication_clarity: <rating>
decision_turnaround: <average time>
issue_resolution_time: <average time>
parallel_efficiency: <percentage>

## Risk Management

### Active Risks

risk_1:
  description: <risk description>
  probability: <low|medium|high>
  impact: <low|medium|high>
  mitigation: <current mitigation>
  owner: <who is managing>

### Materialized Risks

materialized_1:
  description: <risk that happened>
  impact_actual: <actual impact>
  resolution: <how resolved>
  lessons_learned: <what we learned>

## Escalation Log

### Escalations

escalation_1:
  timestamp: YYYY-MM-DDTHH:MM:SSZ
  escalated_by: <agent>
  issue: <what was escalated>
  escalated_to: <pm|user>
  resolution: <how resolved>

## Status Summary

overall_status: <on_track|at_risk|delayed|blocked>
completion_percentage: <percentage>
critical_path_status: <status>
next_milestone: <description and time>

key_highlights:
  - <highlight 1>
  - <highlight 2>
  - <highlight 3>

attention_required:
  - <item 1>
  - <item 2>

## Next Actions

immediate_actions:
  1. <action with owner>
  2. <action with owner>
  3. <action with owner>

upcoming_coordination:
  - <coordination point and time>
  - <coordination point and time>

## Cross-References

plan_document: PL-YYYYMMDD-NNN
todo_tracking: TD-YYYYMMDD-NNN
analysis_document: AN-YYYYMMDD-NNN
related_coordination: [CO-YYYYMMDD-NNN]
issue_tracker: [issue references]

## Notes

pm_notes: <PM observations and guidance>
agent_notes:
  agent_1: <agent 1 notes>
  agent_2: <agent 2 notes>

coordination_learnings: <what we're learning about coordination>