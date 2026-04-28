# ID Registry Template

---
type: id-registry
version: 2.0
last_updated: YYYY-MM-DDTHH:MM:SSZ
registry_purpose: Central tracking of all work item IDs
total_ids: 0
active_ids: 0
completed_ids: 0
archived_ids: 0
---

## Registry Statistics

### Cumulative Metrics

total_analyses: 0
total_plans: 0
total_todos: 0
total_reports: 0
total_coordinations: 0

### Current Period (Last 30 Days)

period_start: YYYY-MM-DD
period_end: YYYY-MM-DD
analyses_created: 0
plans_created: 0
todos_created: 0
completed_items: 0
average_completion_time: 0 hours

### Performance Metrics

on_time_completion_rate: 0%
average_analysis_time: 0 hours
average_planning_time: 0 hours
average_execution_time: 0 hours
first_time_success_rate: 0%

## Active IDs

### Analysis (AN) - Active

AN-YYYYMMDD-NNN:
  title: <brief title>
  status: active
  created: YYYY-MM-DDTHH:MM:SSZ
  updated: YYYY-MM-DDTHH:MM:SSZ
  author: pm
  files: 0
  folder_size: 0KB
  keywords: [keyword1, keyword2]
  linked_plan: PL-YYYYMMDD-NNN
  estimated_completion: YYYY-MM-DDTHH:MM:SSZ

### Plans (PL) - Active

PL-YYYYMMDD-NNN:
  title: <brief title>
  status: <planning|executing|validating>
  created: YYYY-MM-DDTHH:MM:SSZ
  updated: YYYY-MM-DDTHH:MM:SSZ
  analysis_ref: AN-YYYYMMDD-NNN
  todo_ref: TD-YYYYMMDD-NNN
  coordination_ref: CO-YYYYMMDD-NNN
  assigned_agents: [agent1, agent2]
  phases: 0/0 completed
  progress: 0%
  estimated_completion: YYYY-MM-DDTHH:MM:SSZ

### Todos (TD) - Active

TD-YYYYMMDD-NNN:
  title: <brief title>
  status: <not_started|in_progress|blocked>
  created: YYYY-MM-DDTHH:MM:SSZ
  updated: YYYY-MM-DDTHH:MM:SSZ
  plan_ref: PL-YYYYMMDD-NNN
  total_tasks: 0
  completed_tasks: 0
  blocked_tasks: 0
  active_agent: <agent_name>
  progress: 0%
  estimated_completion: YYYY-MM-DDTHH:MM:SSZ

### Reports (RP) - Active

RP-YYYYMMDD-NNN:
  title: <brief title>
  status: draft
  created: YYYY-MM-DDTHH:MM:SSZ
  report_type: <progress|completion|audit>
  related_work: [AN-YYYYMMDD-NNN, PL-YYYYMMDD-NNN]

### Coordinations (CO) - Active

CO-YYYYMMDD-NNN:
  title: <brief title>
  status: active
  created: YYYY-MM-DDTHH:MM:SSZ
  plan_ref: PL-YYYYMMDD-NNN
  participating_agents: [agent1, agent2]
  coordination_points: 0/0 completed
  next_checkpoint: YYYY-MM-DDTHH:MM:SSZ

## Recently Completed (Last 7 Days)

### Completed This Week

AN-YYYYMMDD-NNN:
  title: <brief title>
  completed: YYYY-MM-DDTHH:MM:SSZ
  duration: 0 hours
  outcome: <success|partial|pivoted>
  archive_scheduled: YYYY-MM-DD
  summary: <one-line summary>

PL-YYYYMMDD-NNN:
  title: <brief title>
  completed: YYYY-MM-DDTHH:MM:SSZ
  duration: 0 hours
  deliverables: 0
  archive_scheduled: YYYY-MM-DD
  summary: <one-line summary>

TD-YYYYMMDD-NNN:
  title: <brief title>
  completed: YYYY-MM-DDTHH:MM:SSZ
  total_duration: 0 hours
  tasks_completed: 0/0
  archive_scheduled: YYYY-MM-DD

## Quick Search Index

### By Topic/Keyword

keyword_1: [AN-YYYYMMDD-NNN, PL-YYYYMMDD-NNN]
keyword_2: [AN-YYYYMMDD-NNN, TD-YYYYMMDD-NNN]
keyword_3: [PL-YYYYMMDD-NNN, CO-YYYYMMDD-NNN]

### By Component

component_1: [AN-YYYYMMDD-NNN, PL-YYYYMMDD-NNN]
component_2: [AN-YYYYMMDD-NNN, TD-YYYYMMDD-NNN]

### By Agent

developer: [TD-YYYYMMDD-NNN, CO-YYYYMMDD-NNN]
tester: [TD-YYYYMMDD-NNN]
architect: [AN-YYYYMMDD-NNN]
pm: [all IDs]

### By Date Range

today: [AN-YYYYMMDD-NNN]
yesterday: [PL-YYYYMMDD-NNN]
this_week: [multiple IDs]
last_week: [multiple IDs]

## ID Relationships

### Dependency Graph

AN-YYYYMMDD-001 → PL-YYYYMMDD-001 → TD-YYYYMMDD-001
                                  ↘ CO-YYYYMMDD-001

AN-YYYYMMDD-002 → PL-YYYYMMDD-002 → TD-YYYYMMDD-002

### Cross-References

work_group_1:
  analysis: AN-YYYYMMDD-001
  plan: PL-YYYYMMDD-001
  todo: TD-YYYYMMDD-001
  coordination: CO-YYYYMMDD-001
  report: RP-YYYYMMDD-001

work_group_2:
  analysis: AN-YYYYMMDD-002
  plan: PL-YYYYMMDD-002
  todo: TD-YYYYMMDD-002

## Blocked Items

### Currently Blocked

TD-YYYYMMDD-NNN:
  blocked_by: <description of blocker>
  blocking_items: [list of items this blocks]
  owner: <who is resolving>
  eta: YYYY-MM-DDTHH:MM:SSZ

## Archive Schedule

### Pending Archival (7+ Days Old)

items_to_archive:
  - AN-YYYYMMDD-NNN (completed YYYY-MM-DD)
  - PL-YYYYMMDD-NNN (completed YYYY-MM-DD)
  - TD-YYYYMMDD-NNN (completed YYYY-MM-DD)

next_archive_run: YYYY-MM-DDTHH:MM:SSZ
archive_location: memory/archive/YYYY-MM/

## ID Allocation

### Next Available IDs

next_analysis_id: AN-YYYYMMDD-001
next_plan_id: PL-YYYYMMDD-001
next_todo_id: TD-YYYYMMDD-001
next_report_id: RP-YYYYMMDD-001
next_coordination_id: CO-YYYYMMDD-001

### Today's ID Usage

analyses_today: 0
plans_today: 0
todos_today: 0
reports_today: 0
coordinations_today: 0

## Registry Maintenance

last_cleanup: YYYY-MM-DDTHH:MM:SSZ
last_archive: YYYY-MM-DDTHH:MM:SSZ
last_backup: YYYY-MM-DDTHH:MM:SSZ
integrity_check: passed
orphaned_items: 0

## Notes

registry_notes: <any notes about registry status>
maintenance_notes: <any maintenance performed>
migration_status: <if migrating from old system>