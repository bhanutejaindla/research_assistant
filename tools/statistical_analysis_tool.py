# tools/statistical_analysis_tool.py
from mcp import Tool
from pydantic import BaseModel, Field
from typing import List

class StatisticalAnalysisInput(BaseModel):
    documents: List[str] = Field(..., description="List of document texts for quantitative analysis")

class StatisticalAnalysisTool(Tool):
    def __init__(self):
        super().__init__(
            name="statistical_analysis",
            description="Performs basic statistical analysis on the documents.",
            inputSchema=StatisticalAnalysisInput.model_json_schema()
        )

    def run(self, documents: list):
        # Placeholder: calculate word count per document
        results = [{"doc_index": i, "word_count": len(doc.split())} for i, doc in enumerate(documents)]
        return results
