import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def diagram_agent(state: dict) -> dict:
    """
    Generates a textual system architecture diagram description using OpenAI.
    Expects 'OPENAI_API_KEY' in state["config"].
    """

    state.setdefault("agent_log", [])

    # Check if diagram generation is enabled
    if not state.get("config", {}).get("enable_diagram", True):
        state["agent_log"].append("Diagram Agent: Diagrams disabled by config.")
        return state

    # Retrieve API key from config or environment
    api_key = state.get("config", {}).get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        state["agent_log"].append("Diagram Agent: Missing API key in config or environment.")
        return state

    # Get latest generated documentation or fallback summary
    doc = state.get("documentation", "No documentation available.")

    # Construct the prompt
    prompt = (
        "Given this system summary, describe a high-level architecture diagram "
        "(main components, interactions, and data flow). "
        "The output should be descriptive and usable for diagramming tools.\n\n"
        f"Summary:\n{doc}"
    )

    try:
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )

        diagram_description = response.choices[0].message["content"]
        state["diagrams"] = diagram_description

        state["agent_log"].append("Diagram Agent: LLM described system diagram.")

    except Exception as e:
        state["agent_log"].append(f"Diagram Agent: API call failed: {str(e)}")
        state["diagrams"] = "Diagram generation failed."

    return state
