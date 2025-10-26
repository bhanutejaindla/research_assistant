# agents/fact_validation/tools/source_credibility_tool.py
from fastmcp import FastMCP
from typing import List
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

mcp = FastMCP("source-credibility-tool")

# Implementation function (no decorator)
def _source_credibility_impl(sources: List[str]) -> str:
    """
    Evaluates the trustworthiness and credibility of information sources.
    """
    if not sources:
        return "Please provide at least one source to evaluate."
    
    trusted_domains = ["cdc.gov", "who.int", "nih.gov", "gov", "edu", "nature.com", "science.org"]
    
    results = []
    for source in sources:
        source_lower = source.lower()
        is_trusted = any(domain in source_lower for domain in trusted_domains)
        
        credibility = "HIGH" if is_trusted else "MEDIUM/LOW"
        results.append(f"Source: {source}\nCredibility: {credibility}")
    
    return "--- Source Credibility Report ---\n" + "\n\n".join(results)

# Register with MCP
@mcp.tool()
def source_credibility_tool(sources: List[str]) -> str:
    """
    Evaluates the trustworthiness and credibility of information sources.
    
    Args:
        sources: List of source URLs or names to evaluate for credibility
    
    Returns:
        A report showing credibility assessment for each source
    """
    return _source_credibility_impl(sources)

# For backwards compatibility / testing
def run(sources: List[str]) -> str:
    return _source_credibility_impl(sources)

# Export
__all__ = ['source_credibility_tool', 'run', 'mcp']

if __name__ == "__main__":
    test_sources = [
        "https://www.cdc.gov/health-info",
        "https://randomwebsite.com/article",
        "https://nature.com/research"
    ]
    print(run(test_sources))