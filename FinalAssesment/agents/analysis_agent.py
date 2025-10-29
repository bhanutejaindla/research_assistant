# agents/analysis_agent.py
import os

def analysis_agent(state: dict) -> dict:
    """Performs repository-level analysis and file discovery."""

    file_list = []
    repo_path = (
        state.get("unzipped_path")
        or state.get("repo_path")
        or "uploads"
    )

    for root, _, files in os.walk(repo_path):
        for f in files:
            if not f.startswith(".") and not any(x in root for x in [".git", "node_modules"]):
                file_list.append(os.path.join(root, f))

    state["file_list"] = file_list
    state["agent_log"].append(f"Analysis Agent: Found {len(file_list)} files.")
    return state