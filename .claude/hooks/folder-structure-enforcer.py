#!/usr/bin/env python3
"""
folder structure enforcer Hook
Enhanced Claude Code hook with standardized structure

Hook Type: PostToolUse
Purpose: ...
Triggers: Specific tool operations (see should_process method)
Dependencies: Standard Python libraries
Version: 1.0.0
"""

import sys
import json
import os
from pathlib import Path

# Allowed top-level directories in .claude/
ALLOWED_CLAUDE_DIRECTORIES = {
    'agents', 'commands', 'hooks', 'knowledge', 'memory',
    'skills', 'rules', 'tests', 'artifacts', 'project', 'cleanup',
    'scripts', 'metrics', 'sounds', 'temp',
    'documentation', 'settings.json'
}

# Required subdirectories for each allowed directory
REQUIRED_SUBDIRECTORIES = {
    'tests': {'unit', 'integration', 'e2e', 'performance', 'security', 'reports'},
    'artifacts': {'code', 'design', 'research', 'tests'},
    'project': {'sprint', 'features', 'metrics', 'milestones', 'organization'},
    'cleanup': {'archive', 'deprecated', 'scheduled'}
}

def check_folder_compliance():
    """Check if folder structure complies with standards"""
    project_root = Path.cwd()
    claude_dir = project_root / '.claude'
    
    violations = []
    
    if not claude_dir.exists():
        return violations
    
    # Check for unauthorized top-level directories
    for item in claude_dir.iterdir():
        if item.is_dir() and item.name not in ALLOWED_CLAUDE_DIRECTORIES:
            violations.append({
                'type': 'unauthorized_directory',
                'path': str(item.relative_to(project_root)),
                'message': f"Unauthorized directory '{item.name}' in .claude/. Use existing structure only."
            })
    
    # Check for missing required subdirectories
    for parent_dir, required_subdirs in REQUIRED_SUBDIRECTORIES.items():
        parent_path = claude_dir / parent_dir
        if parent_path.exists():
            existing_subdirs = {d.name for d in parent_path.iterdir() if d.is_dir()}
            missing_subdirs = required_subdirs - existing_subdirs
            
            for missing in missing_subdirs:
                violations.append({
                    'type': 'missing_subdirectory',
                    'path': str(parent_path.relative_to(project_root)),
                    'message': f"Missing required subdirectory '{missing}' in {parent_dir}/"
                })
    
    return violations

def enforce_folder_structure():
    """Enforce folder structure by creating missing directories"""
    project_root = Path.cwd()
    claude_dir = project_root / '.claude'
    
    created_dirs = []
    
    # Create missing required subdirectories
    for parent_dir, required_subdirs in REQUIRED_SUBDIRECTORIES.items():
        parent_path = claude_dir / parent_dir
        if parent_path.exists():
            for subdir in required_subdirs:
                subdir_path = parent_path / subdir
                if not subdir_path.exists():
                    try:
                        subdir_path.mkdir(parents=True, exist_ok=True)
                        created_dirs.append(str(subdir_path.relative_to(project_root)))
                    except Exception as e:
                        print(f"Warning: Could not create {subdir_path}: {e}")
    
    return created_dirs

def generate_compliance_report(violations):
    """Generate a compliance report"""
    if not violations:
        return "✅ Folder structure compliant with Claude Code standards"
    
    report = "🚨 FOLDER STRUCTURE VIOLATIONS DETECTED:\n\n"
    
    unauthorized = [v for v in violations if v['type'] == 'unauthorized_directory']
    missing = [v for v in violations if v['type'] == 'missing_subdirectory']
    
    if unauthorized:
        report += "❌ UNAUTHORIZED DIRECTORIES:\n"
        for violation in unauthorized:
            report += f"   - {violation['path']}: {violation['message']}\n"
        report += "\n"
    
    if missing:
        report += "⚠️  MISSING REQUIRED DIRECTORIES:\n"
        for violation in missing:
            report += f"   - {violation['path']}: {violation['message']}\n"
        report += "\n"
    
    report += "📚 ACTION REQUIRED:\n"
    report += "1. Read /.claude/memory/standards/folder-structure.md\n"
    report += "2. Use established folder structure only\n"
    report += "3. Run /cleanup command to organize files\n"
    
    return report

def main():
    """Main entry point for folder structure enforcement"""
    try:
        # Read input data (tool use information)
        try:
            data = json.load(sys.stdin)
            tool_name = data.get('tool_name', '')
            tool_input = data.get('tool_input', {})
        except:
            # If no input, just run compliance check
            data = {}
            tool_name = ''
            tool_input = {}
        
        # Only run on file system operations that could create directories
        relevant_tools = ['Write', 'MultiEdit', 'mcp__filesystem__write_file', 
                         'mcp__filesystem__create_directory', 'Task']
        
        if tool_name in relevant_tools:
            # Check compliance before and after file operations
            violations = check_folder_compliance()
            
            if violations:
                print(generate_compliance_report(violations))
                
                # Auto-enforce by creating missing directories
                created_dirs = enforce_folder_structure()
                if created_dirs:
                    print(f"\n🔧 Auto-created {len(created_dirs)} missing directories:")
                    for dir_path in created_dirs:
                        print(f"   ✅ {dir_path}")
            
            else:
                print("✅ Folder structure compliance verified")
        
        return 0
        
    except Exception as e:
        print(f"⚠️  Folder structure enforcer error: {str(e)}")
        return 0  # Don't fail the main operation

if __name__ == "__main__":
    sys.exit(main())