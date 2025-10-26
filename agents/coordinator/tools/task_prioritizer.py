# agents/coordinator/tools/task_prioritizer.py
"""
LLM-powered Task Prioritizer
Uses OpenAI's reasoning to determine optimal execution order for subtasks.
Falls back to heuristic prioritization if API fails.
"""

import os
from typing import List
from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()  # This will automatically load OPENAI_API_KEY


# Initialize OpenAI client (expects OPENAI_API_KEY in env)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def prioritize_tasks(sub_tasks: List[str]) -> List[str]:
    """
    Uses OpenAI to reorder tasks in the most logical order.
    If the model fails, falls back to heuristic sorting.
    """
    if not sub_tasks:
        return []

    prompt = f"""
You are an expert research coordinator.
Given the following subtasks, reorder them in the sequence they should logically be executed 
to efficiently complete a research query.

Return the reordered list ONLY, one task per line, in order of priority (highest first).

Subtasks:
{chr(10).join(f"- {t}" for t in sub_tasks)}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert research planner."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )

        output = response.choices[0].message.content.strip()
        lines = [l.strip("-• ").strip() for l in output.splitlines() if l.strip()]
        # Filter lines that match something from original subtasks (avoid hallucinations)
        normalized = {t.lower(): t for t in sub_tasks}
        ordered = []
        for l in lines:
            key = l.lower()
            # match by substring (since model may slightly rephrase)
            match = next((t for t in sub_tasks if l.lower() in t.lower() or t.lower() in l.lower()), None)
            if match and match not in ordered:
                ordered.append(match)

        # Append any missing tasks that the LLM forgot
        for t in sub_tasks:
            if t not in ordered:
                ordered.append(t)

        return ordered

    except Exception as e:
        print(f"[WARN] LLM prioritization failed ({e}); falling back to heuristic ordering.")
        return _heuristic_prioritize(sub_tasks)


def _heuristic_prioritize(sub_tasks: List[str]) -> List[str]:
    """Fallback heuristic prioritization."""
    def score_task(t: str) -> int:
        tl = t.lower()
        if any(k in tl for k in ["find", "search", "retrieve", "collect", "gather", "scrape"]):
            return 0
        if any(k in tl for k in ["compare", "analyze", "trend", "pattern", "cause"]):
            return 1
        if any(k in tl for k in ["verify", "validate", "fact-check", "source"]):
            return 2
        return 3

    scored = [(score_task(t), t) for t in sub_tasks]
    scored.sort(key=lambda x: x[0])
    return [t for _, t in scored]
