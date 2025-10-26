# agents/coordinator/coordinator_server.py

from mcp.server.fastmcp import FastMCP
from agents.coordinator.tools.query_decomposer import decompose_query
from agents.coordinator.tools.task_prioritizer import prioritize_tasks
from agents.coordinator.tools.progress_tracker import ProgressTracker
from agents.coordinator.tools.result_synthesizer import synthesize_results

app = FastMCP("Research Coordinator Agent")

progress_tracker = ProgressTracker()

@app.tool()
@app.tool()
def process_query(query: str):
    sub_tasks = decompose_query(query)
    prioritized = prioritize_tasks(sub_tasks)
    progress_tracker.start("Research Workflow")

    for task in prioritized:
        progress_tracker.update(task["task"], "completed")  # extract string

    structured_results = [
        {"task": t, "agent": "Coordinator", "result": f"Completed: {t}"}
        for t in prioritized
    ]
    result = synthesize_results(structured_results)

    return {
        "query": query,
        "sub_tasks": sub_tasks,
        "prioritized": prioritized,
        "result": result,
    }

if __name__ == "__main__":
    print("🧪 Running self-test mode...")
    result = process_query("impact of climate change on agriculture")
    print(result)

