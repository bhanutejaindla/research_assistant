# agents/coordinator/config.py
"""
Configuration for Coordinator Agent.
Edit the AGENT_ENDPOINTS dictionary to point to your other agent MCP servers.
These URLs are used by the coordinator's http client to call remote tools.
"""

# Example endpoints (update to actual host:port or service addresses)
AGENT_ENDPOINTS = {
    "retrieval": "http://localhost:8001",    # Retrieval MCP server base URL
    "analysis": "http://localhost:8002",     # Analysis MCP server base URL
    "validation": "http://localhost:8003",   # Validation MCP server base URL
    "output": "http://localhost:8004",       # Output formatting MCP server base URL
}

# Tool paths used by the http client (convention - customize as needed).
# The coordinator will POST to: <base_url> + tool_path.format(tool=tool_name)
# Example default pattern expects endpoints like: http://host:port/tools/<tool>
TOOL_INVOKE_PATH = "/tools/{tool}"  # customize if your MCP servers expose different routes

# Timeout for HTTP calls (seconds)
HTTP_TIMEOUT = 30
