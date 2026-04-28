#!/usr/bin/env python3
"""
todo sync Hook
Enhanced Claude Code hook with standardized structure

Hook Type: PostToolUse
Purpose: ...
Triggers: Specific tool operations (see should_process method)
Dependencies: Standard Python libraries
Version: 1.0.0
"""

import json
import sys
import re
import os
from datetime import datetime

def detect_todo_completion(tool_input, tool_response, agent_name):
    """Detect if agent completed a TODO item"""
    
    # Look for TODO completion indicators
    completion_patterns = [
        r'TODO-(\d{8}-[A-Z]\d+-\d+)',  # Simplified format
        r'completed.*TODO-(\d{8}-[A-Z]\d+-\d+)',
        r'finished.*TODO-(\d{8}-[A-Z]\d+-\d+)',
        r'✅.*TODO-(\d{8}-[A-Z]\d+-\d+)',
        r'done.*TODO-(\d{8}-[A-Z]\d+-\d+)',
        r'complete.*TODO-(\d{8}-[A-Z]\d+-\d+)'
    ]
    
    content = str(tool_input) + str(tool_response)
    
    for pattern in completion_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            return f"TODO-{match}"
    
    return None

def detect_todo_start(tool_input, tool_response, agent_name):
    """Detect if agent started working on a TODO item"""
    
    start_patterns = [
        r'starting.*TODO-(\d{8}-[A-Z]\d+-\d+)',
        r'begin.*TODO-(\d{8}-[A-Z]\d+-\d+)',
        r'working on.*TODO-(\d{8}-[A-Z]\d+-\d+)',
        r'🔄.*TODO-(\d{8}-[A-Z]\d+-\d+)'
    ]
    
    content = str(tool_input) + str(tool_response)
    
    for pattern in start_patterns:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            return f"TODO-{match}"
    
    return None

def update_todo_file(todoid, agent_name, status="completed"):
    """Update persistent TODO file with completion"""
    
    try:
        # Extract plan code from todoID (TODO-20251122-A1-001 → A1)
        plan_match = re.search(r'TODO-\d{8}-([A-Z]\d+)-\d+', todoid)
        if not plan_match:
            return False
        
        plan_code = plan_match.group(1)
        
        # Find .claude dir dynamically
        claude_dir = None
        current = os.path.dirname(os.path.abspath(__file__))
        # Walk up from hooks/ to find .claude/
        while current != os.path.dirname(current):
            if os.path.basename(current) == '.claude' or os.path.basename(current) == 'claude':
                claude_dir = current
                break
            if os.path.isdir(os.path.join(current, '.claude')):
                claude_dir = os.path.join(current, '.claude')
                break
            current = os.path.dirname(current)

        # Fallback to env var
        if not claude_dir:
            project_dir = os.environ.get('CLAUDE_PROJECT_DIR', '')
            if project_dir:
                for name in ['.claude', 'claude']:
                    candidate = os.path.join(project_dir, name)
                    if os.path.isdir(candidate):
                        claude_dir = candidate
                        break

        if not claude_dir:
            return False

        # Find TODO file through registry
        registry_path = os.path.join(claude_dir, 'memory', 'todos', 'todoid-registry.json')
        if not os.path.exists(registry_path):
            return False
            
        with open(registry_path, 'r') as f:
            registry = json.load(f)
        
        if plan_code not in registry:
            return False
            
        todo_file_path = registry[plan_code].get('todoFile')
        if not todo_file_path or not os.path.exists(todo_file_path):
            return False
        
        # Update TODO file
        with open(todo_file_path, 'r') as f:
            content = f.read()
        
        # Replace TODO status
        timestamp = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
        
        if status == "completed":
            # Update from pending/in-progress to completed
            old_patterns = [
                f"- \\[ \\] \\*\\*{re.escape(todoid)}\\*\\*",
                f"- \\[\ud83d\udd04\\] \\*\\*{re.escape(todoid)}\\*\\*"
            ]
            new_line = f"- [x] **{todoid}**"
            
            # Try both patterns
            for old_pattern in old_patterns:
                if re.search(old_pattern, content):
                    # Add completion info to the line
                    content = re.sub(
                        f"({old_pattern}[^\n]*)",
                        f"\\1 ✅ {timestamp} by @{agent_name}",
                        content
                    )
                    
                    # Also update the checkbox
                    content = re.sub(old_pattern, new_line, content)
                    break
            
        elif status == "in_progress":
            old_pattern = f"- \\[ \\] \\*\\*{re.escape(todoid)}\\*\\*"
            new_line = f"- [🔄] **{todoid}**"
            
            content = re.sub(
                f"({old_pattern}[^\n]*)",
                f"\\1 🔄 Started: {timestamp} by @{agent_name}",
                content
            )
            
            content = re.sub(old_pattern, new_line, content)
        
        # Write updated content
        with open(todo_file_path, 'w') as f:
            f.write(content)
        
        # Update registry
        if plan_code in registry and 'todos' in registry[plan_code]:
            if todoid in registry[plan_code]['todos']:
                registry[plan_code]['todos'][todoid]['status'] = status
                registry[plan_code]['todos'][todoid]['lastUpdated'] = timestamp
                if status == "completed":
                    registry[plan_code]['todos'][todoid]['completed'] = timestamp
                    registry[plan_code]['todos'][todoid]['completedBy'] = agent_name
                elif status == "in_progress":
                    registry[plan_code]['todos'][todoid]['startedBy'] = agent_name
                    registry[plan_code]['todos'][todoid]['started'] = timestamp
        
        with open(registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
        
        return True
        
    except Exception as e:
        # Log error but don't break the pipeline
        return False

def detect_agent_from_context(tool_name, tool_input):
    """Detect agent from tool usage context"""
    
    # PRIORITY 1: Check for subagent_type in Task tool (most accurate)
    if tool_name == 'Task' and 'subagent_type' in tool_input:
        return tool_input['subagent_type']
    
    # PRIORITY 2: Check for subagent_type in any tool input
    if 'subagent_type' in tool_input:
        return tool_input['subagent_type']
    
    # PRIORITY 3: Look for @agent mentions in prompts/descriptions
    prompt = tool_input.get('prompt', '')
    description = tool_input.get('description', '')
    content = prompt + description
    
    agent_patterns = [
        r'@(developer|tester|reviewer|architect|security|documenter|orchestrator|pm|researcher|data|business-analyst|ux-designer|product-manager)'
    ]
    
    for pattern in agent_patterns:
        match = re.search(pattern, content, re.IGNORECASE)
        if match:
            return match.group(1)
    
    # PRIORITY 4: Tool pattern mapping (fallback)
    tool_patterns = {
        'Edit': 'developer',
        'Write': 'developer', 
        'MultiEdit': 'developer',
        'Bash': 'developer',
        'mcp__playwright': 'tester',
        'mcp__puppeteer': 'tester',
        'WebSearch': 'researcher',
        'WebFetch': 'researcher'
    }
    
    for pattern, agent in tool_patterns.items():
        if pattern in tool_name:
            return agent
            
    return 'unknown'

def main():
    """Main entry point for the hook"""
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        
        tool_name = input_data.get('tool_name', '')
        tool_input = input_data.get('tool_input', {})
        tool_response = input_data.get('tool_response', '')
        
        # Skip if no tool response (nothing to sync)
        if not tool_response:
            print(json.dumps(input_data))
            return
        
        # Detect agent from context
        agent_name = detect_agent_from_context(tool_name, tool_input)
        
        # Check for TODO completion
        completed_todo = detect_todo_completion(tool_input, tool_response, agent_name)
        started_todo = detect_todo_start(tool_input, tool_response, agent_name)
        
        response_additions = []
        
        if completed_todo:
            success = update_todo_file(completed_todo, agent_name, "completed")
            
            if success:
                response_additions.append(f"📋 TODO Updated: {completed_todo} marked complete by @{agent_name}")
        
        if started_todo and started_todo != completed_todo:
            success = update_todo_file(started_todo, agent_name, "in_progress")
            
            if success:
                response_additions.append(f"📋 TODO Started: {started_todo} in progress by @{agent_name}")
        
        # Add confirmations to response if any updates occurred
        if response_additions:
            confirmation = "\n" + "\n".join(response_additions)
            
            if tool_response:
                input_data['tool_response'] = str(tool_response) + confirmation
            else:
                input_data['tool_response'] = confirmation
        
        print(json.dumps(input_data))
        
    except Exception as e:
        # On error, pass through original input without breaking the pipeline
        print(json.dumps(input_data if 'input_data' in locals() else {}))

if __name__ == "__main__":
    main()