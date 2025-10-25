# tools/task_prioritization_tool.py
from typing import List, Type
from pydantic import BaseModel, Field
from mcp import Tool

# Input schema for prioritization
class TaskPrioritizationInput(BaseModel):
    tasks: List[str] = Field(..., description="List of subtasks to prioritize")

# MCP Tool definition
class TaskPrioritizationTool(Tool):
    name: str = "task_prioritization"
    description: str = "Prioritizes a list of subtasks"
    inputSchema: Type[BaseModel] = TaskPrioritizationInput

    def run(self, tasks: List[str]):
        # Simple prioritization example: by length of task (shorter tasks first)
        prioritized_tasks = sorted(tasks, key=lambda x: len(x))
        return prioritized_tasks
