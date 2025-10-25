# tools/causal_reasoning_tool.py
from mcp import Tool
from pydantic import BaseModel, Field
from typing import List

class CausalReasoningInput(BaseModel):
    documents: List[str] = Field(..., description="List of document texts to analyze for cause-effect relationships")

class CausalReasoningTool(Tool):
    def __init__(self):
        super().__init__(
            name="causal_reasoning",
            description="Identifies potential cause-effect relationships within documents.",
            inputSchema=CausalReasoningInput.model_json_schema()
        )

    def run(self, documents: list):
        # Placeholder: pretend every sentence with 'because' is a causal sentence
        results = []
        for i, doc in enumerate(documents):
            causal_sentences = [s for s in doc.split(".") if "because" in s.lower()]
            results.append({"doc_index": i, "causal_sentences": causal_sentences})
        return results
