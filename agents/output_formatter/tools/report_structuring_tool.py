from fastmcp import FastMCP
from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables (especially OPENAI_API_KEY)
load_dotenv()

# Initialize FastMCP agent and OpenAI client
mcp = FastMCP("report_structuring_tool")
llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@mcp.tool(
    name="report_structuring_tool",
    description="Creates a hierarchical research report outline from multiple sections."
)
def report_structuring_tool(sections: list) -> dict:
    """
    Takes sections or bullet points and organizes them into a structured research report.
    """
    combined = "\n".join(sections)
    prompt = f"""
    Organize the following research findings into a structured professional report outline.
    Include sections such as:
    - Introduction
    - Methodology
    - Results
    - Discussion
    - Conclusion

    Findings:
    {combined}
    """

    response = llm_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=800
    )

    return {"structured_report": response.choices[0].message.content}


# -------------------------------------------------------------
# ✅ MAIN (for testing or running standalone)
# -------------------------------------------------------------
if __name__ == "__main__":
    # You can either run this directly to test or host it as an MCP server
    sample_sections = [
        "AI is revolutionizing healthcare with faster diagnostics.",
        "Deep learning models are increasingly used for medical imaging.",
        "However, interpretability remains a challenge.",
        "Recent research focuses on explainable AI for trust in critical systems."
    ]

    print("🔍 Generating structured report...\n")
    result = report_structuring_tool(sample_sections)
    print(result["structured_report"])

    # To run as an MCP server instead of a test:
    # mcp.run()   # uncomment this line when you want it to act as a FastMCP tool server
