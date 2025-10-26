from fastmcp import FastMCP
import matplotlib.pyplot as plt
import os
from agents.output_formatter.config import VISUALIZATION_OUTPUT_DIR

# Ensure output directory exists
os.makedirs(VISUALIZATION_OUTPUT_DIR, exist_ok=True)

# Initialize FastMCP instance
mcp = FastMCP("visualization_generator_tool")

@mcp.tool(
    name="visualization_generator",
    description="Generates bar or line charts from structured data and saves the image locally."
)
def visualization_generator(data: dict, title: str = "Chart", chart_type: str = "bar") -> dict:
    """
    Generates a visualization (bar or line chart) from given data.
    Saves the image locally and returns the file path.
    """
    if not data:
        return {"error": "No data provided."}

    labels = list(data.keys())
    values = list(data.values())

    plt.figure(figsize=(6, 4))
    if chart_type == "bar":
        plt.bar(labels, values)
    elif chart_type == "line":
        plt.plot(labels, values, marker="o")
    else:
        return {"error": "Unsupported chart type. Use 'bar' or 'line'."}

    plt.title(title)
    plt.xlabel("Categories")
    plt.ylabel("Values")

    # Save image
    file_name = f"{title.replace(' ', '_')}.png"
    path = os.path.join(VISUALIZATION_OUTPUT_DIR, file_name)
    plt.savefig(path, bbox_inches="tight")
    plt.close()

    return {"image_path": path}


# -------------------------------------------------------------
# ✅ MAIN (for testing or MCP server mode)
# -------------------------------------------------------------
if __name__ == "__main__":
    # Sample data for quick test
    sample_data = {"A": 10, "B": 25, "C": 17, "D": 30}

    print("📊 Generating visualization...\n")
    result = visualization_generator(sample_data, title="Sample_Report_Data", chart_type="bar")

    if "error" in result:
        print("❌ Error:", result["error"])
    else:
        print(f"✅ Chart successfully generated at: {result['image_path']}")

    # Uncomment below to start as FastMCP tool server
    # mcp.run()
