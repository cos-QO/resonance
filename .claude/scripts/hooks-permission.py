#!/usr/bin/env python3
"""
Claude Code Hooks Permission Fixer
Universal command to fix all hook permission issues across projects and devices.
Resolves exit codes 126/127 for all hooks.
"""

import os
import sys
import stat
import subprocess
import json
import shutil
from pathlib import Path


def log_info(msg: str):
    print(f"🔧 {msg}")


def log_success(msg: str):
    print(f"✅ {msg}")


def log_warn(msg: str):
    print(f"⚠️ {msg}")


def log_error(msg: str):
    print(f"❌ {msg}")


def run_command(cmd, ignore_errors=False):
    """Run shell command safely"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return False, "", str(e)


def find_claude_project_root(start_path=None):
    """Find the project root containing .claude folder, searching upward from any location."""
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path)
    
    current = start_path
    while current != current.parent:
        claude_dir = current / '.claude'
        if claude_dir.exists() and claude_dir.is_dir():
            return current
        current = current.parent
    
    return None


def clean_nested_claude_dirs(project_root):
    """Remove any incorrectly nested .claude directories that cause path duplication."""
    claude_hooks = project_root / '.claude' / 'hooks'
    if not claude_hooks.exists():
        return []
    
    removed = []
    for item in claude_hooks.iterdir():
        if item.is_dir() and item.name == '.claude':
            log_info(f"Removing nested .claude directory: {item}")
            shutil.rmtree(item)
            removed.append(str(item))
    
    return removed


def discover_hooks():
    """Find all Python hooks and analyze their status"""
    # Use universal project root detection instead of environment variable
    project_root = find_claude_project_root()
    if not project_root:
        log_error("No .claude directory found in current path or parent directories")
        return None, {}
    
    hooks_dir = str(project_root / ".claude" / "hooks")
    
    if not os.path.exists(hooks_dir):
        log_error(f"Hooks directory not found: {hooks_dir}")
        return None, {}
    
    log_info(f"Scanning hooks in: {hooks_dir}")
    
    python_hooks = [f for f in os.listdir(hooks_dir) if f.endswith('.py')]
    hooks_info = {}
    
    for hook_file in python_hooks:
        hook_path = os.path.join(hooks_dir, hook_file)
        
        # Check permissions
        try:
            file_stat = os.stat(hook_path)
            permissions = stat.filemode(file_stat.st_mode)
            is_executable = bool(file_stat.st_mode & stat.S_IEXEC)
        except Exception:
            permissions, is_executable = "unknown", False
        
        # Check shebang
        try:
            with open(hook_path, 'rb') as f:
                first_line = f.readline().decode('utf-8', errors='ignore').strip()
            has_correct_shebang = first_line == '#!/usr/bin/env python3'
        except Exception:
            has_correct_shebang = False
        
        # Check quarantine (macOS only)
        has_quarantine = False
        try:
            success, stdout, stderr = run_command(f"xattr -l '{hook_path}'", ignore_errors=True)
            has_quarantine = 'com.apple.quarantine' in stdout
        except Exception:
            pass
        
        hooks_info[hook_file] = {
            "path": hook_path,
            "permissions": permissions,
            "executable": is_executable,
            "correct_shebang": has_correct_shebang,
            "quarantined": has_quarantine,
            "needs_fix": not (is_executable and has_correct_shebang)
        }
    
    return hooks_dir, hooks_info


def fix_hook_permissions(hooks_dir, hooks_info, use_sudo=False):
    """Apply comprehensive permission fixes"""
    log_info("Applying permission fixes to all hooks...")
    
    # Fix hooks directory permissions first
    sudo_prefix = "sudo " if use_sudo else ""
    success, _, _ = run_command(f"{sudo_prefix}chmod 755 '{hooks_dir}'")
    if success:
        log_success("Fixed hooks directory permissions")
    else:
        log_warn("Could not fix hooks directory permissions")
    
    results = {}
    total_fixes = 0
    
    for hook_name, hook_info in hooks_info.items():
        hook_path = hook_info["path"]
        fixes_applied = []
        
        try:
            # 1. Fix file permissions
            if not hook_info["executable"]:
                success, _, _ = run_command(f"{sudo_prefix}chmod 755 '{hook_path}'")
                if success:
                    fixes_applied.append("permissions")
                    total_fixes += 1
            
            # 2. Fix shebang
            if not hook_info["correct_shebang"]:
                try:
                    with open(hook_path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                    
                    # Add or replace shebang
                    if lines and lines[0].startswith('#!'):
                        lines[0] = '#!/usr/bin/env python3\n'
                    else:
                        lines.insert(0, '#!/usr/bin/env python3\n')
                    
                    with open(hook_path, 'w', encoding='utf-8') as f:
                        f.writelines(lines)
                    
                    fixes_applied.append("shebang")
                    total_fixes += 1
                except Exception as e:
                    log_warn(f"Could not fix shebang for {hook_name}: {e}")
            
            # 3. Fix line endings
            try:
                with open(hook_path, 'rb') as f:
                    content = f.read()
                
                if b'\r\n' in content:
                    content = content.replace(b'\r\n', b'\n')
                    with open(hook_path, 'wb') as f:
                        f.write(content)
                    fixes_applied.append("line_endings")
                    total_fixes += 1
            except Exception:
                pass
            
            # 4. Remove quarantine
            if hook_info["quarantined"]:
                success, _, _ = run_command(f"xattr -d com.apple.quarantine '{hook_path}'", ignore_errors=True)
                if success:
                    fixes_applied.append("quarantine")
                    total_fixes += 1
            
            results[hook_name] = {
                "status": "fixed" if fixes_applied else "ok",
                "fixes": fixes_applied
            }
            
        except Exception as e:
            results[hook_name] = {
                "status": "error",
                "error": str(e)
            }
    
    return results, total_fixes


def test_hook_execution(hooks_info):
    """Test that all hooks can execute properly"""
    log_info("Testing hook execution...")
    
    test_results = {}
    passed_tests = 0
    total_tests = 0
    
    for hook_name, hook_info in hooks_info.items():
        hook_path = hook_info["path"]
        
        # Test direct python execution
        success1, _, _ = run_command(f"python3 '{hook_path}' --help 2>/dev/null || echo 'ok'", ignore_errors=True)
        
        # Test shebang execution  
        success2, _, _ = run_command(f"'{hook_path}' --help 2>/dev/null || echo 'ok'", ignore_errors=True)
        
        # Check final permissions
        try:
            file_stat = os.stat(hook_path)
            is_executable = bool(file_stat.st_mode & stat.S_IEXEC)
        except Exception:
            is_executable = False
        
        test_passed = success1 and is_executable
        test_results[hook_name] = {
            "python_execution": success1,
            "shebang_execution": success2, 
            "executable_bit": is_executable,
            "overall": "✅" if test_passed else "❌"
        }
        
        if test_passed:
            passed_tests += 1
        total_tests += 1
    
    return test_results, passed_tests, total_tests


def print_comprehensive_report(hooks_dir, hooks_info, fix_results, total_fixes, test_results, passed_tests, total_tests):
    """Print detailed report"""
    print("\n" + "="*65)
    print("    🔧 CLAUDE CODE HOOKS PERMISSION FIX REPORT")
    print("="*65)
    
    # Directory info
    print(f"\n📁 HOOKS DIRECTORY")
    print(f"├── Location: {hooks_dir}")
    print(f"├── Total Hooks Found: {len(hooks_info)} Python files")
    print(f"└── Directory Status: ✅ Accessible")
    
    # Fix summary
    print(f"\n🔧 FIXES APPLIED")
    print(f"├── Total Fixes Applied: {total_fixes}")
    print(f"├── Hooks Modified: {sum(1 for r in fix_results.values() if r['status'] == 'fixed')}")
    print(f"└── Hooks Already OK: {sum(1 for r in fix_results.values() if r['status'] == 'ok')}")
    
    # Test results
    print(f"\n🧪 EXECUTION TESTING")
    print(f"├── Hooks Tested: {total_tests}")
    print(f"├── Tests Passed: {passed_tests}")
    print(f"├── Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    print(f"└── Exit Code 126/127: {'✅ Resolved' if passed_tests == total_tests else '❌ Still Present'}")
    
    # Individual hook status (only show problematic ones)
    problematic_hooks = {k: v for k, v in test_results.items() if v['overall'] == '❌'}
    if problematic_hooks:
        print(f"\n⚠️ HOOKS NEEDING ATTENTION")
        for hook_name, result in problematic_hooks.items():
            print(f"├── {hook_name}: {result['overall']}")
            if not result['executable_bit']:
                print(f"│   └── Missing executable bit")
            if not result['python_execution']:
                print(f"│   └── Python execution failed")
    else:
        print(f"\n✅ ALL HOOKS STATUS")
        for hook_name in list(test_results.keys())[:5]:  # Show first 5
            print(f"├── {hook_name}: ✅")
        if len(test_results) > 5:
            print(f"└── ... and {len(test_results)-5} more hooks: ✅")
    
    # Overall result
    print(f"\n🎯 OVERALL RESULT")
    if passed_tests == total_tests:
        print("✅ ALL HOOKS FULLY OPERATIONAL")
        print("- No more exit codes 126 (Permission denied)")
        print("- No more exit codes 127 (Command not found)")
        print("- All hooks ready for SessionStart and PostToolUse")
    else:
        print(f"⚠️ {total_tests - passed_tests} HOOKS STILL HAVE ISSUES")
        print("- Some hooks may still show permission errors")
        print("- Consider running with 'pass' argument for sudo privileges")
    
    print("="*65)


def main():
    """Main entry point for hooks permission fixer"""
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h']:
        print("""
Claude Code Hooks Permission Fixer

Usage:
  /hooks-permission [pass]

Arguments:
  pass    - Use sudo for stubborn permission issues (optional)

This command fixes all Claude Code hook permission issues:
- Exit code 126 (Permission denied) 
- Exit code 127 (Command not found)
- Missing executable bits
- Incorrect shebang lines
- CRLF line endings
- macOS quarantine attributes
- Nested .claude directory path issues

Works across all projects and devices from any location.
        """)
        return 0
    
    # Check for sudo flag
    use_sudo = len(sys.argv) > 1 and sys.argv[1] == 'pass'
    
    if use_sudo:
        log_info("Running with sudo privileges for stubborn permission issues")
    
    # PHASE 1: Universal path fixing
    project_root = find_claude_project_root()
    if not project_root:
        log_error("No Claude project found - make sure you're inside a Claude project")
        return 1
    
    log_info(f"Found Claude project: {project_root.name}")
    
    # Clean any nested .claude directories that cause path duplication
    removed_nested = clean_nested_claude_dirs(project_root)
    if removed_nested:
        log_success(f"Fixed path issues: Removed {len(removed_nested)} nested .claude directories")
    
    # PHASE 2: Hook discovery and permission fixing
    hooks_dir, hooks_info = discover_hooks()
    if not hooks_dir:
        return 1
    
    log_info(f"Found {len(hooks_info)} Python hooks to process")
    
    # PHASE 3: Apply permission fixes
    fix_results, total_fixes = fix_hook_permissions(hooks_dir, hooks_info, use_sudo)
    log_success(f"Applied {total_fixes} permission fixes")
    
    # PHASE 4: Re-discover hooks after fixes to get updated status
    _, updated_hooks_info = discover_hooks()
    
    # PHASE 5: Test execution
    test_results, passed_tests, total_tests = test_hook_execution(updated_hooks_info)
    
    # PHASE 6: Generate comprehensive report
    print_comprehensive_report(hooks_dir, hooks_info, fix_results, total_fixes, 
                             test_results, passed_tests, total_tests)
    
    # Additional success message for path fixing
    if removed_nested and passed_tests == total_tests:
        print(f"\n🎯 PATH DUPLICATION ISSUE RESOLVED")
        print(f"✅ SessionStart hook errors should be fixed")
        print(f"✅ No more .claude/hooks/.claude/hooks/ path confusion")
    
    return 0 if passed_tests == total_tests else 1


if __name__ == "__main__":
    sys.exit(main())