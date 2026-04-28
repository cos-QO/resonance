#!/usr/bin/env python3
"""
Execution Tracker Hook
Tracks agent chain progress and injects task awareness.

Events: SubagentStart, SubagentStop
Purpose:
  - SubagentStart: Inject agent's assigned tasks from the plan into its context
  - SubagentStop: Mark agent complete, identify next agents, suggest commit checkpoint
"""

import json
import sys
import os
import glob
from pathlib import Path
from datetime import datetime


def find_claude_dir():
    """Walk up from CWD to find .claude directory"""
    current = Path.cwd()
    while current != current.parent:
        claude_dir = current / '.claude'
        if claude_dir.is_dir():
            return claude_dir
        current = current.parent
    # Fallback: check CLAUDE_PROJECT_DIR env
    project_dir = os.environ.get('CLAUDE_PROJECT_DIR', '')
    if project_dir:
        claude_dir = Path(project_dir) / '.claude'
        if claude_dir.is_dir():
            return claude_dir
    return None


def get_tracker_path(claude_dir):
    return claude_dir / 'memory' / 'active' / 'execution-tracker.json'


def load_tracker(tracker_path):
    """Load or initialize execution tracker"""
    if tracker_path.exists():
        try:
            with open(tracker_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return None


def save_tracker(tracker_path, data):
    """Save execution tracker"""
    tracker_path.parent.mkdir(parents=True, exist_ok=True)
    with open(tracker_path, 'w') as f:
        json.dump(data, f, indent=2)


def find_active_plan(claude_dir):
    """Find the most recent plan/TODO file to extract phase/task info"""
    todos_dir = claude_dir / 'memory' / 'todos'
    if not todos_dir.exists():
        return None

    # Find most recent TODO file
    todo_files = sorted(todos_dir.glob('TODO-*.md'), key=lambda f: f.stat().st_mtime, reverse=True)
    if not todo_files:
        return None

    return todo_files[0]


def parse_plan_for_agent(todo_path, agent_name):
    """Extract tasks assigned to a specific agent from the plan"""
    if not todo_path or not todo_path.exists():
        return None

    content = todo_path.read_text()
    lines = content.split('\n')

    # Extract plan ID
    plan_id = None
    for line in lines:
        if 'PLAN-' in line:
            import re
            match = re.search(r'(PLAN-[\w-]+)', line)
            if match:
                plan_id = match.group(1)
                break

    # Find tasks assigned to this agent
    agent_tasks = []
    current_phase = None
    in_agent_section = False

    for line in lines:
        # Detect phase headers
        if line.startswith('## Phase') or line.startswith('### Phase'):
            current_phase = line.strip('#').strip()
            in_agent_section = False

        # Detect agent assignment
        if f'@{agent_name}' in line or f'AGENT: @{agent_name}' in line or f'agent: {agent_name}' in line.lower():
            in_agent_section = True
            agent_tasks.append({
                'phase': current_phase,
                'task': line.strip().strip('- '),
            })
        elif in_agent_section and line.strip().startswith('- '):
            agent_tasks.append({
                'phase': current_phase,
                'task': line.strip().strip('- '),
            })
        elif in_agent_section and line.strip() == '':
            in_agent_section = False

    return {
        'plan_id': plan_id,
        'todo_file': str(todo_path),
        'agent_tasks': agent_tasks
    }


def extract_parallel_groups(tracker):
    """Find which agents can run in parallel (same phase, no dependencies)"""
    if not tracker or 'phases' not in tracker:
        return []

    pending_phases = [p for p in tracker['phases'] if p.get('status') == 'pending']
    if not pending_phases:
        return []

    # Find phases whose dependencies are all complete
    completed_phases = {p['id'] for p in tracker['phases'] if p.get('status') == 'completed'}

    ready = []
    for phase in pending_phases:
        deps = set(phase.get('depends_on', []))
        if deps.issubset(completed_phases):
            ready.append(phase)

    return ready


def handle_subagent_start(data, claude_dir):
    """Inject task awareness when agent starts"""
    agent_name = data.get('agent_name', '') or data.get('subagent_type', '')
    if not agent_name:
        return

    tracker_path = get_tracker_path(claude_dir)
    tracker = load_tracker(tracker_path)

    # Also try to find tasks from TODO file
    todo_path = find_active_plan(claude_dir)
    plan_info = parse_plan_for_agent(todo_path, agent_name)

    output_parts = []

    # If we have a tracker, show agent its position in the chain
    if tracker:
        completed = tracker.get('completed_agents', [])
        current_phase_id = tracker.get('current_phase')

        # Find this agent's tasks in the tracker
        agent_phase = None
        for phase in tracker.get('phases', []):
            for task in phase.get('tasks', []):
                if task.get('agent') == agent_name and task.get('status') != 'completed':
                    agent_phase = phase
                    break

        if agent_phase:
            output_parts.append(f"📋 EXECUTION CONTEXT")
            output_parts.append(f"Plan: {tracker.get('plan_id', 'unknown')}")
            output_parts.append(f"Your phase: {agent_phase.get('title', agent_phase.get('id', '?'))}")
            output_parts.append(f"Completed before you: {', '.join(completed) if completed else 'none (you are first)'}")
            output_parts.append("")

            # Show this agent's specific tasks
            output_parts.append("YOUR ASSIGNED TASKS:")
            for task in agent_phase.get('tasks', []):
                if task.get('agent') == agent_name:
                    status_icon = '✅' if task.get('status') == 'completed' else '⬜'
                    output_parts.append(f"  {status_icon} {task.get('title', task.get('description', ''))}")

            # Show what previous agents produced (handoff files)
            handoffs = tracker.get('handoff_files', {})
            if handoffs:
                output_parts.append("")
                output_parts.append("PREVIOUS AGENT OUTPUTS (read these first):")
                for agent, files in handoffs.items():
                    if agent != agent_name and files:
                        for f in (files if isinstance(files, list) else [files]):
                            output_parts.append(f"  📄 @{agent}: {f}")

            # Show parallel agents if any
            parallel = [t.get('agent') for p in tracker.get('phases', [])
                       for t in p.get('tasks', [])
                       if p.get('status') == 'in_progress' and t.get('agent') != agent_name and t.get('status') == 'in_progress']
            if parallel:
                output_parts.append("")
                output_parts.append(f"⚡ RUNNING IN PARALLEL WITH: {', '.join(set(parallel))}")
                output_parts.append("Avoid modifying the same files as parallel agents.")

    elif plan_info and plan_info['agent_tasks']:
        # Fallback: use parsed TODO file
        output_parts.append(f"📋 TASKS ASSIGNED TO @{agent_name}:")
        if plan_info['plan_id']:
            output_parts.append(f"Plan: {plan_info['plan_id']}")
        for task in plan_info['agent_tasks']:
            phase_label = f"[{task['phase']}] " if task['phase'] else ''
            output_parts.append(f"  ⬜ {phase_label}{task['task']}")

    if output_parts:
        print('\n'.join(output_parts))


def check_workflow_compliance(tracker, completed_agent, ready_phases):
    """Enforce mandatory workflow rules after each agent completes."""
    warnings = []
    if not tracker or not tracker.get('phases'):
        return warnings

    all_agents_used = set(tracker.get('completed_agents', []))
    all_agents_used.add(completed_agent)

    # Collect all agents assigned across all phases
    all_assigned = set()
    developer_phases = []
    tester_phases = []
    verify_tasks = []
    documenter_tasks = []

    for phase in tracker.get('phases', []):
        for task in phase.get('tasks', []):
            agent = task.get('agent', '')
            all_assigned.add(agent)
            if agent == 'developer':
                developer_phases.append(phase['id'])
            if agent == 'tester':
                tester_phases.append(phase['id'])
            if task.get('skill') == 'verify':
                verify_tasks.append(task)
            if agent == 'documenter':
                documenter_tasks.append(task)

    # Rule 1: Developer MUST be paired with tester
    if completed_agent == 'developer' and 'tester' not in all_assigned:
        warnings.append("MANDATORY: Developer completed but NO tester phase in plan. Add @tester with /verify.")

    # Rule 2: After developer completes, tester should be next (or parallel)
    if completed_agent == 'developer':
        next_has_tester = any(
            any(t.get('agent') == 'tester' for t in p.get('tasks', []))
            for p in (ready_phases or [])
        )
        if not next_has_tester and 'tester' not in all_agents_used:
            warnings.append("EXPECTED: Tester should run after developer. Check plan sequence.")

    # Rule 3: /verify should be in the plan when tester is assigned
    if 'tester' in all_assigned and not verify_tasks:
        warnings.append("RECOMMENDED: Tester assigned but no /verify skill in plan. Consider adding /verify L2.")

    # Rule 4: Documenter should be in every plan
    if not documenter_tasks:
        warnings.append("MANDATORY: No @documenter in plan. Every plan must include documenter as final agent.")

    # Rule 5: When all phases complete, verify documenter ran
    all_done = all(p.get('status') == 'completed' for p in tracker.get('phases', []))
    if all_done:
        if 'documenter' not in all_agents_used:
            warnings.append("PLAN COMPLETE but documenter never ran. Invoke @documenter before closing.")
        if 'tester' in all_assigned and 'tester' not in all_agents_used:
            warnings.append("PLAN COMPLETE but tester never ran. Testing was skipped!")
        # Check if verify ran
        verify_completed = any(
            t.get('status') == 'completed' for t in verify_tasks
        )
        if verify_tasks and not verify_completed:
            warnings.append("PLAN COMPLETE but /verify never completed. Run /verify before closing.")

    return warnings


def handle_subagent_stop(data, claude_dir):
    """Track completion and inject next-agent guidance"""
    agent_name = data.get('agent_name', '') or data.get('subagent_type', '')
    if not agent_name:
        return

    tracker_path = get_tracker_path(claude_dir)
    tracker = load_tracker(tracker_path)

    if not tracker:
        # No active tracker — just provide a generic reminder
        print(f"✅ @{agent_name} completed.")

        # Check if there's a TODO file to extract next steps
        todo_path = find_active_plan(claude_dir)
        if todo_path:
            content = todo_path.read_text()
            # Simple: find any agent mentions after this agent
            lines = content.split('\n')
            found_current = False
            next_agents = []
            for line in lines:
                if f'@{agent_name}' in line:
                    found_current = True
                    continue
                if found_current and '@' in line:
                    import re
                    agents = re.findall(r'@([\w-]+)', line)
                    for a in agents:
                        if a not in next_agents and a != agent_name:
                            next_agents.append(a)

            if next_agents:
                print(f"📌 NEXT IN PLAN: @{next_agents[0]}")
                if len(next_agents) > 1:
                    print(f"   Then: {', '.join('@' + a for a in next_agents[1:3])}")

        print(f"💾 Consider: /commit to checkpoint this agent's work before continuing.")
        return

    # Update tracker: mark this agent's tasks as completed
    if agent_name not in tracker.get('completed_agents', []):
        tracker.setdefault('completed_agents', []).append(agent_name)

    # Mark tasks completed
    for phase in tracker.get('phases', []):
        phase_all_done = True
        for task in phase.get('tasks', []):
            if task.get('agent') == agent_name and task.get('status') != 'completed':
                task['status'] = 'completed'
                task['completed_at'] = datetime.now().isoformat()
            if task.get('status') != 'completed':
                phase_all_done = False
        if phase_all_done and phase.get('tasks'):
            phase['status'] = 'completed'

    # Find next ready phases/agents
    ready_phases = extract_parallel_groups(tracker)

    # Build output
    output_parts = []
    output_parts.append(f"✅ @{agent_name} completed.")

    # Progress summary
    total_phases = len(tracker.get('phases', []))
    completed_phases = len([p for p in tracker.get('phases', []) if p.get('status') == 'completed'])
    output_parts.append(f"📊 Progress: {completed_phases}/{total_phases} phases complete")

    if ready_phases:
        if len(ready_phases) == 1:
            phase = ready_phases[0]
            agents = list(set(t.get('agent') for t in phase.get('tasks', []) if t.get('status') != 'completed'))
            output_parts.append(f"📌 NEXT: Phase '{phase.get('title', phase.get('id'))}' → @{', @'.join(agents)}")
        else:
            # Multiple phases ready = parallel opportunity (capped at 3 to prevent API overload)
            MAX_PARALLEL = 3
            total_agents = sum(
                len([t for t in phase.get('tasks', []) if t.get('status') != 'completed'])
                for phase in ready_phases
            )
            if total_agents > MAX_PARALLEL:
                output_parts.append(f"⚡ PARALLEL OPPORTUNITY: {len(ready_phases)} phases ready, but capping at {MAX_PARALLEL} concurrent agents to prevent API overload.")
                output_parts.append(f"   ⚠️  {total_agents} agents requested — stagger into batches of {MAX_PARALLEL}.")
            else:
                output_parts.append(f"⚡ PARALLEL OPPORTUNITY: {len(ready_phases)} phases can run simultaneously:")
            for phase in ready_phases:
                agents = list(set(t.get('agent') for t in phase.get('tasks', []) if t.get('status') != 'completed'))
                output_parts.append(f"   • '{phase.get('title', phase.get('id'))}' → @{', @'.join(agents)}")
            output_parts.append("   Launch agents in the SAME message for parallel execution (max 3 at a time).")
    else:
        # Check if all done
        all_done = all(p.get('status') == 'completed' for p in tracker.get('phases', []))
        if all_done:
            output_parts.append("🎉 ALL PHASES COMPLETE. Run /commit for final checkpoint.")
        else:
            output_parts.append("⏳ Waiting for dependencies to complete before next phase.")

    # === WORKFLOW COMPLIANCE CHECKS ===
    compliance_warnings = check_workflow_compliance(tracker, agent_name, ready_phases)
    if compliance_warnings:
        output_parts.append("")
        output_parts.append("⚠️  WORKFLOW COMPLIANCE:")
        for w in compliance_warnings:
            output_parts.append(f"   {w}")

    # Always suggest commit checkpoint
    output_parts.append(f"💾 /commit to checkpoint @{agent_name}'s work")

    # Save updated tracker
    tracker['last_updated'] = datetime.now().isoformat()
    save_tracker(tracker_path, tracker)

    print('\n'.join(output_parts))


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, IOError):
        data = {}

    event = data.get('event', os.environ.get('CLAUDE_HOOK_EVENT', ''))

    claude_dir = find_claude_dir()
    if not claude_dir:
        return 0

    if event == 'SubagentStart':
        handle_subagent_start(data, claude_dir)
    elif event == 'SubagentStop':
        handle_subagent_stop(data, claude_dir)
    else:
        # Try to detect from context
        agent_name = data.get('agent_name', '')
        if agent_name:
            # Default to stop behavior
            handle_subagent_stop(data, claude_dir)

    return 0


if __name__ == '__main__':
    sys.exit(main())
