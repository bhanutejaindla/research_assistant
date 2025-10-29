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
            if source == "GitHub URL" and (not github_url or github_url.strip() == ""):
                st.error("Please provide a GitHub URL.")
                return

            if source == "ZIP upload" and zip_file is None:
                st.error("Please upload a ZIP file.")
                return

            # Preprocessing step
            try:
                if zip_file:
                    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
                    tf.write(zip_file.getvalue())
                    tf.flush()
                    tf.close()
                    zip_path = tf.name

                    # Call preprocessing agent
                    from agents.preprocessing_agent import preprocess_repository

                    repo_details = preprocess_repository(zip_path=zip_path)
                    st.session_state["preprocessed_files"] = repo_details.get("files", [])
                    st.session_state["repository_about"] = repo_details.get("about", "Unknown")
                    st.session_state["entry_point"] = repo_details.get("entry_point", "Unknown")

                    st.success("Preprocessing completed successfully.")

                    # Display preprocessing results
                    st.write("### Repository Details")
                    st.write(f"**About**: {st.session_state['repository_about']}")
                    st.write(f"**Entry Point**: {st.session_state['entry_point']}")

                    st.write("### Extracted Files")
                    for file in st.session_state["preprocessed_files"]:
                        st.write(f"- {file}")

                else:
                    st.error("Preprocessing requires a ZIP file.")

            except Exception as e:
                st.error(f"Error during preprocessing: {e}")

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

    st.subheader("Analysis Progress")
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

                st.write("**Activity Feed**")
                # Display the feed messages
                for item in feed[-20:]:
                    t = item.get("type", "info")
                    msg = item.get("message", "")
                    if t == "error":
                        st.error(msg)
                    elif t == "milestone":
                        st.success(msg)
                    else:
                        st.info(msg)

            # Display extracted files if the stage is completed
            if status.get("stage") == "Completed" and "extracted_files" in status:
                st.write("### Extracted Files")
                for file in status["extracted_files"]:
                    st.write(f"- {file}")

            if status.get("stage") in ("Completed", "Error") or int(percent) >= 100:
                st.success("Analysis finished" if status.get("stage") == "Completed" else "Analysis ended with error")
                break

        else:
            placeholder.error(f"Progress request failed: {r.status_code} {r.text}")
            break

        time.sleep(POLL_INTERVAL)


def upload_and_preprocess_ui():
    st.header("Upload and Preprocess Repository")

    # File upload section
    zip_file = st.file_uploader("Upload a ZIP file", type=["zip"], help="Upload a ZIP file containing the repository.")

    if st.button("Preprocess Files"):
        if zip_file is None:
            st.error("Please upload a ZIP file to preprocess.")
            return

        # Save the uploaded file to a temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as temp_file:
            temp_file.write(zip_file.getvalue())
            temp_file_path = temp_file.name

        # Call the preprocessing agent via the backend API
        try:
            files = {"zip_file": (zip_file.name, zip_file.getvalue())}
            response = requests.post(f"{BACKEND_URL}/preprocess", files=files, timeout=15)

            if response.status_code == 200:
                result = response.json()

                # Display preprocessing results
                st.write("### Preprocessing Results")
                st.write(f"**Extracted Files:**")
                for file in result.get("file_list", []):
                    st.write(f"- {file}")

                st.session_state["preprocessed_files"] = result.get("file_list", [])
                st.session_state["detailed_file_info"] = result.get("detailed_file_info", [])
                st.success("Preprocessing completed successfully.")
            else:
                st.error(f"Preprocessing failed: {response.status_code} {response.text}")

        except Exception as e:
            st.error(f"Error during preprocessing: {e}")


def query_ui():
    st.header("Query the Repository")

    if "preprocessed_files" not in st.session_state or not st.session_state["preprocessed_files"]:
        st.info("Please preprocess a repository first.")
        return

    # Display preprocessed files
    st.write("### Preprocessed Files")
    for file in st.session_state["preprocessed_files"]:
        st.write(f"- {file}")

    # Query input
    query = st.text_input("Enter your query about the repository:", help="Ask questions about the repository structure, files, or content.")

    if st.button("Submit Query"):
        if not query.strip():
            st.error("Please enter a query.")
            return

        # Call the backend API to handle the query
        try:
            response = requests.post(f"{BACKEND_URL}/query", json={"query": query}, timeout=15)

            if response.status_code == 200:
                result = response.json()
                st.write("### Query Results")
                st.write(result.get("answer", "No answer provided."))
            else:
                st.error(f"Query failed: {response.status_code} {response.text}")

        except Exception as e:
            st.error(f"Error during query: {e}")


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

    st.markdown("---")

    with left:
        upload_and_preprocess_ui()

    with right:
        query_ui()

if __name__ == "__main__":
    main()
