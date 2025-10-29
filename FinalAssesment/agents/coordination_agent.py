def coordination_agent(state: dict) -> dict:
    """
    Coordinates workflow execution by processing user input and
    determining which agents or modules should run next.
    """

    state.setdefault("agent_log", [])
    state["agent_log"].append(
        "Coordination Agent: Processing user prompt/config and dispatching workflow."
    )

    # Example: analyze user prompt or config to decide which agents to activate
    user_prompt = state.get("user_prompt", "").lower()

    # Example logic — you can expand this as needed
    if "security" in user_prompt:
        state["active_agents"] = ["security_agent"]
    elif "analyze" in user_prompt:
        state["active_agents"] = ["analysis_agent"]
    else:
        state["active_agents"] = ["preprocessing_agent", "analysis_agent", "code_agent"]

    return state
