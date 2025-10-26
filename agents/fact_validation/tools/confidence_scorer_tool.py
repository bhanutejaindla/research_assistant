# agents/fact_validation/tools/confidence_scorer_tool.py
from fastmcp import FastMCP
from typing import List
import statistics

mcp = FastMCP("confidence-scorer-tool")

# Implementation function (no decorator)
def _confidence_scorer_impl(scores: List[int]) -> str:
    """
    Combines credibility and consistency scores into a confidence metric.
    """
    if not scores:
        return "Please provide numerical scores for confidence evaluation."

    avg_score = statistics.mean(scores)
    confidence_level = (
        "High Confidence" if avg_score >= 8 else
        "Medium Confidence" if avg_score >= 5 else
        "Low Confidence"
    )

    return (
        "--- Confidence Score Report ---\n"
        f"Average Score: {avg_score:.2f}\n"
        f"Confidence Level: {confidence_level}"
    )

# Register with MCP
@mcp.tool()
def confidence_scorer_tool(scores: List[int]) -> str:
    """
    Assigns a reliability confidence level based on credibility and consistency scores.
    
    Args:
        scores: List of numerical scores (1-10) to evaluate confidence
    
    Returns:
        A report showing average score and confidence level
    """
    return _confidence_scorer_impl(scores)

# For backwards compatibility / testing
def run(scores: List[int]) -> str:
    return _confidence_scorer_impl(scores)

# Export
__all__ = ['confidence_scorer_tool', 'run', 'mcp']

if __name__ == "__main__":
    sample_scores = [9, 8, 7, 6, 8]
    print(run(sample_scores))