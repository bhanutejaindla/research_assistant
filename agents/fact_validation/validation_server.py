import json
import os
from openai import OpenAI
from agents.deep_analysis.config import MODEL_NAME

# Import MCP tools
from agents.deep_analysis.tools.comparative_analysis_tool import comparative_analysis_tool
from agents.deep_analysis.tools.trend_analysis_tool import trend_analysis_tool
from agents.deep_analysis.tools.causal_reasoning_tool import causal_reasoning_tool
from agents.deep_analysis.tools.statistical_analysis_tool import statistical_analysis_tool

# Initialize OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


# --- LLM Decision Logic ---
def decide_tool(query: str) -> str:
    """
    Uses LLM reasoning to decide which analysis tool should be called
    based on the user's query.
    """
    system_prompt = """
    You are a Deep Analysis Controller Agent.
    You have the following tools available:
    1. comparative_analysis_tool - compare multiple documents
    2. trend_analysis_tool - detect patterns over time
    3. causal_reasoning_tool - detect cause-effect relationships
    4. statistical_analysis_tool - perform quantitative analysis

    Based on the user's query, decide which ONE tool is most appropriate.
    Respond with only the tool name (no explanation).
    """
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ],
        temperature=0
    )
    return response.choices[0].message["content"].strip()


def extract_keyword(query: str) -> str:
    """Naive keyword extractor for trend analysis."""
    words = query.split()
    return words[-1] if words else "data"


# --- Main Deep Analysis Runner ---
def run_deep_analysis(query: str, documents: list):
    tool_name = decide_tool(query)
    print(f"\n[Agent 3 Decision] → Selected Tool: {tool_name}\n")

    if tool_name == "comparative_analysis_tool":
        result = comparative_analysis_tool.func(documents)
    elif tool_name == "trend_analysis_tool":
        keyword = extract_keyword(query)
        result = trend_analysis_tool.func(documents, keyword)
    elif tool_name == "causal_reasoning_tool":
        result = causal_reasoning_tool.func(documents)
    elif tool_name == "statistical_analysis_tool":
        result = statistical_analysis_tool.func(documents)
    else:
        result = {"error": f"Unknown tool selected: {tool_name}"}

    return {"selected_tool": tool_name, "result": result}


# --- Individual tool demo runners ---
def test_comparative_analysis():
    print("\n🧩 Running Comparative Analysis Tool Example")
    docs = [
        "AI and machine learning drive innovation in healthcare.",
        "Healthcare and AI technologies are evolving rapidly.",
    ]
    result = comparative_analysis_tool.func(docs)
    print(json.dumps(result, indent=2))


def test_trend_analysis():
    print("\n📈 Running Trend Analysis Tool Example")
    docs = [
        "2023: AI adoption increased by 20%",
        "2024: AI adoption increased by 50%",
        "2025: AI adoption continues to rise",
    ]
    result = trend_analysis_tool.func(docs, keyword="AI")
    print(json.dumps(result, indent=2))


def test_causal_reasoning():
    print("\n⚙️ Running Causal Reasoning Tool Example")
    docs = [
        "Economic growth leads to higher employment rates.",
        "Increased rainfall causes flooding in coastal areas.",
    ]
    result = causal_reasoning_tool.func(docs)
    print(json.dumps(result, indent=2))


def test_statistical_analysis():
    print("\n📊 Running Statistical Analysis Tool Example")
    docs = [
        "Revenue grew by 120 in 2023 and reached 240 in 2024.",
        "Profits increased to 360 last year.",
    ]
    result = statistical_analysis_tool.func(docs)
    print(json.dumps(result, indent=2))


def test_auto_decision():
    print("\n🧠 Running LLM Decision Example")
    docs = [
        "Quantum computing leads to faster results in 2025.",
        "Due to new quantum breakthroughs, performance increased by 25%.",
    ]
    query = "Find causal relationships between technological advances and performance."
    result = run_deep_analysis(query, docs)
    print(json.dumps(result, indent=2))


# --- Entry Point ---
if __name__ == "__main__":
    print("\n===== Deep Analysis Agent Tool Demos =====\n")

    # Run each tool test individually
    test_comparative_analysis()
    test_trend_analysis()
    test_causal_reasoning()
    test_statistical_analysis()

    # Test LLM-powered dynamic tool selection
    test_auto_decision()
