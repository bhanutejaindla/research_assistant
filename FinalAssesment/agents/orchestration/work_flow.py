from typing import Dict, Any

from langgraph.graph import StateGraph

from agents.orchestration.state import checkpoint_state
from agents.orchestration.agent_wrapper import AgentWrapper, PauseException

from agents.coordination_agent import coordination_agent
from agents.configuration_agent import configuration_agent
from agents.preprocessing_agent import preprocessing_agent
from agents.analysis_agent import analysis_agent
from agents.web_augmentation_agent import web_augmentation_agent
from agents.security_agent import security_agent
from agents.code_agent import code_agent
from agents.documentation_agent import documentation_agent
from agents.diagram_agent import diagram_agent
from agents.results_aggregation_agent import results_aggregation_agent


def build_workflow_graph() -> StateGraph:
    """Builds the full agent workflow graph."""

    graph = StateGraph(Dict[str, Any])

    # Register agents as graph nodes
    graph.add_node("coordination_agent", AgentWrapper(coordination_agent, "coordination_agent"))
    graph.add_node("configuration_agent", AgentWrapper(configuration_agent, "configuration_agent"))
    graph.add_node("preprocessing_agent", AgentWrapper(preprocessing_agent, "preprocessing_agent"))
    graph.add_node("analysis_agent", AgentWrapper(analysis_agent, "analysis_agent"))
    graph.add_node("code_agent", AgentWrapper(code_agent, "code_agent"))
    graph.add_node("web_augmentation_agent", AgentWrapper(web_augmentation_agent, "web_augmentation_agent"))
    graph.add_node("security_agent", AgentWrapper(security_agent, "security_agent"))
    graph.add_node("documentation_agent", AgentWrapper(documentation_agent, "documentation_agent"))
    graph.add_node("diagram_agent", AgentWrapper(diagram_agent, "diagram_agent"))
    graph.add_node("results_aggregation_agent", AgentWrapper(results_aggregation_agent, "results_aggregation_agent"))

    # Define edges (workflow order)
    graph.add_edge("coordination_agent", "configuration_agent")
    graph.add_edge("configuration_agent", "preprocessing_agent")
    graph.add_edge("preprocessing_agent", "analysis_agent")
    graph.add_edge("analysis_agent", "code_agent")
    graph.add_edge("code_agent", "web_augmentation_agent")
    graph.add_edge("web_augmentation_agent", "security_agent")
    graph.add_edge("security_agent", "documentation_agent")
    graph.add_edge("documentation_agent", "diagram_agent")
    graph.add_edge("diagram_agent", "results_aggregation_agent")

    # Define workflow entry and exit
    graph.set_entry_point("coordination_agent")
    graph.set_finish_point("results_aggregation_agent")

    return graph


def run_full_pipeline(initial_state: dict) -> dict:
    """Run the complete agent workflow pipeline."""
    graph = build_workflow_graph()
    app = graph.compile()

    try:
        results = app.invoke(initial_state)
        # Ensure consistent return structure for FastAPI
        return results.get("final_results", results.get("Final_output", results))
    except PauseException as e:
        # Optional: handle paused run
        initial_state["status"] = "paused"
        initial_state["pause_reason"] = str(e)
        return initial_state
