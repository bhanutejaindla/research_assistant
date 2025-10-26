# agents/web_retriever/tools/rag_tool.py
from fastmcp import FastMCP
from agents.web_retriever.tools import web_tool, semantic_search_tool, keyword_search_tool
from typing import List, Optional

mcp = FastMCP("rag-tool")

def llm_generate(prompt: str) -> str:
    # Placeholder LLM call
    return f"[LLM Answer]\nPrompt:\n{prompt[:500]}..."

# Implementation function (no decorator)
def _rag_search_impl(query: str, urls: Optional[List[str]] = None, top_k: int = 5) -> dict:
    """Implementation of RAG search logic"""
    if urls is None:
        urls = []
    
    # Step 1: Scrape + store
    for url in urls:
        print(f"Fetching: {url}")  # DEBUG
        web_result = web_tool.run(url=url)
        if "text" in web_result:
            print(f"Text length: {len(web_result['text'])}")  # DEBUG
            
            # Store in semantic search
            sem_store = semantic_search_tool.run(action="store", url=url, text=web_result["text"])
            print(f"Semantic store result: {sem_store}")  # DEBUG
            
            # Store in keyword search
            key_store = keyword_search_tool.run(action="store", doc_id=url, text=web_result["text"])
            print(f"Keyword store result: {key_store}")  # DEBUG
        else:
            print(f"No text found for {url}")  # DEBUG

    # Step 2: Retrieve top-K
    print(f"\nSearching for: {query}")  # DEBUG
    sem_results = semantic_search_tool.run(action="search", query=query, top_k=top_k).get("results", [])
    print(f"Semantic results count: {len(sem_results)}")  # DEBUG
    
    key_results = keyword_search_tool.run(action="search", query=query, top_k=top_k).get("results", [])
    print(f"Keyword results count: {len(key_results)}")  # DEBUG

    # Combine context
    combined_context = "\n".join([d.get("snippet", d.get("text", "")) for d in sem_results + key_results])
    print(f"Combined context length: {len(combined_context)}")  # DEBUG

    # Step 3: LLM answer
    prompt = f"Answer the question using the context below:\n{combined_context}\nQuestion: {query}"
    answer = llm_generate(prompt)

    return {
        "query": query,
        "retrieved_docs": sem_results + key_results,
        "llm_answer": answer
    }

# Register with MCP - calls implementation
@mcp.tool()
def rag_search(query: str, urls: Optional[List[str]] = None, top_k: int = 5) -> dict:
    """
    Full RAG: scrape URLs, store embeddings in Postgres, keyword index, retrieve, generate LLM answer.
    
    Args:
        query: The search query
        urls: Optional list of URLs to scrape and index
        top_k: Number of top results to retrieve (default: 5)
    
    Returns:
        Dictionary containing query, retrieved_docs, and llm_answer
    """
    return _rag_search_impl(query=query, urls=urls, top_k=top_k)

# Keep the run function for backwards compatibility
def run(query: str, urls: Optional[List[str]] = None, top_k: int = 5):
    return _rag_search_impl(query=query, urls=urls, top_k=top_k)

# Export
__all__ = ['rag_search', 'run', 'mcp']

if __name__ == "__main__":
    mcp.run()