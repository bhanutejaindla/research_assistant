# agents/research_coordinator_agent.py
from mcp import MCPClient
from typing import List

class ResearchCoordinatorAgent:
    def __init__(self):
        # Connect to MCP server
        self.client = MCPClient(base_url="http://localhost:8000")  # adjust if different

        # Register MCP tools
        self.query_tool = self.client.get_tool("query_decomposition")
        self.prioritization_tool = self.client.get_tool("task_prioritization")

    def handle_query(self, query: str) -> List[str]:
        # Step 1: Decompose query
        subtasks = self.query_tool.run(query=query)
        print("\n✅ Subtasks extracted:", subtasks)

        # Step 2: Prioritize tasks
        prioritized_tasks = self.prioritization_tool.run(tasks=subtasks)
        print("\n✅ Prioritized tasks:", prioritized_tasks)

        return prioritized_tasks


if __name__ == "__main__":
    query = "Find latest AI research trends, analyze retrieval-augmented generation models, summarize insights."
    agent = ResearchCoordinatorAgent()
    tasks = agent.handle_query(query)
