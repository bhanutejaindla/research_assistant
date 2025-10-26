# agents/fact_validation/tools/contradiction_detector_tool.py
from fastmcp import FastMCP
from typing import List

mcp = FastMCP("contradiction-detector-tool")

# Implementation function (no decorator)
def _contradiction_detector_impl(statements: List[str]) -> str:
    """
    Detects simple contradictions based on negation or opposing sentiment patterns.
    """
    if not statements or len(statements) < 2:
        return "Please provide multiple statements to detect contradictions."

    contradictions = []
    for i, s1 in enumerate(statements):
        for j, s2 in enumerate(statements):
            if i >= j:
                continue
            if ("not" in s1 and "not" not in s2 and any(word in s2 for word in s1.split())):
                contradictions.append(f"Contradiction: '{s1}' ↔ '{s2}'")

    if not contradictions:
        return "No contradictions detected."

    return "--- Contradiction Detection Report ---\n" + "\n".join(contradictions)

# Register with MCP
@mcp.tool()
def contradiction_detector_tool(statements: List[str]) -> str:
    """
    Detects conflicting or opposite statements in a dataset.
    
    Args:
        statements: List of statements to analyze for contradictions (minimum 2 required)
    
    Returns:
        A report showing detected contradictions or a message if none found
    """
    return _contradiction_detector_impl(statements)

# For backwards compatibility / testing
def run(statements: List[str]) -> str:
    return _contradiction_detector_impl(statements)

# Export
__all__ = ['contradiction_detector_tool', 'run', 'mcp']

if __name__ == "__main__":
    sents = [
        "AI is not reliable for critical healthcare tasks.",
        "AI is reliable for healthcare tasks.",
        "AI is improving rapidly."
    ]
    print(run(sents))