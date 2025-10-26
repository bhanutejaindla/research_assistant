# agents/web_retriever/tools/keyword_search_tool.py
from fastmcp import FastMCP
from agents.web_retriever.config import KEYWORD_DB_PATH
from typing import Optional, Literal
import os, json, re

mcp = FastMCP("keyword-search-tool")

# Implementation function (no decorator)
def _keyword_search_impl(
    action: Literal["store", "search"],
    doc_id: Optional[str] = None,
    text: Optional[str] = None,
    query: Optional[str] = None,
    top_k: int = 5
) -> dict:
    os.makedirs(os.path.dirname(KEYWORD_DB_PATH), exist_ok=True)

    # Indexing
    if action == "store" and doc_id and text:
        entry = {"doc_id": doc_id, "text": text}
        with open(KEYWORD_DB_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
        return {"status": "stored"}

    # Search
    if action == "search" and query:
        results = []
        if os.path.exists(KEYWORD_DB_PATH):
            q = query.lower()
            with open(KEYWORD_DB_PATH, "r") as f:
                for line in f:
                    try:
                        doc = json.loads(line)
                    except Exception:
                        continue
                    text = doc.get("text", "")
                    if q in text.lower():
                        score = len(re.findall(re.escape(q), text.lower()))
                        results.append({"doc_id": doc.get("doc_id"), "text": text, "score": score})
        results = sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]
        return {"results": results}

    return {"error": "Invalid parameters"}

# Register with MCP
@mcp.tool()
def keyword_search(
    action: Literal["store", "search"],
    doc_id: Optional[str] = None,
    text: Optional[str] = None,
    query: Optional[str] = None,
    top_k: int = 5
) -> dict:
    """
    Index or search documents using exact/substring keywords.
    
    Args:
        action: Either "store" to index a document or "search" to query
        doc_id: Document identifier (required for store action)
        text: Document text content (required for store action)
        query: Search query (required for search action)
        top_k: Number of top results to return (default: 5)
    
    Returns:
        Dictionary with status/results or error message
    """
    return _keyword_search_impl(action=action, doc_id=doc_id, text=text, query=query, top_k=top_k)

# Backwards compatibility
def run(action: str, doc_id: str = None, text: str = None, query: str = None, top_k: int = 5):
    return _keyword_search_impl(action=action, doc_id=doc_id, text=text, query=query, top_k=top_k)

# Export
__all__ = ['keyword_search', 'run', 'mcp']

if __name__ == "__main__":
    mcp.run()