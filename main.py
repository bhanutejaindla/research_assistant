# main.py
from langgraph.graph import StateGraph, END, START
# ---- Coordinator ----
from agents.coordinator.coordinator_agent import research_coordinator
from agents.coordinator.tools.query_decomposer import query_decomposer
from agents.coordinator.tools.task_prioritizer import task_prioritizer
from agents.coordinator.tools.progress_tracking import progress_tracking
from agents.coordinator.tools.result_synthesis import result_synthesis

# ---- Web Retriever ----
from agents.web_retriever.web_retriever_agent import web_scraper

# ---- Deep Analysis ----
from agents.deep_analysis.deep_analysis_agent import deep_analysis

# ---- Fact Validation ----
from agents.fact_validation.fact_validation_agent import fact_validation

# ---- Output Formatter ----
from agents.output_formatter.output_formatter_agent import output_formatter

# --- Shared state schema ---
state = {
    "query": str,
    "subtasks": list,
    "documents": list,
    "insights": list,
    "claims": list,
    "validated_facts": list,
    "final_report": str,
    "agent_status": dict,
    "progress": dict
}

# --- Build LangGraph ---
graph = StateGraph(state)

# --- Add Nodes ---
graph.add_node("research_coordinator", research_coordinator)
graph.add_node("query_decomposer", query_decomposer)
graph.add_node("task_prioritizer", task_prioritizer)
graph.add_node("progress_tracking", progress_tracking)
graph.add_node("result_synthesis", result_synthesis)
graph.add_node("web_scraper", web_scraper)
graph.add_node("deep_analysis", deep_analysis)
graph.add_node("fact_validation", fact_validation)
graph.add_node("output_formatter", output_formatter)

# --- Flow Connections ---
graph.add_edge(START, "research_coordinator")
graph.add_edge("research_coordinator", "query_decomposer")
graph.add_edge("query_decomposer", "task_prioritizer")

# --- LLM-Based Conditional Routing ---
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

# After each agent finishes, return to coordinator for tracking & synthesis
graph.add_edge("web_scraper", "progress_tracking")
graph.add_edge("deep_analysis", "progress_tracking")
graph.add_edge("fact_validation", "progress_tracking")
graph.add_edge("progress_tracking", "result_synthesis")
graph.add_edge("result_synthesis", "research_coordinator")
graph.add_edge("output_formatter", END)

compiled_graph = graph.compile()

if __name__ == "__main__":
    final_state = compiled_graph.invoke({"query": "Impact of AI on Global Healthcare"})
    print("\n✅ Final Research Report:\n", final_state["final_report"])
