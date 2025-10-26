from mcp import Tool
from pydantic import BaseModel, Field
import re
from collections import Counter

# Define the input schema using Pydantic
class TrendAnalysisInput(BaseModel):
    texts: list[str] = Field(
        description="List of texts to analyze for trends and keywords",
        min_length=1
    )

def trend_analysis_tool_func(texts: list[str]) -> str:
    """
    Detects most frequent keywords and trends across multiple documents or time periods.
    """
    if not texts:
        return "Please provide at least one text input for trend analysis."

    words = []
    for text in texts:
        tokens = re.findall(r'\b\w+\b', text.lower())
        words.extend(tokens)

    common = Counter(words).most_common(5)
    report = "\n".join([f"{word}: {count}" for word, count in common])
    return f"--- Trend Analysis Report ---\nTop Keywords:\n{report}"

# ✅ Register the tool with MCP with the required inputSchema
trend_analysis_tool = Tool(
    name="trend_analysis_tool",
    description="Analyzes text collection to identify frequently occurring keywords and trends.",
    inputSchema=TrendAnalysisInput.model_json_schema(),
    func=lambda input_data: trend_analysis_tool_func(**input_data)
)

if __name__ == "__main__":
    sample_docs = [
        "AI growth continues as machine learning advances.",
        "Deep learning and AI dominate research trends in 2025.",
        "AI and data science are top fields for innovation."
    ]
    # Test the underlying function directly
    print(trend_analysis_tool_func(sample_docs))
    
    # Or test through the Tool's func with proper input format
    print(trend_analysis_tool.func({"texts": sample_docs}))