from mcp import Tool
from pydantic import BaseModel, Field

# Define the input schema using Pydantic
class CausalReasoningInput(BaseModel):
    observations: list[str] = Field(
        description="List of observations to analyze for cause-effect relationships",
        min_length=1
    )

def causal_reasoning_tool_func(observations: list[str]) -> str:
    """
    Simplistic causal reasoning: tries to detect cause-effect pairs based on text patterns.
    """
    if not observations:
        return "Please provide observations for causal reasoning."
    
    causal_pairs = []
    for obs in observations:
        if "because" in obs:
            parts = obs.split("because")
            if len(parts) >= 2:
                cause = parts[1].strip().rstrip('.')
                effect = parts[0].strip().rstrip('.')
                causal_pairs.append(f"Effect: {effect} ← Cause: {cause}")
        elif "due to" in obs:
            parts = obs.split("due to")
            if len(parts) >= 2:
                cause = parts[1].strip().rstrip('.')
                effect = parts[0].strip().rstrip('.')
                causal_pairs.append(f"Effect: {effect} ← Cause: {cause}")
    
    if not causal_pairs:
        return "No explicit causal relationships detected."
    
    report = "\n".join(causal_pairs)
    return f"--- Causal Reasoning Report ---\n{report}"

# ✅ Register the tool with MCP with the required inputSchema
causal_reasoning_tool = Tool(
    name="causal_reasoning_tool",
    description="Extracts possible cause-effect relationships from text.",
    inputSchema=CausalReasoningInput.model_json_schema(),
    func=lambda input_data: causal_reasoning_tool_func(**input_data)
)

if __name__ == "__main__":
    examples = [
        "The experiment failed because the temperature was too high.",
        "Productivity increased due to better collaboration."
    ]
    # Test the underlying function directly
    print(causal_reasoning_tool_func(examples))
    
    # Or test through the Tool's func with proper input format
    print(causal_reasoning_tool.func({"observations": examples}))