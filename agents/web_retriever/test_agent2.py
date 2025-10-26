# agents/web_retriever/test_agent2.py

# Test web_tool
from agents.web_retriever.tools.web_tool import run as web_run

print("=== Testing web_tool ===")
url = "https://en.wikipedia.org/wiki/Artificial_intelligence"
result = web_run(url)
print("Title:", result.get("title"))
print("Text snippet:", result.get("text")[:300])
print("\n")

# Test semantic_search_tool
from agents.web_retriever.tools.semantic_search_tool import run as sem_run
print("=== Testing semantic_search_tool ===")
sem_run(action="store", url=url, text=result.get("text"))
search_results = sem_run(action="search", query="AI in machines", top_k=2)
print("Semantic Search Results:", search_results)
print("\n")

# Test keyword_search_tool
from agents.web_retriever.tools.keyword_search_tool import run as key_run
print("=== Testing keyword_search_tool ===")
key_run(action="store", doc_id=url, text=result.get("text"))
keyword_results = key_run(action="search", query="intelligence", top_k=2)
print("Keyword Search Results:", keyword_results)
print("\n")

# Test rag_tool
from agents.web_retriever.tools.rag_tool import run as rag_run
print("=== Testing rag_tool ===")
rag_result = rag_run(query="What is Artificial Intelligence?", urls=[url], top_k=2)
print("LLM Answer:\n", rag_result["llm_answer"])
print("Retrieved Docs:\n", rag_result["retrieved_docs"])


