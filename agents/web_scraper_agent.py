# agents/web_scraper_agent.py
from tools.web_scraping_tool import WebScrapingTool
from tools.keyword_search_tool import KeywordSearchTool
from tools.semantic_search_tool import SemanticSearchTool

class WebScraperAgent:
    def __init__(self):
        self.scraper_tool = WebScrapingTool()
        self.keyword_tool = KeywordSearchTool()
        self.semantic_tool = SemanticSearchTool()

    def gather_data(self, query: str):
        keywords = self.keyword_tool.run(query=query)
        print("Extracted Keywords:", keywords)

        # (Simulate web scraping)
        if keywords:
            url_keyword = keywords[0].lower()  # lowercase
            url_keyword = url_keyword.replace(" ", "_")  # spaces → underscores
            url = f"https://en.wikipedia.org/wiki/{keywords[0]}"
            print(f"Scraping data from: {url}")
            content = self.scraper_tool.run(url=url)
        else:
            content = "No keywords found."

        semantic_results = self.semantic_tool.run(query=query)
        return {"scraped_content": content, "semantic_results": semantic_results}

if __name__ == "__main__":
    agent = WebScraperAgent()
    query = "Recent advancements in AI, focusing on Retrieval-Augmented Generation (RAG)."
    data = agent.gather_data(query)
    print("\n--- Agent Output ---")
    print(data)