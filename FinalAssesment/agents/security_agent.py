import os
import time
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st

load_dotenv()


def security_agent(state: dict) -> dict:
    """
    Scans Python code files for common security risks
    and updates progress live in Streamlit.
    """

    state.setdefault("agent_log", [])
    api_key = state.get("config", {}).get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        st.warning("⚠️ Missing API key for security agent.")
        return state

    client = OpenAI(api_key=api_key)

    file_list = [f for f in state.get("file_list", []) if f.endswith(".py")]
    total_files = len(file_list)

    if total_files == 0:
        st.info("No Python files found for security review.")
        return state

    st.info(f"🛡️ Running security review on {total_files} files...")
    progress_bar = st.progress(0)
    status_text = st.empty()

    results = []

    for i, fpath in enumerate(file_list, 1):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                code = f.read()

            progress = int((i / total_files) * 100)
            status_text.info(f"🔒 Checking {os.path.basename(fpath)} ({progress}%)")
            progress_bar.progress(progress / 100)

            prompt = (
                "Identify any security vulnerabilities or unsafe patterns "
                "in the following Python code. Include explanations and suggestions:\n\n"
                f"{code[:3500]}"
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )

            result = response.choices[0].message.content
            results.append({"file": fpath, "security_review": result})
            state["agent_log"].append(f"Security Agent: ✅ Scanned {fpath}")

        except Exception as e:
            msg = f"❌ Security Agent: Error scanning {fpath}: {str(e)}"
            st.warning(msg)
            state["agent_log"].append(msg)

        time.sleep(0.1)

    status_text.success("✅ Security analysis complete.")
    progress_bar.progress(1.0)
    state["security_findings"] = results
    return state
