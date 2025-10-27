# main.py
from langgraph.graph import StateGraph, END, START
from agents.coordinator.coordinator_agent import research_coordinator
from agents.coordinator.tools.query_decomposer import query_decomposer
from agents.coordinator.tools.task_prioritizer import task_prioritizer
from agents.web_retriever.web_retriever_agent import web_scraper
from agents.deep_analysis.deep_analysis_agent import deep_analysis
from agents.fact_validation.fact_validation_agent import fact_validation
from agents.output_formatter.output_formatter_agent import output_formatter

# Define shared research state schema
state = {
    "query": str,
    "subtasks": list,
    "documents": list,
    "insights": list,
    "claims": list,
    "validated_facts": list,
    "final_report": str,
    "agent_status": dict,
}

# Create LangGraph instance
graph = StateGraph(state)

# ---- Define Nodes ----
graph.add_node("research_coordinator", research_coordinator)
graph.add_node("query_decomposer", query_decomposer)
graph.add_node("task_prioritizer", task_prioritizer)
graph.add_node("web_scraper", web_scraper)
graph.add_node("deep_analysis", deep_analysis)
graph.add_node("fact_validation", fact_validation)
graph.add_node("output_formatter", output_formatter)

# ---- Edges (Flow) ----
graph.add_edge(START, "research_coordinator")
graph.add_edge("research_coordinator", "query_decomposer")
graph.add_edge("query_decomposer", "task_prioritizer")

# LLM-based routing logic
graph.add_conditional_edges(
    "task_prioritizer",
    lambda state: state["next_agent"],
    {
        "web_scraper": "web_scraper",
        "deep_analysis": "deep_analysis",
        "fact_validation": "fact_validation",
        "output_formatter": "output_formatter"
    }
)

# Each agent returns to coordinator to update progress
graph.add_edge("web_scraper", "research_coordinator")
graph.add_edge("deep_analysis", "research_coordinator")
graph.add_edge("fact_validation", "research_coordinator")
graph.add_edge("output_formatter", END)

# Compile the LangGraph
compiled_graph = graph.compile()

# ---- Run ----
if __name__ == "__main__":
    result = compiled_graph.invoke({"query": "Impact of AI on global economy"})
    print("Final Report:\n", result["final_report"])
