from mcp import Tool
from pydantic import BaseModel, Field
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Define the input schema using Pydantic
class LLMAnalysisInput(BaseModel):
    prompt: str = Field(
        description="Analysis prompt for the LLM to process and provide insights on",
        min_length=1
    )

def llm_analysis_tool_func(prompt: str) -> str:
    """
    Uses an LLM to provide deep analytical insights or reasoning based on a prompt.
    """
    if not prompt:
        return "Please provide a valid analysis prompt."
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"Analyze this deeply:\n{prompt}"}]
    )
    return response.choices[0].message.content

# ✅ Register the tool with MCP with the required inputSchema
llm_analysis_tool = Tool(
    name="llm_analysis_tool",
    description="Leverages an LLM to provide high-level analytical reasoning.",
    inputSchema=LLMAnalysisInput.model_json_schema(),
    func=lambda input_data: llm_analysis_tool_func(**input_data)
)

if __name__ == "__main__":
    prompt = "Compare the long-term economic impact of AI adoption in healthcare vs manufacturing."
    # Test the underlying function directly
    print(llm_analysis_tool_func(prompt))
    
    # Or test through the Tool's func with proper input format
    print(llm_analysis_tool.func({"prompt": prompt}))