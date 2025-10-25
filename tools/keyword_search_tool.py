# tools/keyword_search_tool.py
from mcp import Tool
from pydantic import BaseModel, Field
import re

class KeywordSearchInput(BaseModel):
    query: str = Field(..., description="The research query text")

class KeywordSearchTool(Tool):
    def __init__(self):
        super().__init__(
            name="keyword_search",
            description="Extracts main keywords from a query.",
            inputSchema=KeywordSearchInput.model_json_schema()  # ✅ required by MCP
        )

    def run(self, query: str):
        words = re.findall(r'\b[A-Za-z]{5,}\b', query)
        keywords = list(set(words))[:5]
        return keywords
