import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def documentation_agent(state: dict) -> dict:
    """
    Generates developer-facing documentation based on outputs
    from the code, security, and web augmentation agents.
    """

    state.setdefault("agent_log", [])

    # Retrieve OpenAI API key from config or environment
    api_key = state.get("config", {}).get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY not found in state['config'] or environment variables."
        )

    client = OpenAI(api_key=api_key)

    # Extract agent results safely
    code_info = state.get("code_analysis_results", "No code analysis found.")
    sec_info = state.get("security_findings", "No security findings found.")
    web_info = state.get("web_aug_results", "No web augmentation results found.")

    # Merge results into a single input prompt
    merged = (
        f"Code summaries:\n{code_info}\n\n"
        f"Security findings:\n{sec_info}\n\n"
        f"Web insights and best practices:\n{web_info}"
    )

    prompt = (
        "You are a technical documentation generator.\n"
        "Given the following technical findings, code summaries, and security results, "
        "write a concise and professional documentation summary intended for developers.\n\n"
        f"{merged}"
    )

    try:
        # Generate documentation
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )

        doc_text = response.choices[0].message["content"]

        # Update state
        state["documentation"] = doc_text
        state["agent_log"].append("Documentation Agent: Generated developer documentation successfully.")

    except Exception as e:
        state["agent_log"].append(f"Documentation Agent: API call failed: {str(e)}")
        state["documentation"] = "Documentation generation failed."

    return state
