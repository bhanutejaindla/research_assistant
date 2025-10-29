import streamlit as st
import requests
import time
import tempfile
import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from agents.documentation_agent import documentation_agent
import io
from state_manager import save_state, load_state


# Import local agents
from agents.analysis_agent import analysis_agent
from agents.code_agent import code_agent
from agents.security_agent import security_agent
from agents.web_augmentation_agent import web_augmentation_agent
from agents.preprocessing_agent import preprocessing_agent
from state_manager import load_state,save_state

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
    """Wrapper to initialize or resume analysis."""
    project_id = 1  # ✅ use fixed or unique numeric ID (not the full state dict)

    saved_state = load_state(project_id)

    if saved_state:
        st.info("Resuming from saved state...")
        state = saved_state
    else:
        st.info("Starting new analysis...")
        state.setdefault("agents", [
            "preprocessing", "analysis_agent", "code_agent",
            "security_agent", "web_augmentation_agent", "documentation_agent"
        ])
        state.setdefault("current_agent_index", 0)
        state.setdefault("is_paused", False)
        state.setdefault("agent_log", [])
        state.setdefault("config", {"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")})
        save_state(project_id, state)

    # ✅ Run main loop
    return run_analysis(project_id, state)



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
def run_local_analysis(project_id):
    """Initializes state and starts/resumes analysis."""
    # Load existing state (if paused)
    state = load_state(project_id)

    # Initialize state if starting fresh
    if not state:
        state = {
            "project_id": project_id,
            "agents": ["preprocessing", "repo_intelligence", "doc_agent", "analysis_agent"],
            "current_agent_index": 0,
            "is_paused": False,
            "agent_log": [],
            "config": {"OPENAI_API_KEY": os.getenv("OPENAI_API_KEY")}
        }

    # Start / Resume analysis
    st.session_state.analysis_state = run_analysis(project_id, state)
    save_state(project_id, st.session_state.analysis_state)
    return st.session_state.analysis_state

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


def create_pdf_from_text(text: str) -> bytes:
    """Generate a PDF file in memory from plain text."""
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    text_object = c.beginText(50, height - 50)
    text_object.setFont("Helvetica", 11)
    for line in text.split("\n"):
        text_object.textLine(line)
    c.drawText(text_object)
    c.showPage()
    c.save()
    buffer.seek(0)
    return buffer.getvalue()
# ---------------------------
# Query UI
# ---------------------------

def query_ui():
    st.header("Ask the Repository Assistant or Generate Documentation")

    if not st.session_state.get("analysis_results"):
        st.info("Run an analysis first.")
        return

    tab1, tab2 = st.tabs(["💬 Ask Question", "📘 Generate Documentation"])

    # ---------------------------------------------------------------------
    # 🧠 Tab 1: General Query Mode (Ask the repository assistant anything)
    # ---------------------------------------------------------------------
    with tab1:
        query = st.text_input("Enter your question:")
        if st.button("Ask", key="ask_button"):
            results = st.session_state["analysis_results"]
            context = (
                f"Repository Overview:\n{results.get('analysis_overview', '')}\n\n"
                f"Code Insights:\n{results.get('code_analysis_results', '')}\n\n"
                f"Security Findings:\n{results.get('security_findings', '')}\n\n"
                f"Web Augmentation Insights:\n{results.get('web_aug_results', '')}\n\n"
            )
            prompt = context + f"\n\nUser asks: {query}\nProvide a clear, helpful answer."
            with st.spinner("Thinking..."):
                answer = query_llm(prompt)
            st.markdown("### 🧠 Assistant Answer")
            st.write(answer)

    # ---------------------------------------------------------------------
    # 📘 Tab 2: Documentation Generation (Role-specific)
    # ---------------------------------------------------------------------
    with tab2:
        st.markdown("Generate role-based documentation for the analyzed repository.")
        role = st.selectbox("Select your role", ["Product Manager (PM)", "Software Developer (SDE)"])

        if st.button("Generate Documentation", key="doc_button"):
            role_key = "PM" if "Product" in role else "SDE"
            state = st.session_state["analysis_results"]
            state["role"] = role_key

            with st.spinner(f"Generating documentation for {role_key}..."):
                state = documentation_agent(state)

            documentation = state.get("documentation", "⚠️ No documentation generated.")
            st.session_state["analysis_results"] = state

            # --- Display the output
            st.subheader(f"📄 {role} Documentation")
            st.markdown(documentation)

            # --- Download as Markdown
            st.download_button(
                label="⬇️ Download as Markdown",
                data=documentation,
                file_name=f"{role_key}_Documentation.md",
                mime="text/markdown"
            )

            # --- Download as PDF
            pdf_data = create_pdf_from_text(documentation)
            st.download_button(
                label="📄 Download as PDF",
                data=pdf_data,
                file_name=f"{role_key}_Documentation.pdf",
                mime="application/pdf"
            )
def summarize_progress_ui(state):
    """Use LLM to summarize current progress from logs."""
    logs = "\n".join(state.get("agent_log", []))
    if not logs:
        st.info("No logs yet.")
        return

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"Summarize the current analysis progress based on these logs:\n\n{logs}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a repository progress summarizer."},
            {"role": "user", "content": prompt},
        ]
    )
    st.markdown("### 🧾 Current Summary")
    st.write(response.choices[0].message.content)


def progress_ui():
    st.header("📊 Analysis Control Panel")
    project_id = st.session_state.get("project_id", 1)
    state = load_state(project_id)
    st.session_state["analysis_state"] = state

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("⏸️ Pause"):
            state["is_paused"] = True
            save_state(project_id, state)
            st.success("Analysis paused!")

    with col2:
        if st.button("▶️ Resume"):
            state["is_paused"] = False
            save_state(project_id, state)
            st.info("Resuming from last saved point...")
            run_analysis(project_id, state)

    with col3:
        if st.button("🧠 Summarize Current State"):
            summarize_progress_ui(state)

    # Log display
    st.subheader("🪵 Logs")
    for log in reversed(state.get("agent_log", [])):
        st.markdown(f"- {log}")

# ---------------------------
# Main Streamlit App Layout
# ---------------------------

def main():
    st.set_page_config(page_title="Repository Intelligence System", layout="wide")

    ensure_session_state()

    st.title("🧠 Repository Intelligence & Documentation System")

    menu = st.sidebar.radio(
        "Navigation",
        ["🏁 Start Analysis", "📊 Progress", "💬 Query / Documentation"],
        index=0
    )

    if menu == "🏁 Start Analysis":
        upload_and_start_ui()
    elif menu == "📊 Progress":
        progress_ui()
    elif menu == "💬 Query / Documentation":
        query_ui()


if __name__ == "__main__":
    main()

