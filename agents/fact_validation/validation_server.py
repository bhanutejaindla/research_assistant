# agents/fact_validation/agent.py
import os
from openai import OpenAI
from dotenv import load_dotenv
from agents.fact_validation.tools.source_credibility_tool import run as source_credibility_run
from agents.fact_validation.tools.cross_reference_tool import run as cross_reference_run
from agents.fact_validation.tools.confidence_scorer_tool import run as confidence_scorer_run
from agents.fact_validation.tools.contradiction_detector_tool import run as contradiction_detector_run
from agents.fact_validation.tools.llm_analysis_tool import run as llm_analysis_run

# Load environment variables
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Tool descriptions for routing
TOOL_DESCRIPTIONS = {
    "source_credibility_tool": "Evaluates the trustworthiness and credibility of information sources",
    "cross_reference_tool": "Cross-checks claims across documents for consistency or disagreement",
    "confidence_scorer_tool": "Assigns a reliability confidence level based on credibility and consistency scores",
    "contradiction_detector_tool": "Detects conflicting or opposite statements in a dataset",
    "llm_analysis_tool": "Leverages an LLM to provide high-level analytical reasoning and fact-checking"
}

TOOLS = {
    "source_credibility_tool": source_credibility_run,
    "cross_reference_tool": cross_reference_run,
    "confidence_scorer_tool": confidence_scorer_run,
    "contradiction_detector_tool": contradiction_detector_run,
    "llm_analysis_tool": llm_analysis_run
}


def choose_tool(query: str) -> str:
    """
    Ask the LLM which tool best fits this fact-checking query.
    """
    tool_descriptions = "\n".join(
        [f"- {name}: {desc}" for name, desc in TOOL_DESCRIPTIONS.items()]
    )

    prompt = f"""
You are a Fact-Checking Orchestrator.
You have access to the following tools:

{tool_descriptions}

Given the user's request below, return ONLY the name of the most suitable tool.

User request:
\"\"\"{query}\"\"\"
Answer with just the tool name.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        tool_name = response.choices[0].message.content.strip()
        return tool_name
    except Exception as e:
        print(f"Error selecting tool: {str(e)}")
        return "llm_analysis_tool"  # Default fallback


def run_agent(query: str):
    """
    Uses LLM to route the query to the correct fact-checking tool.
    """
    tool_name = choose_tool(query)

    print(f"\n🔍 Selected Tool: {tool_name}")

    if tool_name not in TOOLS:
        print(f"⚠️ Tool '{tool_name}' not recognized. Using llm_analysis_tool as fallback.")
        tool_name = "llm_analysis_tool"

    tool_func = TOOLS[tool_name]

    try:
        # Basic input handling depending on tool type
        if tool_name == "source_credibility_tool":
            # Extract URLs from query or use the query itself
            inputs = [query] if isinstance(query, str) else query
            return tool_func(inputs)
        
        elif tool_name == "cross_reference_tool":
            # For cross-reference, we need multiple claims
            # Try to split the query into claims or use example claims
            claims = [
                query,
                "AI accuracy improves over time"
            ]
            return tool_func(claims)
        
        elif tool_name == "confidence_scorer_tool":
            # Use sample scores for demonstration
            return tool_func([8, 7, 9])
        
        elif tool_name == "contradiction_detector_tool":
            # Create statements for contradiction detection
            statements = [
                query,
                "AI is not accurate for diagnosis",
                "AI is accurate for diagnosis"
            ]
            return tool_func(statements)
        
        elif tool_name == "llm_analysis_tool":
            # Direct LLM analysis
            return tool_func(query)
        
        else:
            return tool_func(query)
    
    except Exception as e:
        return f"Error executing tool '{tool_name}': {str(e)}"


if __name__ == "__main__":
    print("🧠 Fact-Checking & Validation Agent Ready.")
    print("=" * 60)
    
    sample_queries = [
        "Check how trustworthy the source https://www.cdc.gov is.",
        "Compare these claims: AI increases accuracy vs AI reduces accuracy.",
        "Give confidence score for credibility 9, 8, 7.",
        "Detect contradictions in statements about AI reliability.",
        "Fact-check the claim: 'AI will replace 80% of jobs by 2030.'"
    ]

    for q in sample_queries:
        print(f"\n📝 User Query: {q}")
        result = run_agent(q)
        print(result)
        print("-" * 60)