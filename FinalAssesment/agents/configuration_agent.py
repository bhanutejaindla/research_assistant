import os


def configuration_agent(state: dict) -> dict:
    """
    Loads configuration values (like API keys) from environment variables
    and stores them in the shared state.
    """

    state.setdefault("agent_log", [])

    # Fetch configuration from environment
    state["config"] = {
        "OPENAI_API_KEY": os.environ.get("OPENAI_API_KEY", "your-fallback-or-false")
    }

    # Add other configurations here if needed

    state["agent_log"].append("Configuration Agent: added config to state.")
    return state
