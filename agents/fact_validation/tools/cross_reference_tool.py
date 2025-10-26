# agents/fact_validation/tools/cross_reference_tool.py
from fastmcp import FastMCP
from typing import List

mcp = FastMCP("cross-reference-tool")

# Implementation function (no decorator)
def _cross_reference_impl(claims: List[str]) -> str:
    """
    Cross-checks claims across multiple documents and identifies alignment or conflict.
    """
    if not claims or len(claims) < 2:
        return "Please provide at least two claims to cross-reference."

    matches = 0
    conflicts = 0
    base_claim = claims[0].lower()

    for other in claims[1:]:
        if base_claim in other.lower() or other.lower() in base_claim:
            matches += 1
        else:
            conflicts += 1

    return (
        "--- Cross Reference Report ---\n"
        f"Aligned Claims: {matches}\n"
        f"Conflicting Claims: {conflicts}"
    )

# Register with MCP
@mcp.tool()
def cross_reference_tool(claims: List[str]) -> str:
    """
    Cross-checks claims across multiple documents and identifies alignment or conflict.
    
    Args:
        claims: List of claims to cross-reference (minimum 2 claims required)
    
    Returns:
        A report showing aligned and conflicting claims
    """
    return _cross_reference_impl(claims)

# For backwards compatibility / testing
def run(claims: List[str]) -> str:
    return _cross_reference_impl(claims)

# Export
__all__ = ['cross_reference_tool', 'run', 'mcp']

if __name__ == "__main__":
    claims = [
        "AI improves diagnosis accuracy by 30%.",
        "Studies show AI increases diagnostic accuracy significantly.",
        "AI has no impact on medical accuracy."
    ]
    print(run(claims))