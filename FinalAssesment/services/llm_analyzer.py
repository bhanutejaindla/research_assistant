import os
import asyncio
from openai import OpenAI
from services.event_manager import EventManager

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def analyze_repo_with_llm(
    project_id: int,
    repo_path: str,
    metadata: dict,
    event_manager: EventManager
):
    """
    Analyze repository code snippets using an LLM to infer key characteristics.

    Steps:
      1. Collect representative code snippets (async-safe).
      2. Send status updates via EventManager.
      3. Call OpenAI model for analysis.
      4. Return structured text insights.
    """
    await event_manager.send(project_id, "🤖 Starting LLM-based repository analysis...")

    file_snippets = []
    max_files = 5
    max_chars = 1000

    # Collect representative snippets asynchronously
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith((".py", ".js", ".ts", ".jsx", ".tsx")):
                path = os.path.join(root, file)
                try:
                    # Offload blocking file I/O to a thread
                    snippet = await asyncio.to_thread(read_snippet, path, max_chars)
                    file_snippets.append(f"### {file}\n{snippet}")
                except Exception as e:
                    await event_manager.send(project_id, f"⚠️ Skipped {file}: {str(e)}")
                    continue

                if len(file_snippets) >= max_files:
                    break
        if len(file_snippets) >= max_files:
            break

    context = "\n\n".join(file_snippets)
    prompt = f"""
You are an intelligent code analyst. Analyze the following repository.

Identify and summarize:
1. The main language(s) and frameworks used
2. The overall purpose of the repository
3. Major components (API, frontend, database, etc.)
4. Notable libraries or dependencies

Metadata:
{metadata}

Code Snippets:
{context}
"""

    try:
        # Run LLM call in a thread to avoid blocking
        response = await asyncio.to_thread(
            client.responses.create,
            model="gpt-4o-mini",
            input=prompt
        )

        insights = response.output_text.strip()
        await event_manager.send(project_id, "✅ LLM analysis complete.")
        return insights

    except Exception as e:
        await event_manager.send(project_id, f"❌ LLM analysis failed: {str(e)}")
        return {"error": str(e)}


def read_snippet(path: str, limit: int = 1000) -> str:
    """Read a snippet of the file content safely."""
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read(limit)
