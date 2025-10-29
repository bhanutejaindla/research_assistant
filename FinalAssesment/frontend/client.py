import streamlit as st
import requests
import time
import tempfile
import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

# Import local agents
from agents.analysis_agent import analysis_agent
from agents.code_agent import code_agent
from agents.security_agent import security_agent
from agents.web_augmentation_agent import web_augmentation_agent
from agents.preprocessing_agent import preprocessing_agent

# ---------------------------
# Setup
# ---------------------------
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
BACKEND_URL = "http://localhost:8080"
POLL_INTERVAL = 1.0  # seconds


# ---------------------------
# Session Helpers
# ---------------------------

def ensure_session_state():
    defaults = {
        "users": {},
        "current_user": None,
        "job_id": None,
        "feed": [],
        "chat_history": [],
        "auth_token": None,
        "important_files": [],
        "detailed_file_info": [],
        "preprocessed_files": [],
        "analysis_results": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


# ---------------------------
# LLM Query
# ---------------------------

def query_llm(prompt: str) -> str:
    """Query OpenAI GPT model."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are an expert repository analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error querying LLM: {e}"


# ---------------------------
# Local Analysis Pipeline
# ---------------------------

def run_local_analysis(state):
    """Run the 4 agents locally and simulate live progress updates."""
    st.subheader("🔍 Real-Time Local Analysis Progress")

    steps = [
        ("Preprocessing", preprocessing_agent),
        ("Analysis Agent", analysis_agent),
        ("Code Agent", code_agent),
        ("Security Agent", security_agent),
        ("Web Augmentation Agent", web_augmentation_agent),
    ]

    progress = st.progress(0)
    feed_box = st.empty()
    total_steps = len(steps)

    state["feed"] = []
    for i, (label, func) in enumerate(steps, 1):
        try:
            feed_box.info(f"🚀 Running {label} ...")
            time.sleep(0.5)
            state = func(state)
            state["feed"].append({"type": "milestone", "message": f"{label} complete ✅"})
        except Exception as e:
            state["feed"].append({"type": "error", "message": f"{label} failed: {e}"})
            st.error(f"{label} failed: {e}")
            break

        progress.progress(i / total_steps)
        with feed_box.container():
            st.write("### Activity Feed")
            for f in state["feed"][-10:]:
                if f["type"] == "error":
                    st.error(f["message"])
                elif f["type"] == "milestone":
                    st.success(f["message"])
                else:
                    st.info(f["message"])
        time.sleep(1)

    st.success("🎉 All agents finished successfully!")
    return state


# ---------------------------
# Upload & Start UI
# ---------------------------

def upload_and_start_ui():
    st.header("Start Repository Analysis")

    col1, col2 = st.columns([2, 1])
    with col1:
        source = st.radio("Repository Source", ["GitHub URL", "ZIP upload"], index=1)
        zip_file = None
        github_url = None
        if source == "GitHub URL":
            github_url = st.text_input("GitHub URL")
        else:
            zip_file = st.file_uploader("Upload ZIP file", type=["zip"])

        web_aug = st.checkbox("Enable web augmentation", value=True)
        run_locally = st.checkbox("Run locally (skip backend)", value=True)

    with col2:
        st.write("\n" * 5)
        if st.button("🚀 Start Analysis"):
            if not zip_file and source == "ZIP upload":
                st.error("Please upload a ZIP file.")
                return

            # Save zip temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmp:
                tmp.write(zip_file.getvalue())
                tmp.flush()
                zip_path = tmp.name

            # Prepare shared state
            state = {"zip_path": zip_path, "web_augmentation": web_aug}

            if run_locally:
                st.info("Running locally using agents...")
                final_state = run_local_analysis(state)
                st.session_state["analysis_results"] = final_state

                st.subheader("🧾 Final Summary")
                combined_prompt = (
                    f"Repository Overview:\n{final_state.get('analysis_overview', '')}\n\n"
                    f"Code Analysis:\n{final_state.get('code_analysis_results', '')}\n\n"
                    f"Security Findings:\n{final_state.get('security_findings', '')}\n\n"
                    f"Web Insights:\n{final_state.get('web_aug_results', '')}\n\n"
                    "Create a concise, clear summary of key insights."
                )
                summary = query_llm(combined_prompt)
                st.write(summary)

            else:
                st.info("Sending to backend for analysis...")
                try:
                    files = {"file": ("repo.zip", zip_file.getvalue(), "application/zip")}
                    resp = requests.post(f"{BACKEND_URL}/analyze", files=files, timeout=30)
                    if resp.status_code == 200:
                        st.success("Backend analysis started!")
                        job_id = resp.json().get("job_id")
                        st.session_state["job_id"] = job_id
                    else:
                        st.error(f"Backend error: {resp.status_code}")
                except Exception as e:
                    st.error(f"Error contacting backend: {e}")


# ---------------------------
# Progress UI (Backend Polling)
# ---------------------------

def progress_ui():
    job_id = st.session_state.get("job_id")
    if not job_id:
        return

    st.subheader("Backend Analysis Progress")
    placeholder = st.empty()
    progress_bar = st.progress(0)

    while True:
        try:
            r = requests.get(f"{BACKEND_URL}/analyze/progress/{job_id}", timeout=10)
        except Exception as e:
            placeholder.error(f"Could not contact backend: {e}")
            break

        if r.status_code == 200:
            status = r.json()
            percent = status.get("percent", 0)
            stage = status.get("stage", "")
            feed = status.get("feed", [])

            progress_bar.progress(int(percent))
            with placeholder.container():
                st.write(f"**Stage**: {stage} — {percent}%")
                st.write("**Activity Feed**")
                for item in feed[-10:]:
                    msg_type = item.get("type", "info")
                    msg = item.get("message", "")
                    if msg_type == "error":
                        st.error(msg)
                    elif msg_type == "milestone":
                        st.success(msg)
                    else:
                        st.info(msg)
            if stage in ("Completed", "Error"):
                break
        else:
            placeholder.error(f"Progress error: {r.status_code}")
            break
        time.sleep(POLL_INTERVAL)


# ---------------------------
# Query UI
# ---------------------------

def query_ui():
    st.header("Ask the Repository Assistant")

    if not st.session_state.get("analysis_results"):
        st.info("Run an analysis first.")
        return

    query = st.text_input("Enter your question:")
    if st.button("Ask"):
        results = st.session_state["analysis_results"]
        context = (
            f"Repo overview:\n{results.get('analysis_overview', '')}\n"
            f"Code insights:\n{results.get('code_analysis_results', '')}\n"
            f"Security issues:\n{results.get('security_findings', '')}\n"
            f"Web aug info:\n{results.get('web_aug_results', '')}\n"
        )
        prompt = context + f"\n\nUser asks: {query}\nProvide a clear, helpful answer."
        with st.spinner("Thinking..."):
            answer = query_llm(prompt)
        st.write(answer)


# ---------------------------
# Main App
# ---------------------------

def main():
    st.set_page_config(page_title="Repository Research Assistant", layout="wide")
    ensure_session_state()

    st.title("🧠 Repository Research Assistant")

    left, right = st.columns([2, 3])
    with left:
        upload_and_start_ui()
    with right:
        progress_ui()

    st.divider()
    query_ui()


if __name__ == "__main__":
    main()
