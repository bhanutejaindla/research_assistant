# agents/coordinator/tools/query_decomposer.py
from typing import List, Dict
import re
import os
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()  # This will automatically load OPENAI_API_KEY
# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def decompose_query(query: str, use_llm: bool = True) -> List[Dict]:
    """
    Decompose the user's query into smaller subtasks.
    Returns a list of dicts: [{"task": "subtask 1"}, {"task": "subtask 2"}, ...]
    
    Parameters:
        query: The main user query string
        use_llm: Whether to use LLM for decomposition (falls back to regex if False or LLM fails)
    """
    if not query:
        return []

    if use_llm:
        try:
            prompt = f"""
            You are a research assistant. Break down the following query into 
            independent, actionable subtasks. Return only a clean numbered list, 
            one subtask per line. Do not include extra text.

            Query: {query}
            """
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            tasks_text = response.choices[0].message.content
            # Split by lines and clean
            tasks = [t.strip("0123456789. ").strip() for t in tasks_text.split("\n") if t.strip()]
            return [{"task": t} for t in tasks if t]

        except Exception as e:
            print(f"[WARN] LLM decomposition failed, falling back to regex. Error: {e}")

    # === Fallback: Regex-based decomposition ===
    s = " ".join(query.split())
    parts = re.split(r'[?;\n]+', s)
    subtasks = []
    for p in parts:
        subparts = re.split(r'\band\b|\bor\b|,', p, flags=re.IGNORECASE)
        for sp in subparts:
            candidate = sp.strip()
            if candidate and len(candidate) > 3:
                subtasks.append(candidate)

    # Deduplicate while preserving order
    seen = set()
    dedup = []
    for t in subtasks:
        if t.lower() not in seen:
            seen.add(t.lower())
            dedup.append({"task": t})

    return dedup
