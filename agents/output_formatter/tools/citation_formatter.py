# agents/output_formatter/tools/citation_formatter.py
from fastmcp import FastMCP
from agents.output_formatter.config import DEFAULT_STYLE
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

mcp = FastMCP("citation_formatter_")
llm_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@mcp.tool("citation_formatter")
def citation_formatter(citations: list, style: str = DEFAULT_STYLE) -> dict:
    """
    Formats raw citation data into APA/MLA/Chicago styles using an LLM.
    """
    citations_text = "\n".join(citations)
    prompt = f"""
    Format the following citations in {style} style:
    {citations_text}
    """

    response = llm_client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=600
    )

    return {"formatted_citations": response.choices[0].message.content}


# 🧪 Local testing entrypoint
if __name__ == "__main__":
    test_citations = [
        "Smith, John. Artificial Intelligence and the Future. MIT Press, 2021.",
        "Doe, Jane. Machine Learning in Practice. Oxford University Press, 2020."
    ]

    result = citation_formatter(test_citations, "APA")
    print("\n✅ Formatted Citations:\n")
    print(result["formatted_citations"])
