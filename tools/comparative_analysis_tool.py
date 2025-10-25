# tools/comparative_analysis_tool.py
from mcp import Tool
from pydantic import BaseModel, Field
from typing import List

class ComparativeAnalysisInput(BaseModel):
    documents: List[str] = Field(..., description="List of document texts to compare")

class ComparativeAnalysisTool(Tool):
    def __init__(self):
        super().__init__(
            name="comparative_analysis",
            description="Compares multiple document snippets and highlights similarities and differences.",
            inputSchema=ComparativeAnalysisInput.model_json_schema()
        )

    def run(self, documents: list):
        # Placeholder logic: just return length of each document
        results = [{"doc_index": i, "length": len(doc)} for i, doc in enumerate(documents)]
        return results
