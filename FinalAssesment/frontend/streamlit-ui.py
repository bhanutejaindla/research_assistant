import streamlit as st
import tempfile
import time
import os

# === Import your agent modules ===
from agents.coordination_agent import coordination_agent
from agents.configuration_agent import configuration_agent
from agents.preprocessing_agent import preprocessing_agent
from agents.analysis_agent import analysis_agent
from agents.code_agent import code_agent
from agents.web_augmentation_agent import web_augmentation_agent
from agents.security_agent import security_agent
from agents.documentation_agent import documentation_agent
from agents.diagram_agent import diagram_agent
from agents.results_aggregation_agent import results_aggregation_agent

# =============================
# 🎨 Page Configuration
# =============================
st.set_page_config(page_title="Code Insight Chatbot", layout="wide")
st.title("🤖 Code-Aware Chatbot")

# =============================
# 📦 Sidebar: Project Input
# =============================
with st.sidebar:
    st.header("📁 Project Input")

    uploaded_zip = st.file_uploader("Upload ZIP file", type=["zip"])
    github_url = st.text_input("or paste GitHub repo URL:")

# =============================
# 🧠 Session State Initialization
# =============================
if "project_state" not in st.session_state:
    st.session_state.project_state = None

if "preprocessing_complete" not in st.session_state:
    st.session_state.preprocessing_complete = False

if "preprocessing_progress" not in st.session_state:
    st.session_state.preprocessing_progress = None

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "agent_log" not in st.session_state:
    st.session_state.agent_log = []

if "chat_paused" not in st.session_state:
    st.session_state.chat_paused = False


# =============================
# ⚙️ Real-time Preprocessing
# =============================
def run_preprocessing(state):
    state["agent_log"] = []
    coordination_agent(state)
    configuration_agent(state)

    code_dir = (
        state.get("unzipped_path")
        or state.get("repo_path")
        or "uploads/internet-banking-concept-micro"
    )

    file_list = []
    for root, _, files in os.walk(code_dir):
        for fname in files:
            file_list.append(os.path.join(root, fname))

    file_count = len(file_list)
    progress_bar = st.progress(0)
    status_text = st.empty()

    for idx, fname in enumerate(file_list):
        progress_bar.progress((idx + 1) / file_count)
        status_text.info(
            f"{idx+1}/{file_count} files found: {os.path.relpath(fname, code_dir)}"
        )
        time.sleep(0.02)  # simulate progress animation

    status_text.success("✅ All files discovered. Running pipeline...")

    # Call your actual agent pipeline
    preprocessing_agent(state)
    analysis_agent(state)

    # Add more agents as desired
    return state


# =============================
# 🚀 Pipeline Trigger
# =============================
if (uploaded_zip or github_url) and not st.session_state.preprocessing_complete:
    state = {}

    if uploaded_zip:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tf:
            tf.write(uploaded_zip.read())
            state["zip_path"] = tf.name
    elif github_url:
        state["github_url"] = github_url.strip()

    st.info("🧩 Preprocessing project files. Please wait...")
    state = run_preprocessing(state)

    print("Preprocessing started...")
    st.session_state.project_state = state
    st.session_state.preprocessing_complete = True
    st.session_state.agent_log = state.get("agent_log", [])
    time.sleep(0.5)

    st.success("Preprocessing complete! You can now chat with your codebase.")


# =============================
# 👀 Real-time Preprocessing Indicator
# =============================
if st.session_state.preprocessing_progress:
    st.info(st.session_state.preprocessing_progress)


# =============================
# 💬 Chatbot Interface
# =============================
if st.session_state.preprocessing_complete:
    st.subheader("💬 Ask the AI about your uploaded codebase!")

    if st.session_state.chat_paused:
        st.info("Processing your previous request. Please wait...")
    else:
        user_query = st.text_input("You:", key="user_query", value="", disabled=False)

        if user_query:
            st.session_state.chat_paused = True  # freeze input while processing
            st.experimental_rerun()

    if st.session_state.chat_paused and st.session_state.get("user_query"):
        query = st.session_state.user_query.lower()
        state = st.session_state.project_state.copy()
        agent_log = []

        # Determine which agent to trigger
        if "security" in query or "vulnerability" in query:
            security_agent(state)
            agent_log.append("security_agent")

        elif "diagram" in query or "architecture" in query:
            diagram_agent(state)
            agent_log.append("diagram_agent")

        elif any(k in query for k in ["document", "summary", "docstring"]):
            documentation_agent(state)
            agent_log.append("documentation_agent")

        elif "quality" in query or "code" in query:
            code_agent(state)
            agent_log.append("code_agent")

        elif any(k in query for k in ["web", "external", "package"]):
            web_augmentation_agent(state)
            agent_log.append("web_augmentation_agent")

        # Always aggregate results at the end
        results_aggregation_agent(state)
        agent_log.append("results_aggregation_agent")

        # Retrieve answer
        answer = state.get("result", "See pipeline log for details.")
        st.session_state.chat_history.append((st.session_state.user_query, answer))
        st.session_state.agent_log.append(f"Agents run: {agent_log}")

        # Reset state
        st.session_state.user_query = ""
        st.session_state.chat_paused = False
        st.experimental_rerun()

    # Show chat history
    for q, a in st.session_state.chat_history:
        st.markdown(f"**🧑 You:** {q}")
        st.markdown(f"**🤖 AI:** {a}")

    # Agent Log
    with st.expander("🧾 Show Pipeline Log"):
        st.write(st.session_state.agent_log)
else:
    st.info("⬆️ Upload a ZIP or enter a GitHub repo to start!")
