# Claude Code Ecosystem Structure (Markdown-KV)

## Authority and Status

```
scope: application-support structure for agents (supplement)
approval_required: PM/Product Manager approval for modifications
change_log_location: /.claude/memory/standards/CHANGELOG.md
status: MANDATORY - agent ecosystem separate from project files
last_updated: 2025-09-22
version: 2.0
```

## Core Principle: Separation of Concerns

```
principle: separation of concerns between agent ecosystem and project files
agent_ecosystem_purpose: analyze project without modifying project structure
collaboration_method: build/scale actual project through coordination
separation_requirement: clean separation between agent work and project files
enhancement_approach: enhance project without interfering with project organization
```

## Critical Requirements for All Agents

```
requirement_1: work with project files - analyze, enhance, and build the actual project
requirement_2: keep .claude/ separate - never mix agent workspace with project files
requirement_3: respect project structure - follow existing project conventions
requirement_4: use .claude/ for agent coordination - memory, workspace, artifacts for collaboration
violation_consequence: automatic detection and correction
compliance_mandatory: yes for all agents without exception
```

## Directory Structure Definitions

```
workspace_folder_status: REMOVED - using git for version control and staging
system_focus: learning about and enhancing existing project, not creating parallel workspaces
structure_purpose: agent coordination and project enhancement
```

### Agent Testing Structure

```
testing_location: /.claude/tests/
unit_tests_path: /.claude/tests/unit/ (agent-generated unit tests FOR the project)
integration_tests_path: /.claude/tests/integration/ (agent-generated integration tests FOR the project)
e2e_tests_path: /.claude/tests/e2e/ (agent-generated E2E tests FOR the project)
performance_tests_path: /.claude/tests/performance/ (performance tests FOR the project)
security_tests_path: /.claude/tests/security/ (security tests FOR the project)
reports_path: /.claude/tests/reports/ (test analysis and validation reports)
```

```
test_purpose: agent-generated tests FOR the project
relationship_to_project_tests: supplements, not replacement
project_test_locations: project/tests/, project/spec/, etc. (preserved)
staging_function: tests staged here before integration into project structure
tester_workflow: generate tests in .claude/tests/, then integrate into project structure
```

### Artifacts Structure

```
artifacts_location: /.claude/artifacts/
code_artifacts_path: /.claude/artifacts/code/ (generated code snippets TO BE ADDED to project)
design_artifacts_path: /.claude/artifacts/design/ (design files, mockups FOR the project)
research_artifacts_path: /.claude/artifacts/research/ (research documents ABOUT the project)
debug_artifacts_path: /.claude/artifacts/debug/ (debug files, logs, diagnostic data)
test_artifacts_path: /.claude/artifacts/tests/ (generated test artifacts and data)
```

### Temporary Files Structure

```
temp_location: /.claude/temp/
debug_temp_path: /.claude/temp/debug/ (temporary debug files with auto-cleanup)
cache_temp_path: /.claude/temp/cache/ (temporary cache files)
logs_temp_path: /.claude/temp/logs/ (temporary log files)
scratch_temp_path: /.claude/temp/scratch/ (temporary scratch files)
```

```
staging_purpose: staging areas for project enhancement
developer_workflow: generate code here → then add to actual project files
ux_designer_workflow: create designs here → then implement in project
researcher_workflow: document findings here → then apply insights to project
storage_principle: not permanent storage - artifacts should flow INTO the actual project
```

### Project Management Structure

```
project_location: /.claude/project/
sprint_path: /.claude/project/sprint/ (sprint planning and tracking files)
features_path: /.claude/project/features/ (feature specifications and requirements)
metrics_path: /.claude/project/metrics/ (project metrics and analytics)
milestones_path: /.claude/project/milestones/ (milestone tracking and definitions)
organization_path: /.claude/project/organization/ (project structure and team organization)
```

```
product_manager_usage: project/features/ and project/sprint/
business_analyst_usage: project/metrics/ and project/milestones/
pm_usage: project/organization/ for coordination
```

### Cleanup Structure

```
cleanup_location: /.claude/cleanup/
archive_path: /.claude/cleanup/archive/ (old files archived for reference)
deprecated_path: /.claude/cleanup/deprecated/ (deprecated files marked for removal)
scheduled_path: /.claude/cleanup/scheduled/ (files scheduled for cleanup operations)
```

```
all_agents_usage: move old files to cleanup/archive/
developer_usage: mark deprecated code in cleanup/deprecated/
cleanup_command_usage: automatically manages cleanup/scheduled/
```

## Enforced Rules

### Rule 1: No New Top-Level Folders

```
forbidden_pattern: creating new top-level folders in /.claude/
forbidden_examples: /.claude/my-new-folder/, /.claude/temp/, /.claude/custom/
required_approach: use existing established directories
required_examples: /.claude/workspace/sandbox/my-prototype/, /.claude/artifacts/code/my-generated-code/
rule_enforcement: automatic detection and correction
```

### Rule 2: Exact Path Usage

```
wrong_patterns: /.claude/test-files/, /.claude/designs/, /.claude/research-docs/
correct_patterns: /.claude/tests/unit/, /.claude/artifacts/design/, /.claude/artifacts/research/
path_requirement: use exact specified paths only
path_deviation_consequence: automatic violation detection
```

### Rule 3: Agent-Specific Requirements

```
developer_code_artifacts: /.claude/artifacts/code/
developer_test_files: /.claude/tests/[unit|integration|e2e]/
developer_work_in_progress: /.claude/workspace/current/
```

```
ux_designer_design_outputs: /.claude/artifacts/design/ (ALL design outputs)
ux_designer_exceptions: none - never create /designs/ or similar
ux_designer_enforcement: strict path compliance required
```

```
tester_unit_tests: /.claude/tests/unit/
tester_integration_tests: /.claude/tests/integration/
tester_e2e_tests: /.claude/tests/e2e/
tester_test_reports: /.claude/tests/reports/
```

```
researcher_research_outputs: /.claude/artifacts/research/ (ALL research)
researcher_prototypes: /.claude/workspace/sandbox/
```

```
product_manager_features: /.claude/project/features/
product_manager_sprint_planning: /.claude/project/sprint/
```

```
security_security_tests: /.claude/tests/security/
security_security_artifacts: /.claude/artifacts/code/security/
```

## Memory as Project Knowledge Base

```
memory_purpose: contains LEARNED knowledge about the EXISTING PROJECT
memory_location: /.claude/memory/
standards_path: /.claude/memory/standards/ (analyzed project conventions, patterns, structure)
discovery_path: /.claude/memory/discovery/ (project analysis, research findings)
context_path: /.claude/memory/context/ (current project state, recent changes)
decisions_path: /.claude/memory/decisions/ (architecture decisions ABOUT the project)
insights_path: /.claude/memory/insights/ (accumulated wisdom ABOUT the project)
```

```
conventions_file: /.claude/memory/standards/conventions.md (code style, naming, patterns with timestamp)
tree_file: /.claude/memory/standards/tree.md (project structure analysis with timestamp)
folder_structure_file: /.claude/memory/standards/folder-structure.md (this file - how .claude/ works)
design_system_file: /.claude/memory/standards/design-system.md (UI patterns, components, tokens with timestamp)
reportid_system_file: /.claude/memory/standards/reportid-system.md (progress tracking system)
```

```
prepare_command_management: /prepare manages key analysis files
conventions_purpose: learned coding patterns FROM the project
tree_purpose: documented project structure (not .claude structure)
design_system_purpose: analyzed UI tokens, components, visual patterns
timestamp_requirement: all include timestamps to track when analysis was last updated
```

## Pre-Work Checklist

```
step_1: read project memory - understand current project state
step_2: analyze project structure - learn existing patterns/conventions
step_3: use .claude/ for coordination - work within agent ecosystem
step_4: enhance project files - apply improvements to actual project
step_5: update memory - share learnings with other agents
checklist_requirement: mandatory for ALL tasks
checklist_compliance: must be completed before starting any work
```

## Violation Detection

```
violation_trigger_1: creating folders outside established structure
violation_trigger_2: creating duplicate folders with similar purposes
violation_trigger_3: ignoring agent-specific folder requirements
violation_trigger_4: not checking this document before file creation
detection_method: automatic monitoring and reporting
correction_method: automatic reorganization and cleanup
```

## Maintenance Protocol

```
structure_immutability: immutable - do not change without system-wide updates
structure_compliance: mandatory - all agents must comply
structure_monitoring: monitored - violations detected and corrected
structure_enforcement: enforced - cleanup command reorganizes violations
protocol_status: active and operational
```

## Quick Reference

```
developer_primary: artifacts/code/, tests/unit/
developer_secondary: workspace/current/
tester_primary: tests/[unit|integration|e2e]/
tester_secondary: tests/reports/
ux_designer_primary: artifacts/design/
ux_designer_secondary: workspace/sandbox/
researcher_primary: artifacts/research/
researcher_secondary: workspace/sandbox/
architect_primary: artifacts/code/, artifacts/design/
architect_secondary: workspace/staging/
security_primary: tests/security/
security_secondary: artifacts/code/security/
product_manager_primary: project/features/, project/sprint/
product_manager_secondary: project/metrics/
business_analyst_primary: project/metrics/, project/milestones/
business_analyst_secondary: artifacts/research/
```

```
structure_purpose: prevent chaos through organized file management
compliance_requirement: follow religiously without deviation
agent_obligation: all agents must read and follow this structure
violation_handling: automatic correction by cleanup system
structure_authority: mandatory for all agent operations
```
