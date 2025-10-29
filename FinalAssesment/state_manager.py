import json, os

STATE_DIR = "analysis_states"
os.makedirs(STATE_DIR, exist_ok=True)

def save_state(project_id, state):
    """Save analysis state to disk."""
    path = os.path.join(STATE_DIR, f"state_project_{project_id}.json")
    with open(path, "w") as f:
        json.dump(state, f, indent=2)
    return path

def load_state(project_id):
    """Load state if exists, else return empty dict."""
    path = os.path.join(STATE_DIR, f"state_project_{project_id}.json")
    if os.path.exists(path):
        with open(path, "r") as f:
            return json.load(f)
    return {}
