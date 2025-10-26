# agents/coordinator/tools/query_decomposer.py
from typing import List
import re

def decompose_query(query: str) -> List[str]:
    """
    Decompose the user's query into smaller sub-tasks.
    This is a simple, rule-based decomposer that splits on punctuation
    and common conjunctions. Replace with an LLM-based decomposer for
    more advanced behavior.
    """
    if not query:
        return []

    # Normalize whitespace
    s = " ".join(query.split())

    # First try splitting on question marks / semicolons / newlines
    parts = re.split(r'[?;\n]+', s)
    subtasks = []
    for p in parts:
        # further split on 'and', 'or', commas that look like list separators
        subparts = re.split(r'\band\b|\bor\b|,', p, flags=re.IGNORECASE)
        for sp in subparts:
            candidate = sp.strip()
            if candidate:
                # avoid trivial tokens
                if len(candidate) > 3:
                    subtasks.append(candidate)
    # Deduplicate while preserving order
    seen = set()
    dedup = []
    for t in subtasks:
        if t.lower() not in seen:
            seen.add(t.lower())
            dedup.append(t)
    return dedup
