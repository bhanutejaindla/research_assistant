import os
from openai import OpenAI

# Import MCP tools
from agents.fact_validation.tools.source_credibility_tool import source_credibility_tool
from agents.fact_validation.tools.cross_reference_tool import cross_reference_tool
from agents.fact_validation.tools.confidence_scorer_tool import confidence_scorer_tool
from agents.fact_validation.tools.contradiction_detector_tool import contradiction_detector_tool
from agents.fact_validation.tools.llm_validation_tool import llm_validation_tool

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# Dictionary of all tools
TOOLS = {
    "source_credibility_tool": source_credibility_tool,
    "cross_reference_tool": cross_reference_tool,
    "confidence_scorer_tool": confidence_scorer_tool,
    "contradiction_detector_tool": contradiction_detector_tool,
    "llm_validation_tool": llm_validation_tool
}


# --- LLM Tool Selector ---
def choose_tool(query: str) -> str:
    """
    Uses an LLM to decide which Fact-Checking tool is most appropriate for the query.
    Returns the tool name.
    """
    tool_descriptions = "\n".join([f"- {name}: {tool.description}" for name, tool in TOOLS.items()])

    prompt = f"""
You are a Fact-Checking Orchestrator Agent.
You have access to the following tools:

{tool_descriptions}

Given the user's request below, return ONLY the name of the most suitable tool.

User request:
\"\"\"{query}\"\"\"
Answer with just the tool name.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    return response.choices[0].message.content.strip()


# --- Main Agent Runner ---
def run_agent(query: str):
    """
    Routes the query to the correct MCP tool based on LLM decision.
    """
    tool_name = choose_tool(query)
    print(f"\n🔍 Selected Tool: {tool_name}\n")

    if tool_name not in TOOLS:
        return f"Tool '{tool_name}' not recognized."

    tool = TOOLS[tool_name]

    # Simple demo inputs depending on tool type
    if tool_name == "source_credibility_tool":
        inputs = [query] if isinstance(query, str) else query
        return tool.func(inputs)

    elif tool_name == "cross_reference_tool":
        # Demo: comparing user query with a dummy claim
        return tool.func([query, "AI improves diagnostic accuracy."])

    elif tool_name == "confidence_scorer_tool":
        # Demo: use fixed scores
        return tool.func([8, 7, 9])

    elif tool_name == "contradiction_detector_tool":
        return tool.func([
            query,
            "AI is not reliable for diagnosis",
            "AI is reliable for diagnosis"
        ])

    else:
        # llm_validation_tool or fallback
        return tool.func(query)


# --- Entry Point for Testing ---
if __name__ == "__main__":
    print("\n===== Fact-Checking & Validation Agent =====\n")

    sample_queries = [
        "Check how trustworthy the source https://www.cdc.gov is.",
        "Compare these claims: AI increases accuracy vs AI reduces accuracy.",
        "Give confidence score for credibility 9, 8, 7.",
        "Detect contradictions in statements about AI reliability.",
        "Fact-check the claim: 'AI will replace 80% of jobs by 2030.'"
    ]

    for q in sample_queries:
        print(f"\nUser Query: {q}")
        result = run_agent(q)
        print(result)
        print("-" * 60)
