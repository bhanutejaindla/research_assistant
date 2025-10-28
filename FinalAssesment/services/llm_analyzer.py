# services/llm_analyzer.py
import os
from openai import OpenAI
from services.event_manager import EventManager

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

async def analyze_repo_with_llm(repo_path: str, metadata: dict, event_manager: EventManager, project_id: int):
    await event_manager.send(project_id, "🧠 Running LLM-based repository analysis...")

    # Collect a few code snippets for context
    snippets = []
    for root, _, files in os.walk(repo_path):
        for file in files:
            if file.endswith((".py", ".js", ".ts")):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        snippets.append(f"### {file}\n{f.read(500)}")
                except Exception:
                    continue
        if len(snippets) >= 3:
            break

    prompt = f"""
    You are an expert software analyst. Analyze the following repository metadata and code snippets.
    Summarize:
    1. Main language and frameworks
    2. Purpose of the repo
    3. Key modules or files
    4. Libraries/dependencies used
    Metadata:
    {metadata}
    Code Snippets:
    {'\\n'.join(snippets)}
    """

    try:
        response = client.responses.create(model="gpt-4o-mini", input=prompt)
        result = response.output[0].content[0].text
        await event_manager.send(project_id, "✅ LLM analysis complete.")
        return result
    except Exception as e:
        await event_manager.send(project_id, f"❌ LLM analysis failed: {str(e)}")
        return {"error": str(e)}
