# agents/fact_validation/tools/llm_validation_tool.py
from fastmcp import FastMCP
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

mcp = FastMCP("llm-validation-tool")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Implementation function (no decorator)
def _llm_validation_impl(query: str) -> str:
    """
    Uses an LLM to perform holistic fact-checking and credibility reasoning.
    """
    if not query:
        return "Please provide a query or claim for validation."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": f"Fact-check this statement and explain your reasoning:\n{query}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error during LLM validation: {str(e)}"

# Register with MCP
@mcp.tool()
def llm_validation_tool(query: str) -> str:
    """
    Uses an LLM to fact-check a claim with reasoning and citation hints.
    
    Args:
        query: The claim or statement to fact-check
    
    Returns:
        Fact-checking analysis with reasoning from the LLM
    """
    return _llm_validation_impl(query)

# For backwards compatibility / testing
def run(query: str) -> str:
    return _llm_validation_impl(query)

# Export
__all__ = ['llm_validation_tool', 'run', 'mcp']

if __name__ == "__main__":
    print(run("AI can fully replace doctors in diagnosis by 2025."))