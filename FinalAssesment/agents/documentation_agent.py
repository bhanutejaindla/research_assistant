import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def documentation_agent(state: dict) -> dict:
    """
    Generates role-based documentation (PM or SDE) from analysis results.
    Uses existing agent outputs (analysis, code, security, etc.) as context.
    """

    role = state.get("role", "SDE")  # Default role = SDE
    api_key = state.get("config", {}).get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        state.setdefault("agent_log", []).append("❌ Documentation Agent: Missing API key.")
        return state

    client = OpenAI(api_key=api_key)

    # Collect all previously generated insights
    repo_overview = state.get("analysis_overview", "")
    code_analysis = state.get("code_analysis_results", "")
    security_findings = state.get("security_findings", "")
    web_aug = state.get("web_aug_results", "")

    # Choose prompt style based on role
    if role.upper() == "PM":
        role_prompt = (
            "You are a Product Manager creating documentation for stakeholders. "
            "Explain in clear business terms:\n"
            "- What this project does and why it exists.\n"
            "- The key features and their business value.\n"
            "- How the system supports users or product goals.\n"
            "- Summarize technical complexity only at a high level."
        )
    else:  # SDE
        role_prompt = (
            "You are a Senior Software Engineer writing internal technical documentation. "
            "Focus on how the system works:\n"
            "- Explain repository structure and modules.\n"
            "- Describe internal logic, dependencies, and APIs.\n"
            "- Include technical challenges and improvement ideas.\n"
            "- Keep it precise, structured, and developer-focused."
        )

    full_context = f"""
    Repository Overview:
    {repo_overview}

    Code Analysis:
    {code_analysis}

    Security Insights:
    {security_findings}

    Web Augmentation:
    {web_aug}
    """

    prompt = f"{role_prompt}\n\nHere is the analysis context:\n{full_context}\n\nNow generate documentation for the role: {role.upper()}."

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert technical documentation generator."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.6,
            max_tokens=800,
        )

        documentation = response.choices[0].message.content.strip()
        state["documentation"] = documentation
        state.setdefault("agent_log", []).append(f"📘 Documentation Agent: Generated {role.upper()} documentation.")
    except Exception as e:
        state.setdefault("agent_log", []).append(f"❌ Documentation Agent failed: {str(e)}")
        state["documentation"] = f"Error: {e}"

    return state
