#!/usr/bin/env python3
"""
Unified Context Processor Hook
Consolidates functionality from context-injection.py, enhanced-agent-context.py, and smart-error-context.py

Hook Type: PostToolUse
Purpose: Unified context injection with smart conditional execution
Triggers: Major operations (Task, TodoWrite, MultiEdit) and error conditions
Dependencies: Standard Python libraries
Version: 2.0.0
Author: Developer Agent
Date: 2025-10-05
"""

import json
import sys
import os
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any


class UnifiedContextProcessor:
    """Unified context processor combining project details, agent tracking, and error context"""
    
    def __init__(self):
        self.active_operations = {}
        self.agent_skills = {}
        self.current_phase = None
        self.plan_context = None
        self.error_history = []
        
    def should_process_operation(self, tool_name: str, tool_input: Dict[str, Any]) -> bool:
        """Determine if operation needs context processing"""
        
        # High priority operations - always process
        high_priority_tools = {
            'Task', 'TodoWrite', 'MultiEdit', 'Write', 'Edit', 
            'NotebookEdit', 'Bash'
        }
        
        # Skip simple read operations unless they involve important files
        if tool_name in ['Read', 'Glob', 'LS']:
            path = tool_input.get('path', '') or tool_input.get('file_path', '')
            if path:
                important_patterns = [
                    '/agents/', '/knowledge/', '/memory/', '/standards/',
                    'package.json', 'requirements.txt', '.claude'
                ]
                return any(pattern in path for pattern in important_patterns)
            return False
            
        # Process high priority tools
        if tool_name in high_priority_tools:
            return True
            
        # Process if agent delegation detected
        if tool_name == 'Task' and tool_input.get('subagent_type'):
            return True
            
        return False
    
    def get_project_context(self) -> str:
        """Generate project context (from context-injection.py)"""
        try:
            cwd = Path.cwd()
            project_name = cwd.name

            context_lines = [
                "🚀 PM MODE ACTIVE",
                "",
                "Main Claude is operating as PM (Project Manager) with:",
                "  - ✅ PM instructions from /.claude/agents/pm.md",
                "  - ✅ Full Task tool access for agent coordination",
                "  - ✅ On-demand knowledge loading capability",
                "  - ✅ Automatic routing and coordination",
                "",
                "Make natural requests without any prefix - PM will analyze, plan, and coordinate.",
                "",
                "---",
                "",
                "📁 Project Details",
                "",
                f"  - Project: {project_name}",
                f"  - Location: {cwd}",
                "  - Type: Claude Code Multi-Agent Development System",
                "",
                "🔍 Project Type Detection",
                "",
            ]
            
            # Check for project type indicators
            if (cwd / '.claude').exists():
                context_lines.append("  - 🤖 Claude Code setup detected (.claude directory)")
            
            if (cwd / 'package.json').exists():
                context_lines.append("  - 📦 Node.js project detected (package.json)")
                
            # Check for Python indicators
            python_files = ['requirements.txt', 'pyproject.toml', 'setup.py']
            python_detected = any((cwd / f).exists() for f in python_files)
            hook_dir = cwd / '.claude' / 'hooks'
            if python_detected or (hook_dir.exists() and any(hook_dir.glob('*.py'))):
                context_lines.append("  - 🐍 Python project detected (Python hooks and scripts)")
            
            # System Architecture
            context_lines.extend([
                "",
                "🏗️ System Architecture",
                "",
                "  - 13 Specialized Agents: PM, Developer, Orchestrator, Tester, Reviewer, Architect, Documenter, Researcher, Business Analyst, UX Designer, Security, Data, Product Manager",
                "  - Organized Knowledge Base: .claude/knowledge/ with 100+ specialized files",
                "  - Hook System: 20+ operational hooks in .claude/hooks/",
                "  - Memory System: Project context storage in .claude/memory/",
                "",
                "📋 Standards & Conventions",
                "",
                "  - Standards Location: /.claude/memory/standards/conventions.md",
                "  - File Organization: /.claude/memory/standards/tree.md",
                "  - Knowledge Index: /.claude/knowledge/INDEX.md",
                "  - Agent Configurations: Individual agent files in /.claude/agents/"
            ])
            
            return '\n'.join(context_lines)
            
        except Exception:
            return (
                "📁 Project Details\n"
                f"  - Project: {Path.cwd().name}\n"
                "  - Type: Claude Code Multi-Agent Development System\n"
                "\n"
                "🤖 Claude Code setup detected and ready for development"
            )
    
    def get_agent_emoji(self, agent_name: str) -> str:
        """Get emoji for agent types (from enhanced-agent-context.py)"""
        agent_emojis = {
            'pm': '📋',
            'developer': '💻', 
            'architect': '🏗️',
            'tester': '🧪',
            'reviewer': '🔍',
            'documenter': '📝',
            'orchestrator': '🎭',
            'researcher': '🔬',
            'product-manager': '🎯',
            'business-analyst': '📊',
            'ux-designer': '🎨',
            'security': '🔒',
            'data': '📈'
        }
        return agent_emojis.get(agent_name, '🤖')
    
    def detect_agent_from_operation(self, tool_name: str, tool_input: Dict[str, Any]) -> Optional[str]:
        """Detect which agent is likely performing this operation"""
        
        # Task tool indicates agent delegation
        if tool_name == "Task":
            subagent = tool_input.get("subagent_type", "")
            return subagent
            
        # Knowledge file patterns
        path = tool_input.get("path", "") or tool_input.get("file_path", "")
        if path:
            if '/agents/' in path:
                for agent in ['pm', 'developer', 'architect', 'tester', 'reviewer', 
                             'documenter', 'orchestrator', 'researcher', 'product-manager',
                             'business-analyst', 'ux-designer', 'security', 'data']:
                    if agent in path:
                        return agent
            
            # Specialized knowledge patterns
            if '/specialized/pm/' in path:
                return 'pm'
            elif '/specialized/developer/' in path:
                return 'developer'
            elif '/specialized/architect/' in path:
                return 'architect'
                
        return None
    
    def get_skill_context(self, path: str) -> Optional[str]:
        """Extract skill context from file path"""
        if not path:
            return None
            
        skill_patterns = {
            'python-pro': '🐍 Python Pro',
            'javascript-pro': '🟨 JS Expert', 
            'typescript-pro': '🔷 TS Expert',
            'ai-llm-expert': '🤖 LLM Expert',
            'database-expert': '🗄️ DB Expert',
            'planning-protocol': '📋 Planning',
            'agent-coordination': '🤝 Coordination',
            'chain-of-thought': '🧠 Deep Think',
            'security-expert': '🔒 Security',
            'git-commit-expert': '📝 Git Expert'
        }
        
        filename = Path(path).name.lower()
        for pattern, description in skill_patterns.items():
            if pattern in filename:
                return description
                
        return None
    
    def get_error_type_emoji(self, error_type: str) -> str:
        """Get emoji for different error types (from smart-error-context.py)"""
        emojis = {
            'syntax': '🔤',
            'type': '🔷',
            'runtime': '💥',
            'import': '📦',
            'network': '🌐',
            'permission': '🔒',
            'file': '📁',
            'validation': '✅',
            'compile': '⚙️',
            'test': '🧪',
            'lint': '🔍',
            'format': '🎨',
            'general': '❌'
        }
        return emojis.get(error_type, '❌')
    
    def detect_error_type(self, error_message: str) -> str:
        """Detect the type of error from the message"""
        error_message_lower = error_message.lower()
        
        if 'syntaxerror' in error_message_lower or 'unexpected token' in error_message_lower:
            return 'syntax'
        elif 'typeerror' in error_message_lower or 'type ' in error_message_lower:
            return 'type'
        elif 'importerror' in error_message_lower or 'cannot find module' in error_message_lower:
            return 'import'
        elif 'permission' in error_message_lower or 'access denied' in error_message_lower:
            return 'permission'
        elif 'file not found' in error_message_lower or 'enoent' in error_message_lower:
            return 'file'
        elif 'validation' in error_message_lower or 'invalid' in error_message_lower:
            return 'validation'
        elif 'compile' in error_message_lower or 'compilation' in error_message_lower:
            return 'compile'
        elif 'test' in error_message_lower or 'assertion' in error_message_lower:
            return 'test'
        elif 'lint' in error_message_lower or 'eslint' in error_message_lower:
            return 'lint'
        elif 'network' in error_message_lower or 'connection' in error_message_lower:
            return 'network'
        else:
            return 'general'
    
    def extract_file_location(self, error_message: str) -> Optional[Dict[str, str]]:
        """Extract file path and line number from error message"""
        patterns = [
            r'File "([^"]+)", line (\d+)',  # Python
            r'at ([^:]+):(\d+):(\d+)',       # JavaScript/TypeScript
            r'([^:]+):(\d+):(\d+)',           # Generic
            r'in ([^:]+) on line (\d+)',     # PHP-style
            r'([^(]+)\((\d+),(\d+)\)',       # Windows-style
        ]
        
        for pattern in patterns:
            match = re.search(pattern, error_message)
            if match:
                file_path = match.group(1)
                line_num = match.group(2)
                col_num = match.group(3) if len(match.groups()) >= 3 else None
                
                return {
                    'file': file_path,
                    'line': line_num,
                    'column': col_num
                }
        
        return None
    
    def get_suggestion_for_error(self, error_type: str, error_message: str) -> List[str]:
        """Generate helpful suggestions based on error type"""
        suggestions = []
        
        if error_type == 'syntax':
            suggestions.append("💡 Check for missing brackets, quotes, or semicolons")
            suggestions.append("💡 Verify indentation (spaces vs tabs)")
            
        elif error_type == 'type':
            suggestions.append("💡 Check variable types and function parameters")
            suggestions.append("💡 Use TypeScript or type hints for better type safety")
            
        elif error_type == 'import':
            module_match = re.search(r"'([^']+)'|\"([^\"]+)\"", error_message)
            if module_match:
                module = module_match.group(1) or module_match.group(2)
                suggestions.append(f"💡 Try: npm install {module} or pip install {module}")
            suggestions.append("💡 Check import paths and module names")
            
        elif error_type == 'permission':
            suggestions.append("💡 Check file permissions with ls -la")
            suggestions.append("💡 Try running with elevated permissions if needed")
            
        elif error_type == 'file':
            suggestions.append("💡 Verify the file path exists")
            suggestions.append("💡 Check for typos in the filename")
            
        elif error_type == 'network':
            suggestions.append("💡 Check network connectivity")
            suggestions.append("💡 Verify API endpoints and credentials")
            
        elif error_type == 'validation':
            suggestions.append("💡 Review input data format")
            suggestions.append("💡 Check schema or validation rules")
            
        elif error_type == 'compile':
            suggestions.append("💡 Check syntax and type definitions")
            suggestions.append("💡 Review compiler configuration")
            
        elif error_type == 'test':
            suggestions.append("💡 Review test expectations and assertions")
            suggestions.append("💡 Check test data and mocks")
            
        elif error_type == 'lint':
            suggestions.append("💡 Run auto-fix: npm run lint:fix or similar")
            suggestions.append("💡 Review linting rules in config")
        
        return suggestions
    
    def format_agent_operation(self, tool_name: str, tool_input: Dict[str, Any]) -> Optional[str]:
        """Format operation with enhanced agent context"""
        
        agent = self.detect_agent_from_operation(tool_name, tool_input)
        
        if tool_name == "Task" and agent:
            # Agent delegation - high priority
            description = tool_input.get("description", "")
            agent_emoji = self.get_agent_emoji(agent)
            return f"🎯 DELEGATION: {agent_emoji} {agent.title()} → {description}"
            
        elif "knowledge" in tool_input.get("path", "").lower() or "agents" in tool_input.get("path", "").lower():
            # Knowledge/skill loading - medium priority
            path = tool_input.get("path", "") or tool_input.get("file_path", "")
            skill = self.get_skill_context(path)
            
            if agent and skill:
                agent_emoji = self.get_agent_emoji(agent)
                return f"🚀 {agent.title()} loading: {skill}"
            elif skill:
                return f"📚 Loading: {skill}"
                
        return None
    
    def format_error_context(self, error_message: str, tool_name: str = "", file_path: str = "") -> str:
        """Format error with rich context"""
        error_type = self.detect_error_type(error_message)
        emoji = self.get_error_type_emoji(error_type)
        
        # Extract location if not provided
        location = self.extract_file_location(error_message)
        if location and not file_path:
            file_path = location['file']
        
        # Build formatted output
        lines = []
        
        # Header with error type
        if file_path and location:
            lines.append(f"{emoji} {error_type.title()} Error in {file_path}:{location['line']}")
        elif file_path:
            lines.append(f"{emoji} {error_type.title()} Error in {file_path}")
        else:
            lines.append(f"{emoji} {error_type.title()} Error")
        
        # Error message (truncated if too long)
        error_lines = error_message.split('\n')
        key_line = error_lines[0] if error_lines else error_message
        if len(key_line) > 100:
            key_line = key_line[:97] + "..."
        lines.append(f"   → {key_line}")
        
        # Add code context if we have location
        if location and location.get('line'):
            lines.append(f"   📍 Line {location['line']}" + 
                        (f", Column {location['column']}" if location.get('column') else ""))
        
        # Add suggestions
        suggestions = self.get_suggestion_for_error(error_type, error_message)
        for suggestion in suggestions:
            lines.append(f"   {suggestion}")
        
        # Add quick actions if applicable
        if error_type == 'lint':
            lines.append("   🔧 Quick fix: Run formatter/linter with --fix flag")
        elif error_type == 'type' and 'typescript' in error_message.lower():
            lines.append("   🔧 Quick fix: Add type annotations or use 'any' temporarily")
        
        return "\n".join(lines)
    
    def analyze_error_patterns(self) -> Optional[str]:
        """Analyze patterns in error history"""
        if len(self.error_history) < 3:
            return None
        
        # Check for repeated errors
        error_types = [self.detect_error_type(e) for e in self.error_history[-5:]]
        most_common = max(set(error_types), key=error_types.count)
        
        if error_types.count(most_common) >= 3:
            return f"⚠️ Pattern detected: Repeated {most_common} errors. Consider addressing the root cause."
        
        return None
    
    def process_operation(self, tool_name: str, tool_input: Dict[str, Any], tool_response: str = "") -> Optional[Dict[str, Any]]:
        """Main processing method for unified context"""
        
        # Skip processing if not needed
        if not self.should_process_operation(tool_name, tool_input):
            return None
        
        context_messages = []
        
        # 1. Process agent operations
        agent_context = self.format_agent_operation(tool_name, tool_input)
        if agent_context:
            context_messages.append(agent_context)
        
        # 2. Process errors in tool response
        if tool_response and isinstance(tool_response, str):
            has_error = any(indicator in tool_response.lower() 
                          for indicator in ['error', 'failed', 'exception', 'traceback'])
            
            if has_error:
                # Track in history
                self.error_history.append(tool_response)
                
                # Format error with context
                formatted_error = self.format_error_context(tool_response, tool_name)
                context_messages.append(formatted_error)
                
                # Check for patterns
                pattern_warning = self.analyze_error_patterns()
                if pattern_warning:
                    context_messages.append(pattern_warning)
        
        # 3. Add project context for Task operations
        if tool_name == "Task":
            project_context = self.get_project_context()
            context_messages.append(project_context)
        
        # Return formatted context if any messages exist
        if context_messages:
            return {
                "continue": True,
                "suppressOutput": False,
                "systemMessage": "\n\n".join(context_messages)
            }
        
        return None


def main():
    """Main entry point for the unified context processor hook"""
    try:
        # Prevent duplicate execution for context-injection compatibility
        lock_file = Path.cwd() / '.claude' / 'hooks' / '.unified-context.lock'
        current_time = time.time()
        
        # Check if already executed recently (5 second window)
        if lock_file.exists():
            try:
                with open(lock_file, 'r') as f:
                    last_run = float(f.read().strip())
                if current_time - last_run < 5:
                    return 0  # Skip duplicate execution
            except:
                pass  # If lock file is invalid, continue
        
        # Read input from stdin
        try:
            data = json.load(sys.stdin)
        except:
            data = {}
        
        tool_name = data.get("tool_name", "")
        tool_input = data.get("tool_input", {})
        tool_response = data.get("tool_response", "")
        
        # Process with unified context processor
        processor = UnifiedContextProcessor()
        result = processor.process_operation(tool_name, tool_input, tool_response)
        
        if result:
            # Update tool response if error formatting was applied
            if tool_response and any(indicator in tool_response.lower() 
                                   for indicator in ['error', 'failed', 'exception', 'traceback']):
                # Extract formatted error from result
                formatted_error = None
                for msg in result["systemMessage"].split("\n\n"):
                    if any(emoji in msg for emoji in ['🔤', '🔷', '💥', '📦', '🌐', '🔒', '📁', '✅', '⚙️', '🧪', '🔍', '🎨', '❌']):
                        formatted_error = msg
                        break
                
                if formatted_error:
                    data['tool_response'] = formatted_error
                    print(json.dumps(data))
                else:
                    print(json.dumps(result))
            else:
                print(json.dumps(result))
        else:
            # Pass through original data if no processing needed
            print(json.dumps(data) if data else "{}")
        
        # Update lock file
        try:
            with open(lock_file, 'w') as f:
                f.write(str(current_time))
        except:
            pass  # If can't write lock file, continue anyway
        
        return 0
        
    except Exception as e:
        # On error, pass through original input or minimal response
        try:
            data = json.load(sys.stdin)
            print(json.dumps(data))
        except:
            print(json.dumps({"error": f"Unified context processor error: {str(e)}"}))
        return 0


if __name__ == "__main__":
    sys.exit(main())
