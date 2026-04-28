#!/usr/bin/env python3
"""
Hook: chain-checkpoint.py
Trigger: PostToolUse (Task tool)
Purpose: Log and display agent completion checkpoints for chain visibility

This hook provides real-time progress tracking by:
1. Capturing agent completion events
2. Logging to chain-log.jsonl for audit trail
3. Displaying checkpoint notifications in terminal
4. Tracking execution timeline and progress
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Configuration
CHAIN_LOG_PATH = "claude/memory/active/chain-log.jsonl"
MAX_OUTPUT_PREVIEW = 300  # Characters to preview from agent output
CHECKPOINT_EMOJI = "✅"
TIMESTAMP_FORMAT = "%Y-%m-%d %H:%M:%S"


def get_project_root() -> Path:
    """Get project root directory (where claude/ folder exists)."""
    current = Path.cwd()

    # Check if claude/ exists in current directory
    if (current / "claude").exists():
        return current

    # Check parent directories (up to 3 levels)
    for parent in [current.parent, current.parent.parent, current.parent.parent.parent]:
        if (parent / "claude").exists():
            return parent

    # Fallback to current directory
    return current


def ensure_chain_log_exists() -> Path:
    """Ensure chain log file and directory exist."""
    project_root = get_project_root()
    log_path = project_root / CHAIN_LOG_PATH

    # Create directory if needed
    log_path.parent.mkdir(parents=True, exist_ok=True)

    return log_path


def extract_agent_info(tool_input: Dict[str, Any]) -> tuple[str, str]:
    """Extract agent type and task description from Task tool input."""
    agent = tool_input.get("subagent_type", "unknown")
    description = tool_input.get("description", "")

    # Truncate long descriptions
    if len(description) > 100:
        description = description[:97] + "..."

    return agent, description


def create_checkpoint(agent: str, description: str, tool_output: Any) -> Dict[str, Any]:
    """Create checkpoint data structure."""
    now = datetime.now()

    # Extract useful info from tool_output
    output_str = str(tool_output)
    output_preview = output_str[:MAX_OUTPUT_PREVIEW]

    if len(output_str) > MAX_OUTPUT_PREVIEW:
        output_preview += "..."

    checkpoint = {
        "timestamp": now.isoformat(),
        "timestamp_human": now.strftime(TIMESTAMP_FORMAT),
        "agent": agent,
        "task": description,
        "status": "completed",
        "output_preview": output_preview,
        "output_length": len(output_str)
    }

    return checkpoint


def log_checkpoint(checkpoint: Dict[str, Any]) -> None:
    """Append checkpoint to chain log file."""
    try:
        log_path = ensure_chain_log_exists()

        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(checkpoint) + "\n")

    except Exception as e:
        # Don't fail the hook if logging fails
        print(f"⚠️  Warning: Failed to log checkpoint: {e}", file=sys.stderr)


def display_checkpoint(checkpoint: Dict[str, Any]) -> None:
    """Display checkpoint notification in terminal."""
    agent = checkpoint["agent"]
    task = checkpoint["task"]
    timestamp = checkpoint["timestamp_human"]

    print(f"\n{CHECKPOINT_EMOJI} CHECKPOINT: @{agent} completed", flush=True)
    print(f"   Task: {task}", flush=True)
    print(f"   Time: {timestamp}", flush=True)


def get_chain_statistics() -> Optional[Dict[str, Any]]:
    """Get statistics from current chain log."""
    try:
        log_path = ensure_chain_log_exists()

        if not log_path.exists():
            return None

        checkpoints = []
        with open(log_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    checkpoints.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue

        if not checkpoints:
            return None

        # Calculate statistics
        agents = [cp["agent"] for cp in checkpoints]
        unique_agents = set(agents)

        first_timestamp = datetime.fromisoformat(checkpoints[0]["timestamp"])
        last_timestamp = datetime.fromisoformat(checkpoints[-1]["timestamp"])
        duration = (last_timestamp - first_timestamp).total_seconds()

        return {
            "total_checkpoints": len(checkpoints),
            "unique_agents": len(unique_agents),
            "agent_list": list(unique_agents),
            "duration_seconds": duration,
            "start_time": first_timestamp.strftime(TIMESTAMP_FORMAT),
            "last_checkpoint": last_timestamp.strftime(TIMESTAMP_FORMAT)
        }

    except Exception:
        return None


def hook(tool_name: str, tool_input: Dict[str, Any], tool_output: Any) -> None:
    """
    Post-tool hook for Task tool completion.

    Args:
        tool_name: Name of the tool that was executed
        tool_input: Input parameters passed to the tool
        tool_output: Output/result from the tool execution
    """
    # Only process Task tool completions
    if tool_name != "Task":
        return

    # Extract agent information
    agent, description = extract_agent_info(tool_input)

    # Create checkpoint
    checkpoint = create_checkpoint(agent, description, tool_output)

    # Log checkpoint to file
    log_checkpoint(checkpoint)

    # Display checkpoint in terminal
    display_checkpoint(checkpoint)

    # Optional: Display chain statistics periodically (every 5 checkpoints)
    stats = get_chain_statistics()
    if stats and stats["total_checkpoints"] % 5 == 0:
        print(f"\n📊 Chain Progress: {stats['total_checkpoints']} checkpoints | "
              f"{stats['unique_agents']} agents | "
              f"{stats['duration_seconds']:.1f}s elapsed", flush=True)


def clear_chain_log() -> None:
    """Clear the chain log (useful at start of new plan)."""
    try:
        log_path = ensure_chain_log_exists()

        if log_path.exists():
            log_path.unlink()

        print(f"🗑️  Chain log cleared: {log_path}")

    except Exception as e:
        print(f"⚠️  Failed to clear chain log: {e}", file=sys.stderr)


def show_chain_summary() -> None:
    """Display summary of current chain execution."""
    stats = get_chain_statistics()

    if not stats:
        print("📋 No chain checkpoints logged yet")
        return

    print("\n" + "="*60)
    print("📊 CHAIN EXECUTION SUMMARY")
    print("="*60)
    print(f"Total Checkpoints: {stats['total_checkpoints']}")
    print(f"Unique Agents: {stats['unique_agents']}")
    print(f"Agents: {', '.join('@' + a for a in stats['agent_list'])}")
    print(f"Duration: {stats['duration_seconds']:.1f} seconds")
    print(f"Started: {stats['start_time']}")
    print(f"Last Checkpoint: {stats['last_checkpoint']}")
    print("="*60 + "\n")


# CLI interface for manual invocation
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Chain Checkpoint Manager"
    )
    parser.add_argument(
        "action",
        choices=["clear", "summary", "stats"],
        help="Action to perform"
    )

    args = parser.parse_args()

    if args.action == "clear":
        clear_chain_log()
    elif args.action in ["summary", "stats"]:
        show_chain_summary()
