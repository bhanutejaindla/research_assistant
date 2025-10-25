from mcp.server.fastmcp import FastMCP
from retrieval_agent.tools.web_scraper_tool import scrape_website
from retrieval_agent.tools.keyword_search_tool import keyword_search
from retrieval_agent.tools.embedding_storage_tool import store_embedding, query_similar_documents

app = FastMCP("retrieval_agent_tools")

@app.tool()
def web_scraper(url: str) -> dict:
    return scrape_website(url)

@app.tool()
def search_keyword(keyword: str) -> list:
    return keyword_search(keyword)

@app.tool()
def save_document_embedding(document: str) -> str:
    return store_embedding(document)

@app.tool()
def get_similar_documents(query: str, top_k: int = 5) -> list:
    return query_similar_documents(query, top_k)

if __name__ == "__main__":
    app.run()
