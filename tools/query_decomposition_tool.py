# tools/query_decomposition_tool.py
from typing import Type
from pydantic import BaseModel, Field
from mcp import Tool

# 1️⃣ Input schema
class QueryDecompositionInput(BaseModel):
    query: str = Field(..., description="The research query to decompose")

# 2️⃣ MCP tool definition
class QueryDecompositionTool(Tool):
    name: str = "query_decomposition"  # type annotation required
    description: str = "Decomposes a research query into subtasks"
    inputSchema: Type[BaseModel] = QueryDecompositionInput  # type annotation required

    def run(self, query: str):
        # Simple sentence-based decomposition
        subtasks = [q.strip() for q in query.split('.') if q.strip()]
        return subtasks
