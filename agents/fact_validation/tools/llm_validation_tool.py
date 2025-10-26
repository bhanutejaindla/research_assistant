from mcp import Tool
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def llm_validation_tool_func(query: str) -> str:
    """
    Uses an LLM to perform holistic fact-checking and credibility reasoning.
    """
    if not query:
        return "Please provide a query or claim for validation."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": f"Fact-check this statement and explain your reasoning:\n{query}"}
        ]
    )
    return response.choices[0].message.content

llm_validation_tool = Tool(
    name="llm_validation_tool",
    description="Uses an LLM to fact-check a claim with reasoning and citation hints.",
    func=llm_validation_tool_func
)

if __name__ == "__main__":
    print(llm_validation_tool.func("AI can fully replace doctors in diagnosis by 2025."))
