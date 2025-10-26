# agents/output_formatter/formatter_server.py
from fastmcp import FastMCP
from openai import OpenAI
import os
from dotenv import load_dotenv

# Import all tool modules (they auto-register)
from agents.output_formatter.tools import (
    citation_formatter,
    report_structuring_tool,
    visualization_generator,
    executive_summary_generator,
)

load_dotenv()

app = FastMCP("output_formatter_agent")
llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Map tool names to their callable functions
TOOL_MAP = {
    "citation_formatter": citation_formatter.citation_formatter,
    "report_structuring_tool": report_structuring_tool.report_structuring_tool,
    "visualization_generator": visualization_generator.visualization_generator,
    "executive_summary_generator": executive_summary_generator.executive_summary_generator,
}

@app.tool("select_and_run_output_formatter")
def select_and_run_output_formatter(user_query: str, data: dict = None) -> dict:
    """
    Uses LLM reasoning to select the correct output formatting tool based on the query.
    """
    data = data or {}
    available_tools = ", ".join(TOOL_MAP.keys())

    prompt = f"""
    You are the Output Formatting Coordinator Agent.

    Based on the user's request, select ONE of the following tools to use:
    {available_tools}

    Then, explain why you chose it and return only the tool name.

    User query:
    {user_query}
    """

    # Ask the LLM which tool is appropriate
    response = llm_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    chosen_tool_name = response.choices[0].message.content.strip().split()[0]
    chosen_tool = TOOL_MAP.get(chosen_tool_name)

    if not chosen_tool:
        return {"error": f"Unknown tool '{chosen_tool_name}' selected by LLM."}

    # Execute the chosen tool
    try:
        result = chosen_tool(**data)
        return {"tool_used": chosen_tool_name, "result": result}
    except Exception as e:
        return {"error": f"Tool execution failed: {e}"}


if __name__ == "__main__":
    print("Starting Output Formatter MCP Agent...")
    app.run()
