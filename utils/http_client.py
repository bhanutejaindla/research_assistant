# utils/http_client.py
"""
Simple HTTP client helper for coordinator to call other agents' tools.

Important notes:
- This is a minimalist helper. Ensure your remote MCP servers expose a
  compatible REST endpoint. The default assumption used by coordinator_server.py:
    POST <base_url>/tools/<tool>
  with JSON body equals payload.

- Adapt the URL/path logic if your agent services expose different routes.
"""

import requests
from typing import Any, Dict
from utils.logger import get_logger

logger = get_logger("http_client")

def call_remote_tool(url: str, payload: Dict[str, Any], timeout: int = 30) -> Any:
    """
    Call a remote tool via HTTP POST, expecting JSON response.
    Returns the parsed JSON response, or raises on network errors.
    """
    headers = {"Content-Type": "application/json"}
    try:
        logger.info(f"POST {url} payload keys: {list(payload.keys())}")
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        resp.raise_for_status()
        try:
            data = resp.json()
            logger.info(f"Received JSON response from {url}")
            return data
        except ValueError:
            # not JSON — return raw text
            logger.warning(f"Non-JSON response from {url}: returning raw text")
            return resp.text
    except requests.RequestException as e:
        logger.exception(f"HTTP call to {url} failed: {e}")
        raise
