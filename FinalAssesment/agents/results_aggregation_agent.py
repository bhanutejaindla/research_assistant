def results_aggregation_agent(state: dict) -> dict:
    """
    Aggregates all outputs from previous agents into a single
    structured final output dictionary.
    """

    state.setdefault("agent_log", [])

    final = {
        "documentation": state.get("documentation", ""),
        "diagram": state.get("diagrams", ""),
        "agent_log": state.get("agent_log", []),
        "code_analysis": state.get("code_analysis_results", []),
        "security_findings": state.get("security_findings", []),
        "web_aug_results": state.get("web_aug_results", "")
    }

    state["final_output"] = final
    state["agent_log"].append("Results Aggregation Agent: Delivered final outputs.")

    return state
