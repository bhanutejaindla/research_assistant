# services/llm_analyzer.py
import os
from openai import OpenAI
from services.event_manager import EventManager

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def analyze_repo_with_llm(repo_path: str, metadata: dict, event_manager: EventManager):
    await event_manager.send(0, "Analyzing repository using LLM...")

    # Read some representative files (limit size)
    file_snippets = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith((".py", ".js", ".ts")):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        snippet = f.read(1000)
                    file_snippets.append(f"### {file}\n{snippet}")
                except Exception:
                    continue
        if len(file_snippets) > 5:
            break

    context = "\n\n".join(file_snippets)
    prompt = f"""
    Analyze the following repository code snippets.
    Identify:
    1. The language and framework used
    2. The main purpose of the repo
    3. Important components (e.g., API, frontend, database)
    4. Notable libraries or dependencies

    Metadata:
    {metadata}

    Code Snippets:
    {context}
    """

    response = client.responses.create(
        model="gpt-4o-mini",
        input=prompt
    )

    insights = response.output[0].content[0].text
    await event_manager.send(0, "LLM analysis complete.")
    return insights
