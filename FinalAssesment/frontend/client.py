import streamlit as st
import requests
import time
import threading
import tempfile
import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

# ---------------------------
# Setup
# ---------------------------

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Store key in .env safely

BACKEND_URL = "http://localhost:8080"  # Adjust if your FastAPI backend runs elsewhere
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
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def signup(email: str, password: str, role: str) -> Optional[str]:
    payload = {"email": email, "password": password, "role": role}
    try:
        resp = requests.post(f"{BACKEND_URL}/auth/register", json=payload, timeout=8)
        if resp.status_code in (200, 201):
            body = resp.json()
            st.session_state["current_user"] = {
                "email": body.get("email", email),
                "role": body.get("role", role),
            }
            if "token" in body:
                st.session_state["auth_token"] = body["token"]
            return None
        return f"Registration failed: {resp.status_code} {resp.text}"
    except requests.exceptions.RequestException:
        users = st.session_state["users"]
        if email in users:
            return "Email already exists (local)"
        users[email] = {"password": password, "role": role}
        st.session_state["current_user"] = {"email": email, "role": role}
        return None


def signin(email: str, password: str) -> Optional[str]:
    payload = {"email": email, "password": password}
    try:
        resp = requests.post(f"{BACKEND_URL}/auth/login", json=payload, timeout=8)
        if resp.status_code == 200:
            body = resp.json()
            st.session_state["current_user"] = {
                "email": body.get("email", email),
                "role": body.get("role", "User"),
            }
            if "token" in body:
                st.session_state["auth_token"] = body["token"]
            return None
        return f"Login failed: {resp.status_code} {resp.text}"
    except requests.exceptions.RequestException:
        users = st.session_state["users"]
        user = users.get(email)
        if not user or user.get("password") != password:
            return "Invalid email or password (local)"
        st.session_state["current_user"] = {"email": email, "role": "User"}
        return None


def signout():
    for key in ["current_user", "job_id", "feed", "chat_history"]:
        st.session_state[key] = None


# ---------------------------
# LLM Query (modern OpenAI syntax)
# ---------------------------

def query_llm(prompt: str) -> str:
    """Query OpenAI GPT-4 model with updated SDK syntax."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Or "gpt-4o" for best performance
            messages=[
                {"role": "system", "content": "You are an expert software repository analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.7,
            max_tokens=400,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error querying LLM: {e}"


# ---------------------------
# UI — Upload and Start
# ---------------------------

def upload_and_start_ui():
    st.header("Start Repository Analysis")

    col1, col2 = st.columns([2, 1])
    with col1:
        source = st.radio("Repository Source", ["GitHub URL", "ZIP upload"], index=0)

        github_url, zip_file = None, None
        if source == "GitHub URL":
            github_url = st.text_input("GitHub URL (e.g. https://github.com/user/repo)")
        else:
            zip_file = st.file_uploader("Upload ZIP file", type=["zip"])

        personas = st.multiselect("Target personas", ["SDE", "PM"], default=["SDE"])
        depth = st.selectbox("Analysis depth", ["Quick", "Standard", "Deep"], index=1)
        web_aug = st.checkbox("Enable web augmentation (search docs)", value=True)

    run_locally = st.checkbox("Run locally (use agents in repo)", value=False)

    with col2:
        st.write("\n" * 5)
        if st.button("Start Analysis"):
            if source == "GitHub URL" and not github_url:
                st.error("Please provide a GitHub URL.")
                return
            if source == "ZIP upload" and not zip_file:
                st.error("Please upload a ZIP file.")
                return

            try:
                if zip_file:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tf:
                        tf.write(zip_file.getvalue())
                        tf.flush()
                        zip_path = tf.name

                    # --- Local preprocessing ---
                    from agents.preprocessing_agent import preprocess_repository
                    repo_details = preprocess_repository(zip_path=zip_path)

                    st.session_state["preprocessed_files"] = repo_details.get("files", [])
                    st.session_state["repository_about"] = repo_details.get("about", "Unknown")
                    st.session_state["entry_point"] = repo_details.get("entry_point", "Unknown")

                    st.success("✅ Preprocessing completed successfully!")
                    st.write("**Repository Summary**")
                    st.write(f"- About: {st.session_state['repository_about']}")
                    st.write(f"- Entry Point: {st.session_state['entry_point']}")
                    st.write("### Files")
                    for f in st.session_state["preprocessed_files"]:
                        st.write(f"- {f}")
                else:
                    st.error("Please upload a ZIP file for preprocessing.")
            except Exception as e:
                st.error(f"Error during preprocessing: {e}")


# ---------------------------
# Progress UI (Polling Backend)
# ---------------------------

def progress_ui():
    job_id = st.session_state.get("job_id")
    if not job_id:
        return

    st.subheader("Analysis Progress")
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
            current_file = status.get("current_file")

            progress_bar.progress(int(percent))
            with placeholder.container():
                st.write(f"**Stage**: {stage} — {percent}%")
                if current_file:
                    st.write(f"**Current file:** {current_file}")
                st.write("**Activity Feed**")
                for item in feed[-15:]:
                    msg_type = item.get("type", "info")
                    msg = item.get("message", "")
                    if msg_type == "error":
                        st.error(msg)
                    elif msg_type == "milestone":
                        st.success(msg)
                    else:
                        st.info(msg)
            if status.get("stage") in ("Completed", "Error"):
                break
        else:
            placeholder.error(f"Progress error: {r.status_code}")
            break
        time.sleep(POLL_INTERVAL)


# ---------------------------
# Preprocessing UI
# ---------------------------

def upload_and_preprocess_ui():
    st.header("Upload Repository for Analysis")

    zip_file = st.file_uploader("Upload ZIP file", type=["zip"])
    if zip_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
            temp_file.write(zip_file.getvalue())
            temp_file_path = temp_file.name

        from agents.preprocessing_agent import preprocessing_agent

        try:
            state = {"zip_path": temp_file_path}
            state = preprocessing_agent(state)
            important_files = [
                f for f in state.get("file_list", [])
                if f.endswith((".py", ".yaml", ".json", "Dockerfile", "Makefile"))
            ]
            st.session_state["important_files"] = important_files
            st.write("### Important Files")
            for f in important_files:
                st.write(f"- {f}")
            st.success("Preprocessing done.")
        except Exception as e:
            st.error(f"Error: {e}")


# ---------------------------
# Query UI (Chat with LLM)
# ---------------------------

def query_ui():
    st.header("Ask the Repository Assistant")

    if not st.session_state.get("important_files"):
        st.info("Upload and preprocess a repository first.")
        return

    query = st.text_input("Enter your question:")
    if st.button("Ask"):
        if not query.strip():
            st.error("Please enter a valid query.")
            return

        files = ", ".join(st.session_state["important_files"][:20])
        refined_prompt = (
            f"The following are key files from a repository:\n{files}\n\n"
            f"User asks: {query}\n"
            "Provide a detailed and accurate response."
        )
        with st.spinner("Thinking..."):
            response = query_llm(refined_prompt)
        st.write("### Answer")
        st.write(response)


# ---------------------------
# Main App Layout
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

    with left:
        upload_and_preprocess_ui()
    with right:
        query_ui()


if __name__ == "__main__":
    main()
