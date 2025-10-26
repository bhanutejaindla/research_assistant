# agents/fact_validation/tools/llm_analysis_tool.py
from fastmcp import FastMCP
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

mcp = FastMCP("llm-analysis-tool")

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Implementation function (no decorator)
def _llm_analysis_impl(prompt: str, model: str = "gpt-4o-mini") -> str:
    """
    Uses an LLM to provide deep analytical insights or reasoning based on a prompt.
    """
    if not prompt:
        return "Please provide a valid analysis prompt."
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": f"Analyze this deeply:\n{prompt}"}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error during LLM analysis: {str(e)}"

# Register with MCP
@mcp.tool()
def llm_analysis_tool(prompt: str, model: str = "gpt-4o-mini") -> str:
    """
    Leverages an LLM to provide high-level analytical reasoning.
    
    Args:
        prompt: Analysis prompt for the LLM to process and provide insights on (required, min length: 1)
        model: OpenAI model to use for analysis (default: gpt-4o-mini)
    
    Returns:
        Analytical insights from the LLM or an error message
    """
    return _llm_analysis_impl(prompt=prompt, model=model)

# For backwards compatibility / testing
def run(prompt: str, model: str = "gpt-4o-mini") -> str:
    return _llm_analysis_impl(prompt=prompt, model=model)

# Export
__all__ = ['llm_analysis_tool', 'run', 'mcp']

if __name__ == "__main__":
    prompt = "Compare the long-term economic impact of AI adoption in healthcare vs manufacturing."
    print(run(prompt))