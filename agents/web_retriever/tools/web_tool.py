# agents/web_retriever/tools/web_tool.py
from fastmcp import FastMCP
import requests
from readability import Document
from bs4 import BeautifulSoup
import chardet
from agents.web_retriever.config import FETCH_TIMEOUT, USER_AGENT
from typing import Optional

mcp = FastMCP("web-tool")

@mcp.tool()
def fetch_webpage(url: str) -> dict:
    """
    Fetches a webpage and extracts readable text content.
    
    Args:
        url: The URL of the webpage to fetch
    
    Returns:
        Dictionary containing url, title, text, and metadata, or error message
    """
    headers = {"User-Agent": USER_AGENT}
    
    try:
        r = requests.get(url, headers=headers, timeout=FETCH_TIMEOUT)
        
        if r.status_code != 200:
            return {"error": f"Failed to fetch {url}: {r.status_code}"}

        raw_bytes = r.content
        enc = chardet.detect(raw_bytes).get("encoding", "utf-8")
        html = raw_bytes.decode(enc, errors="replace")

        doc = Document(html)
        title = doc.short_title()
        summary_html = doc.summary()
        text = BeautifulSoup(summary_html, "html.parser").get_text(separator="\n")

        return {
            "url": url,
            "title": title,
            "text": text,
            "metadata": {
                "length": len(text),
                "status": r.status_code,
                "encoding": enc
            }
        }
    
    except requests.exceptions.Timeout:
        return {"error": f"Request to {url} timed out after {FETCH_TIMEOUT} seconds"}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed for {url}: {str(e)}"}
    except Exception as e:
        return {"error": f"Error processing {url}: {str(e)}"}

# Backwards compatibility
def run(url: str):
    return fetch_webpage(url)

# Export
__all__ = ['fetch_webpage', 'run', 'mcp']

if __name__ == "__main__":
    mcp.run()