from mcp import Tool
from pydantic import BaseModel, Field
import statistics

# Define the input schema using Pydantic
class StatisticalAnalysisInput(BaseModel):
    data: list[float] = Field(
        description="List of numerical values to analyze statistically",
        min_length=1
    )

def statistical_analysis_tool_func(data: list[float]) -> str:
    """
    Performs simple statistical calculations on numerical data.
    """
    if not data:
        return "Please provide numerical data for statistical analysis."
    
    try:
        mean_val = statistics.mean(data)
        median_val = statistics.median(data)
        stdev_val = statistics.stdev(data) if len(data) > 1 else 0.0
    except Exception as e:
        return f"Error in computation: {str(e)}"
    
    return (
        "--- Statistical Analysis Report ---\n"
        f"Mean: {mean_val:.2f}\n"
        f"Median: {median_val:.2f}\n"
        f"Standard Deviation: {stdev_val:.2f}"
    )

# ✅ Register the tool with MCP with the required inputSchema
statistical_analysis_tool = Tool(
    name="statistical_analysis_tool",
    description="Performs basic statistical analysis (mean, median, std deviation).",
    inputSchema=StatisticalAnalysisInput.model_json_schema(),
    func=lambda input_data: statistical_analysis_tool_func(**input_data)
)

if __name__ == "__main__":
    nums = [10, 15, 20, 25, 30]
    # Test the underlying function directly
    print(statistical_analysis_tool_func(nums))
    
    # Or test through the Tool's func with proper input format
    print(statistical_analysis_tool.func({"data": nums}))