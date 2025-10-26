from mcp import Tool
from pydantic import BaseModel, Field

# Define the input schema using Pydantic
class ComparativeAnalysisInput(BaseModel):
    documents: list[str] = Field(
        description="List of documents to compare (minimum 2 required)",
        min_length=2
    )

# Define the function
def comparative_analysis_tool(documents: list[str]) -> str:
    """
    Perform a basic comparative analysis between multiple documents.
    """
    if not documents or len(documents) < 2:
        return "Please provide at least two documents for comparison."

    base_doc = documents[0]
    similarities = []
    differences = []

    for idx, doc in enumerate(documents[1:], start=2):
        common = set(base_doc.split()).intersection(set(doc.split()))
        diff = set(base_doc.split()).symmetric_difference(set(doc.split()))
        similarities.append(f"Doc 1 & Doc {idx} Similar Words: {len(common)}")
        differences.append(f"Doc 1 & Doc {idx} Different Words: {len(diff)}")

    report = "\n".join(similarities + differences)
    return f"--- Comparative Analysis Report ---\n{report}"


# ✅ Register the tool with MCP with the required inputSchema
comparative_analysis = Tool(
    name="comparative_analysis_tool",
    description="Compares multiple documents to find key differences and similarities.",
    inputSchema=ComparativeAnalysisInput.model_json_schema(),
    func=lambda input_data: comparative_analysis_tool(**input_data)
)


# ✅ Local test block
if __name__ == "__main__":
    docs = [
        "AI is transforming the research landscape by enabling automation.",
        "Automation through AI is changing how research is conducted."
    ]
    # Test the underlying function directly
    print(comparative_analysis_tool(docs))
    
    # Or test through the Tool's func with proper input format
    print(comparative_analysis.func({"documents": docs}))