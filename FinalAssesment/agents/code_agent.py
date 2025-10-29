import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def code_agent(state: dict) -> dict:
    """
    Analyzes Python code files using OpenAI for summary, API/class extraction,
    and improvement suggestions.
    Expects OPENAI_API_KEY in state["config"].
    """

    # Ensure logging list exists
    state.setdefault("agent_log", [])

    # Safely set API key from config or environment
    api_key = state.get("config", {}).get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        state["agent_log"].append("Code Agent: Missing API key in config or environment.")
        return state

    client = OpenAI(api_key=api_key)

    results = []

    for fpath in state.get("file_list", []):
        if fpath.endswith(".py"):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    code = f.read()

                # Build the LLM prompt
                prompt = (
                    "As a code expert, please:\n"
                    "1. Briefly summarize what this Python code does.\n"
                    "2. List major APIs, functions, or classes found.\n"
                    "3. Suggest one possible improvement.\n\n"
                    f"Code:\n{code[:3800]}"  # Limit to prevent token overflow
                )

                # Send to OpenAI model
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                )

                analysis = response.choices[0].message["content"]
                results.append({"file": fpath, "analysis": analysis})

                state["agent_log"].append(f"Code Agent: LLM-analyzed {fpath}.")
            except Exception as e:
                state["agent_log"].append(f"Code Agent: Error with {fpath}: {str(e)}")

    state["code_analysis_results"] = results
    return state
