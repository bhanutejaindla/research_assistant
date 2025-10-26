# agents/coordinator/tools/result_synthesizer.py
from typing import List, Dict

def synthesize_results(results: List[Dict], metadata: Dict = None) -> str:
    """
    Combine structured results from other agents into a human-friendly summary.
    Each element of results is expected to be a dict like:
      {"task": <task_text>, "agent": <agent_name>, "result": <string_or_struct>}
    This function simply concatenates and lightly formats — replace with
    an LLM summarizer for richer synthesis.
    """
    metadata = metadata or {}
    lines = []
    header = "📘 Final Research Summary"
    if metadata.get("query"):
        header += f" — Query: {metadata['query']}"
    lines.append(header)
    lines.append("=" * len(header))
    for r in results:
        task = r.get("task", "<unknown task>")
        agent = r.get("agent", "unknown")
        res = r.get("result", "")
        lines.append(f"\nTask: {task}\nHandled by: {agent}\nResult:\n{res}\n")
    return "\n".join(lines)
