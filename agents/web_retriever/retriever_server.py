# agents/web_retriever/retriever_server.py
from fastmcp import FastMCP
from agents.web_retriever import tools

app = FastMCP(
    name="web_retriever_agent",
    description="Agent 2: Web Scraper & Document Retrieval Agent (RAG-ready, Postgres + pgvector)"
)

# Register all tools
for tool_module in [tools.web_tool, tools.semantic_search_tool, tools.keyword_search_tool, tools.rag_tool]:
    app.register_tool(tool_module.tool_spec)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8002)
