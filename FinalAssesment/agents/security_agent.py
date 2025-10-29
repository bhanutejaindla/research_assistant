import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def security_agent(state: dict) -> dict:
    """
    Reviews Python files for potential security vulnerabilities using OpenAI.
    Expects 'OPENAI_API_KEY' in state["config"] or environment variables.
    """

    state.setdefault("agent_log", [])

    # Check if security review is enabled
    if not state.get("config", {}).get("enable_security", True):
        state["agent_log"].append("Security Agent: Skipped, setting disabled.")
        return state

    # Retrieve API key from config or environment
    api_key = state.get("config", {}).get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        state["agent_log"].append("Security Agent: Missing API key in config or environment.")
        return state

    client = OpenAI(api_key=api_key)

    results = []

    for fpath in state.get("file_list", []):
        if fpath.endswith(".py"):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    code = f.read()

                prompt = (
                    "Review the following Python code for common vulnerabilities, "
                    "OWASP Top 10 risks, and poor security practices. "
                    "List any issues found and provide a short explanation for each.\n\n"
                    f"Code:\n{code[:3800]}"  # Limit to prevent token overflow
                )

                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role": "user", "content": prompt}],
                )

                sec_result = response.choices[0].message["content"]
                results.append({"file": fpath, "security_review": sec_result})

                state["agent_log"].append(f"Security Agent: LLM scanned {fpath}.")
            except Exception as e:
                state["agent_log"].append(f"Security Agent: Error with {fpath}: {str(e)}")

    state["security_findings"] = results
    return state
