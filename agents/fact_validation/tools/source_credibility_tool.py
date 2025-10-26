from mcp import Tool
from pydantic import BaseModel, Field
import re

# Define the input schema using Pydantic
class SourceCredibilityInput(BaseModel):
    urls: list[str] = Field(
        description="List of URLs to evaluate for credibility",
        min_length=1
    )

def source_credibility_tool_func(urls: list[str]) -> str:
    """
    Evaluates credibility of given sources based on domain and content pattern.
    """
    if not urls:
        return "Please provide one or more URLs to evaluate."

    credibility_scores = []
    for url in urls:
        score = 0
        if re.search(r"\.gov|\.edu|\.org", url):
            score += 8
        elif re.search(r"\.com", url):
            score += 6
        else:
            score += 4

        if "wikipedia" in url:
            score -= 2
        if "blog" in url or "medium" in url:
            score -= 3

        credibility_scores.append(f"{url} → Credibility Score: {max(min(score,10),1)} / 10")

    return "--- Source Credibility Report ---\n" + "\n".join(credibility_scores)

# ✅ Register the tool with MCP with the required inputSchema
source_credibility_tool = Tool(
    name="source_credibility_tool",
    description="Evaluates how credible given URLs are based on domain heuristics.",
    inputSchema=SourceCredibilityInput.model_json_schema(),
    func=lambda input_data: source_credibility_tool_func(**input_data)
)

if __name__ == "__main__":
    test_urls = [
        "https://www.nih.gov/research/ai-healthcare",
        "https://techcrunch.com/article-on-ai",
        "https://randomblog.medium.com/opinion-on-ai"
    ]
    # Test the underlying function directly
    print(source_credibility_tool_func(test_urls))
    
    # Or test through the Tool's func with proper input format
    print(source_credibility_tool.func({"urls": test_urls}))