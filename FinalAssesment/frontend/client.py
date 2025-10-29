import streamlit as st
import requests
import time
import threading
import tempfile
import os
from typing import Optional

# Simple Streamlit client for the Research Assistant backend.
# Features:
# - Signup / Signin (in-memory session for demo)
# - Upload ZIP or provide GitHub URL
# - Start an analysis job (POST /real-time-analyze)
# - Poll job progress (GET /analyze/progress/{job_id})
# - Simple Chatbox that will attempt to call a job-scoped ask endpoint (POST /ask/{job_id}) if available

# Configuration
BACKEND_URL = "http://localhost:8080"  # Hardcoded to use port 8080
POLL_INTERVAL = 1.0  # seconds

# ---------------------------
# Helpers
# ---------------------------

def ensure_session_state():
    if "users" not in st.session_state:
        st.session_state["users"] = {}  # format: {email: {password: str, role: str}}
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = None
    if "job_id" not in st.session_state:
        st.session_state["job_id"] = None
    if "feed" not in st.session_state:
        st.session_state["feed"] = []
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []
    if "auth_token" not in st.session_state:
        st.session_state["auth_token"] = None  # Initialize auth_token to avoid KeyError


def signup(email: str, password: str, role: str) -> Optional[str]:
    # Attempt backend registration; fall back to local in-memory if backend is unavailable
    payload = {"email": email, "password": password, "role": role}
    try:
        resp = requests.post(f"{BACKEND_URL}/auth/register", json=payload, timeout=8)
        if resp.status_code in (200, 201):
            body = resp.json()
            # Expect backend to return user info {"username":..., "role":...}
            user = body.get("user") or body
            st.session_state["current_user"] = {"email": user.get("email", email), "role": user.get("role", role)}
            # Optionally persist token/session if backend provides one
            if "token" in body:
                st.session_state["auth_token"] = body["token"]
            return None
        else:
            return f"Registration failed: {resp.status_code} {resp.text}"
    except requests.exceptions.RequestException:
        # Fallback to in-memory simple signup for local demo
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
            user = body.get("user") or body
            st.session_state["current_user"] = {"email": user.get("email", email), "role": user.get("role", "User")}
            if "token" in body:
                st.session_state["auth_token"] = body["token"]
            return None
        else:
            return f"Login failed: {resp.status_code} {resp.text}"
    except requests.exceptions.RequestException:
        # Fallback to local in-memory signin for demo
        users = st.session_state["users"]
        user = users.get(email)
        if not user or user.get("password") != password:
            return "Invalid email or password (local)"
        st.session_state["current_user"] = {"email": email, "role": user.get("role")}
        return None


def signout():
    st.session_state["current_user"] = None
    st.session_state["job_id"] = None
    st.session_state["feed"] = []
    st.session_state["chat_history"] = []


# ---------------------------
# UI Pieces
# ---------------------------

def upload_and_start_ui():
    st.header("Start Repository Analysis")

    col1, col2 = st.columns([2, 1])
    with col1:
        source = st.radio("Repository source", ["GitHub URL", "ZIP upload"], index=0)

        github_url = None
        zip_file = None
        if source == "GitHub URL":
            github_url = st.text_input("GitHub repository URL (e.g. https://github.com/owner/repo)")
        else:
            zip_file = st.file_uploader("Upload a ZIP file", type=["zip"]) 

        personas = st.multiselect("Target personas", ["SDE", "PM"], default=["SDE"]) 
        depth = st.selectbox("Analysis depth", ["Quick", "Standard", "Deep"], index=1)
        web_aug = st.checkbox("Enable web augmentation (search docs)", value=True)

    # Option to run agents locally (import from agents/) instead of calling backend
    run_locally = st.checkbox("Run locally (use agents in this repo)", value=False)

    with col2:
        st.write("\n")
        st.write("\n")
        st.write("\n")
        if st.button("Start Analysis"):
            if not st.session_state["current_user"]:
                st.warning("Please sign in to start an analysis.")
                return

            if source == "GitHub URL" and (not github_url or github_url.strip() == ""):
                st.error("Please provide a GitHub URL.")
                return

            if source == "ZIP upload" and zip_file is None:
                st.error("Please upload a ZIP file.")
                return

            # Build form data
            files = {}
            data = {"analysis_depth": depth, "personas": ",".join(personas), "web_augmented": str(web_aug)}

            # If running locally, call agents directly; otherwise call backend
            if run_locally:
                # Save zip to temp file if provided
                zip_path = None
                if zip_file:
                    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
                    tf.write(zip_file.getvalue())
                    tf.flush()
                    tf.close()
                    zip_path = tf.name

                # Start a background thread that runs agents from the repo
                def local_runner():
                    try:
                        # Use the orchestrated workflow from agents.orchestration
                        from agents.orchestration.work_flow import run_full_pipeline
                        from agents.orchestration.state import get_initial_state

                        # Prepare initial state and inject inputs
                        state = get_initial_state()
                        state["zip_path"] = zip_path if zip_path else None
                        state["github_url"] = github_url
                        state["config"]["analysis_depth"] = depth
                        state["config"]["personas"] = personas
                        state["config"]["web_augmented"] = web_aug

                        # Run full orchestrated pipeline
                        result_state = run_full_pipeline(state)

                        # Update UI state
                        st.session_state["feed"] = result_state.get("agent_log", [])
                        st.session_state["local_final_output"] = result_state.get("final_results") or result_state.get("final_output") or result_state
                        st.session_state["job_id"] = f"local-{int(time.time())}"
                        st.success(f"Local analysis finished — job_id: {st.session_state['job_id']}")
                    except Exception as e:
                        # Ensure we capture errors in the feed
                        st.session_state.setdefault("feed", []).append(f"Local analysis failed: {e}")
                        st.error(f"Local analysis failed: {e}")

                thread = threading.Thread(target=local_runner, daemon=True)
                thread.start()

            else:
                try:
                    if github_url:
                        data["github_url"] = github_url.strip()
                        resp = requests.post(f"{BACKEND_URL}/real-time-analyze", data=data, timeout=10)
                    else:
                        # multipart upload with file
                        files = {"zip_file": (zip_file.name, zip_file.getvalue())}
                        resp = requests.post(f"{BACKEND_URL}/real-time-analyze", data=data, files=files, timeout=10)

                    if resp.status_code in (200, 201):
                        body = resp.json()
                        job_id = body.get("job_id")
                        st.session_state["job_id"] = job_id
                        st.success(f"Analysis started — job_id: {job_id}")
                        st.session_state["feed"] = []
                    else:
                        st.error(f"Failed to start analysis: {resp.status_code} {resp.text}")

                except Exception as e:
                    st.error(f"Error starting analysis: {e}")


def progress_ui():
    job_id = st.session_state.get("job_id")
    if not job_id:
        return

    st.subheader("Analysis progress")
    placeholder = st.empty()
    progress_bar = st.progress(0)

    # Poll for updates until job completes
    while True:
        try:
            r = requests.get(f"{BACKEND_URL}/analyze/progress/{job_id}", timeout=10)
        except Exception as e:
            placeholder.error(f"Could not contact backend for progress: {e}")
            break

        if r.status_code == 200:
            status = r.json()
            percent = status.get("percent", 0)
            stage = status.get("stage", "")
            feed = status.get("feed", [])
            current_file = status.get("current_file")

            progress_bar.progress(int(percent))

            with placeholder.container():
                st.write(f"**Stage**: {stage} — **{percent}%**")
                if current_file:
                    st.write(f"**Current file**: {current_file}")

                st.write("**Activity feed**")
                # display only last 20 feed messages
                for item in feed[-20:]:
                    t = item.get("type", "info")
                    msg = item.get("message", "")
                    if t == "error":
                        st.error(msg)
                    elif t == "milestone":
                        st.success(msg)
                    else:
                        st.info(msg)

            if status.get("stage") in ("Completed", "Error") or int(percent) >= 100:
                st.success("Analysis finished" if status.get("stage") == "Completed" else "Analysis ended with error")
                break

        else:
            placeholder.error(f"Progress request failed: {r.status_code} {r.text}")
            break

        time.sleep(POLL_INTERVAL)


# ---------------------------
# App layout
# ---------------------------

def main():
    st.set_page_config(page_title="Research Assistant — Client", layout="wide")
    ensure_session_state()

    st.title("Research Assistant — Repository Analysis")

    # Main columns: left for actions, right for progress
    left, right = st.columns([2, 3])

    with left:
        upload_and_start_ui()

    with right:
        progress_ui()

if __name__ == "__main__":
    main()
