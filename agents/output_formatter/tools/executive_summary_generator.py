# agents/output_formatter/tools/executive_summary_generator.py
from fastmcp import FastMCP
from openai import OpenAI
from agents.output_formatter.config import DEFAULT_SUMMARY_LENGTH
from dotenv import load_dotenv
import os

# Load environment variables (especially OPENAI_API_KEY)
load_dotenv()

mcp = FastMCP("executive_summary_generator_tool")
llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@mcp.tool(
    name="executive_summary_generator",
    # description="Generates an executive summary from the full research report."
)
def executive_summary_generator(report_text: str, word_limit: int = DEFAULT_SUMMARY_LENGTH) -> dict:
    """
    Summarizes the research into an executive summary using GPT-4.
    """
    prompt = f"""
    Provide a concise executive summary (around {word_limit} words) for the following research text:
    {report_text}
    """

    response = llm_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=800
    )

    return {"executive_summary": response.choices[0].message.content}


# 🧪 Local testing entrypoint
if __name__ == "__main__":
    sample_report = """
    Artificial Intelligence (AI) is transforming industries through automation,
    data analysis, and intelligent decision-making. Recent advancements in
    large language models and reinforcement learning have enabled systems that
    can generate text, create images, and even write code. However, challenges
    remain regarding bias, interpretability, and ethical deployment of AI
    systems in real-world applications.
    """

    print("🔍 Generating executive summary...\n")
    result = executive_summary_generator(sample_report, word_limit=80)
    print("✅ Executive Summary:\n")
    print(result["executive_summary"])
