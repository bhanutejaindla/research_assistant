# agents/web_retriever/tools/rag_tool.py
from fastmcp import FastMCP
from agents.web_retriever.tools import web_tool, semantic_search_tool, keyword_search_tool
from typing import List, Optional

mcp = FastMCP("rag-tool")

def llm_generate(prompt: str) -> str:
    # Placeholder LLM call
    return f"[LLM Answer]\nPrompt:\n{prompt[:500]}..."

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
    if urls is None:
        urls = []
    
    # Step 1: Scrape + store
    for url in urls:
        web_result = web_tool.run(url=url)
        if "text" in web_result:
            semantic_search_tool.run(action="store", url=url, text=web_result["text"])
            keyword_search_tool.run(action="store", doc_id=url, text=web_result["text"])

    # Step 2: Retrieve top-K
    sem_results = semantic_search_tool.run(action="search", query=query, top_k=top_k).get("results", [])
    key_results = keyword_search_tool.run(action="search", query=query, top_k=top_k).get("results", [])

    # Combine context
    combined_context = "\n".join([d.get("snippet", d.get("text", "")) for d in sem_results + key_results])

    # Step 3: LLM answer
    prompt = f"Answer the question using the context below:\n{combined_context}\nQuestion: {query}"
    answer = llm_generate(prompt)

    return {
        "query": query,
        "retrieved_docs": sem_results + key_results,
        "llm_answer": answer
    }

# Keep the run function for backwards compatibility if needed
def run(query: str, urls: List[str] = [], top_k: int = 5):
    return rag_search(query=query, urls=urls, top_k=top_k)