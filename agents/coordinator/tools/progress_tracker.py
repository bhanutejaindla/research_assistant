# agents/coordinator/tools/progress_tracker.py
"""
Progress Tracker Tool
Tracks progress of the research workflow.
"""

from typing import Dict

class ProgressTracker:
    def __init__(self):
        # Keeps track of all tasks and their statuses
        self.progress: Dict[str, str] = {}
        self.workflow_name = None

    def start(self, workflow_name: str):
        """Start a new workflow."""
        self.workflow_name = workflow_name
        self.progress.clear()
        print(f"[PROGRESS] Started workflow: {workflow_name}")

    def update(self, task_name: str, status: str):
        """Update the status of a specific task."""
        if not self.workflow_name:
            print("[WARN] Workflow not started yet — call start() first.")
            return
        self.progress[task_name] = status
        print(f"[PROGRESS] Task '{task_name}' marked as {status}")

    def get_status(self):
        """Return a snapshot of current progress."""
        return {
            "workflow": self.workflow_name,
            "tasks": self.progress,
            "completed": sum(1 for s in self.progress.values() if s == "completed"),
            "total": len(self.progress),
        }

    def reset(self):
        """Reset all progress."""
        self.workflow_name = None
        self.progress.clear()
        print("[PROGRESS] Reset all workflow data.")
