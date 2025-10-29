import os
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()


def get_initial_state() -> dict:
    """
    Initializes the default state for the multi-agent system.
    Loads configuration (like API keys) from environment variables.
    """
    return {
        "config": {
            "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "your-fallback-or-raise"),
        },
        "input_data": "Paste your code, file, or data here.",
        "agent_log": [],
        "code_analysis": None,
        "web_aug_results": None,
        "security_findings": None,
        "documentation": None,
        "diagram_content": None,
        "final_results": None,
        "pause_requested": False,
        "current_node": "coordination_agent",
        "user_questions": [],
        "context_injections": [],
        "interrupted": False,
        "checkpoint_history": [],
        "previous_interactions": []
    }


def checkpoint_state(state: dict, path: str = "checkpoint_state.json") -> None:
    """
    Saves the current state to disk as a JSON file with a UTC timestamp.
    """
    state_copy = dict(state)
    state_copy["checkpointed_at"] = datetime.utcnow().isoformat()

    with open(path, "w", encoding="utf-8") as f:
        json.dump(state_copy, f, indent=2)


def load_checkpoint(path: str = "checkpoint_state.json") -> dict:
    """
    Loads a previously saved state checkpoint from disk.
    Returns an empty state if the file is missing or corrupted.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return get_initial_state()
