# tools/web_scraping_tool.py
from mcp import Tool
from pydantic import BaseModel, Field
import requests
from bs4 import BeautifulSoup
from typing import ClassVar, Optional
import time
from urllib.parse import urlparse

class WebScrapingInput(BaseModel):
    url: str = Field(..., description="The URL to scrape data from")
    max_length: Optional[int] = Field(5000, description="Maximum length of scraped content")
    timeout: Optional[int] = Field(10, description="Request timeout in seconds")

class WebScrapingTool(Tool):
    name: str = "web_scraper"
    inputSchema: ClassVar = WebScrapingInput

    def __init__(self):
        super().__init__()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                          "AppleWebKit/537.36 (KHTML, like Gecko) "
                          "Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        })
        self.last_request_time = 0
        self.min_delay = 1  # Minimum delay between requests in seconds

    def _is_valid_url(self, url: str) -> bool:
        """Validate URL format"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False

    def _rate_limit(self):
        """Implement rate limiting to be respectful"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_delay:
            time.sleep(self.min_delay - time_since_last)
        self.last_request_time = time.time()

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content, removing noise"""
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                             'aside', 'iframe', 'noscript', 'meta', 'link']):
            element.decompose()

        # Try to find main content areas (common patterns)
        main_content = None
        
        # Try common content containers
        content_selectors = [
            'main',
            'article',
            '[role="main"]',
            '.content',
            '#content',
            '.main-content',
            '#main-content',
            '.post-content',
            '.article-content'
        ]
        
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
        
        # Fallback to body if no main content found
        if not main_content:
            main_content = soup.find('body')
        
        if not main_content:
            return ""

        # Get text with proper spacing
        text = main_content.get_text(separator=' ', strip=True)
        
        # Clean up extra whitespace
        text = ' '.join(text.split())
        
        return text

    def _extract_metadata(self, soup: BeautifulSoup) -> dict:
        """Extract useful metadata from the page"""
        metadata = {
            'title': '',
            'description': '',
            'author': '',
            'date': ''
        }
        
        # Get title
        title_tag = soup.find('title')
        if title_tag:
            metadata['title'] = title_tag.get_text(strip=True)
        
        # Get meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            metadata['description'] = meta_desc.get('content')
        
        # Get author
        meta_author = soup.find('meta', attrs={'name': 'author'})
        if meta_author and meta_author.get('content'):
            metadata['author'] = meta_author.get('content')
        
        # Get date (try multiple formats)
        date_selectors = [
            ('meta', {'property': 'article:published_time'}),
            ('meta', {'name': 'date'}),
            ('time', {'class': 'published'})
        ]
        
        for tag, attrs in date_selectors:
            date_elem = soup.find(tag, attrs=attrs)
            if date_elem:
                metadata['date'] = date_elem.get('content') or date_elem.get_text(strip=True)
                break
        
        return metadata

    def run(self, url: str, max_length: int = 5000, timeout: int = 10) -> dict:
        """
        Scrape content from a URL
        
        Args:
            url: The URL to scrape
            max_length: Maximum length of content to return
            timeout: Request timeout in seconds
            
        Returns:
            dict with 'content', 'metadata', 'url', and 'success' status
        """
        result = {
            'url': url,
            'success': False,
            'content': '',
            'metadata': {},
            'error': None
        }
        
        # Validate URL
        if not self._is_valid_url(url):
            result['error'] = "Invalid URL format"
            return result
        
        try:
            # Rate limiting
            self._rate_limit()
            
            # Make request
            response = self.session.get(
                url, 
                timeout=timeout,
                allow_redirects=True,
                verify=True  # Verify SSL certificates
            )
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text/html' not in content_type and 'application/xhtml' not in content_type:
                result['error'] = f"Unsupported content type: {content_type}"
                return result
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract metadata
            result['metadata'] = self._extract_metadata(soup)
            
            # Extract main content
            content = self._extract_main_content(soup)
            
            # Truncate if needed
            if len(content) > max_length:
                content = content[:max_length] + "... [truncated]"
            
            result['content'] = content
            result['success'] = True
            
            return result
            
        except requests.exceptions.Timeout:
            result['error'] = f"Request timeout after {timeout} seconds"
        except requests.exceptions.ConnectionError:
            result['error'] = "Connection error - could not reach the URL"
        except requests.exceptions.HTTPError as e:
            result['error'] = f"HTTP error: {e.response.status_code}"
        except requests.exceptions.RequestException as e:
            result['error'] = f"Request failed: {str(e)}"
        except Exception as e:
            result['error'] = f"Unexpected error: {str(e)}"
        
        return result

    def run_batch(self, urls: list, max_length: int = 5000) -> list:
        """Scrape multiple URLs"""
        results = []
        for url in urls:
            result = self.run(url, max_length=max_length)
            results.append(result)
            # Add delay between batch requests
            if len(urls) > 1:
                time.sleep(self.min_delay)
        return results


# Example usage
if __name__ == "__main__":
    scraper = WebScrapingTool()
    
    # Test with a single URL
    result = scraper.run("https://en.wikipedia.org/wiki/Artificial_intelligence")
    
    if result['success']:
        print(f"Title: {result['metadata']['title']}")
        print(f"Content length: {len(result['content'])}")
        print(f"Content preview: {result['content'][:200]}...")
    else:
        print(f"Error: {result['error']}")