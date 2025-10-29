import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def web_augmentation_agent(state: dict) -> dict:
    """
    Enhances the state with the latest web-related best practices
    using the OpenAI API. Expects 'OPENAI_API_KEY' in state["config"].
    """

    state.setdefault("agent_log", [])

    # Check if web augmentation is enabled
    if not state.get("config", {}).get("web_augmented", True):
        state["agent_log"].append("Web Augmentation Agent: Disabled by config.")
        return state

    # Retrieve API key from config or environment
    api_key = state.get("config", {}).get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        state["agent_log"].append("Web Augmentation Agent: Missing API key in config or environment.")
        return state

    # Define the prompt for latest web best practices
    prompt = (
        "Summarize the latest best practices for:\n"
        "1. FastAPI async endpoint design.\n"
        "2. Securing Python web applications (OWASP Top 10 compliance).\n"
        "3. React 18 migration and performance optimization.\n"
    )

    try:
        client = OpenAI(api_key=api_key)

        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
        )

        best_practices = response.choices[0].message["content"]
        state["web_aug_results"] = best_practices

        state["agent_log"].append("Web Augmentation Agent: LLM summarized best practices successfully.")

    except Exception as e:
        state["agent_log"].append(f"Web Augmentation Agent: API call failed: {str(e)}")
        state["web_aug_results"] = "Web best practices generation failed."

    return state

