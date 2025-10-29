from agents.orchestration.state import checkpoint_state
import datetime


class PauseException(Exception):
    """Raised when a pause is requested."""
    pass


def agent_wrapper(agent_fn, agent_name):
    """
    Wraps each agent function to handle logging, checkpointing, and pause control.
    """

    def wrapped(state):
        # Update current active node
        state["current_node"] = agent_name

        # Log entry
        state.setdefault("agent_log", []).append(
            f"Entering {agent_name} at {datetime.datetime.utcnow().isoformat()}"
        )

        # Create a checkpoint before running agent
        checkpoint_state(state)

        # Pause mechanism
        if state.get("pause_requested", False):
            state["interrupted"] = True
            checkpoint_state(state)
            raise PauseException(f"Paused at {agent_name}")

        # Execute the actual agent function
        try:
            result_state = agent_fn(state)
        except Exception as e:
            state["agent_log"].append(f"Error in {agent_name}: {str(e)}")
            checkpoint_state(state)
            raise

        # Checkpoint again after execution
        checkpoint_state(result_state)
        return result_state

    return wrapped
