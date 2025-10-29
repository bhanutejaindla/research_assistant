import os
import time
import requests
from openai import OpenAI
from dotenv import load_dotenv
import streamlit as st

load_dotenv()


def web_augmentation_agent(state: dict) -> dict:
    """
    Fetches web-based insights about dependencies or related tools,
    showing progress updates during augmentation.
    """

    state.setdefault("agent_log", [])
    api_key = state.get("config", {}).get("OPENAI_API_KEY") or os.getenv("OPENAI_API_KEY")

    if not api_key:
        st.warning("⚠️ Missing API key for web augmentation agent.")
        return state

    client = OpenAI(api_key=api_key)

    repo_path = state.get("repo_path") or state.get("unzipped_path") or "."
    deps = []

    # Gather dependencies
    for file in ("requirements.txt", "package.json"):
        dep_path = os.path.join(repo_path, file)
        if os.path.exists(dep_path):
            with open(dep_path, "r", encoding="utf-8") as f:
                deps.extend(f.readlines())

    if not deps:
        deps = ["fastapi", "react", "tailwindcss"]  # Fallback for demo

    total_deps = len(deps)
    st.info(f"🌐 Augmenting with {total_deps} dependencies...")
    progress_bar = st.progress(0)
    status_text = st.empty()

    summaries = []

    for i, dep in enumerate(deps, 1):
        dep_name = dep.strip()
        progress = int((i / total_deps) * 100)
        status_text.info(f"🔎 Fetching info for {dep_name} ({progress}%)")
        progress_bar.progress(progress / 100)

        try:
            prompt = (
                f"Provide a concise summary of the library '{dep_name}':\n"
                "1. What it is used for\n"
                "2. Latest version trend (approximate)\n"
                "3. Security or maintenance concerns\n"
                "4. Modern alternatives if outdated"
            )

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
            )

            result = response.choices[0].message.content.strip()
            summaries.append({dep_name: result})
            state["agent_log"].append(f"Web Augmentation Agent: ✅ Retrieved info for {dep_name}")

        except Exception as e:
            msg = f"⚠️ Failed to augment {dep_name}: {e}"
            st.warning(msg)
            state["agent_log"].append(msg)

        time.sleep(0.1)

    status_text.success("✅ Web augmentation complete.")
    progress_bar.progress(1.0)
    state["web_aug_results"] = summaries
    return state
