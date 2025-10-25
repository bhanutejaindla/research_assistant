# tools/trend_analysis_tool.py
from mcp import Tool
from pydantic import BaseModel, Field
from typing import List

class TrendAnalysisInput(BaseModel):
    documents: List[str] = Field(..., description="List of document texts to analyze trends")

class TrendAnalysisTool(Tool):
    def __init__(self):
        super().__init__(
            name="trend_analysis",
            description="Detects temporal patterns or trends in the provided documents.",
            inputSchema=TrendAnalysisInput.model_json_schema()
        )

    def run(self, documents: list):
        # Placeholder: count mentions of "AI" over documents
        results = [{"doc_index": i, "AI_mentions": doc.lower().count("ai")} for i, doc in enumerate(documents)]
        return results
