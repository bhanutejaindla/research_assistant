import streamlit as st
import requests
import time
from typing import Optional

# Simple Streamlit client for the Research Assistant backend.
# Features:
# - Signup / Signin (in-memory session for demo)
# - Upload ZIP or provide GitHub URL
# - Start an analysis job (POST /real-time-analyze)
# - Poll job progress (GET /analyze/progress/{job_id})
# - Simple Chatbox that will attempt to call a job-scoped ask endpoint (POST /ask/{job_id}) if available

# Configuration
BACKEND_URL = st.secrets.get("backend_url", "http://localhost:8000")
POLL_INTERVAL = 1.0  # seconds

# ---------------------------
# Helpers
# ---------------------------

def ensure_session_state():
    if "users" not in st.session_state:
        # format: {username: {password: str, role: str}}
        st.session_state["users"] = {}
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = None
    if "job_id" not in st.session_state:
        st.session_state["job_id"] = None
    if "feed" not in st.session_state:
        st.session_state["feed"] = []
    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []


def signup(username: str, password: str, role: str) -> Optional[str]:
    users = st.session_state["users"]
    if username in users:
        return "Username already exists"
    users[username] = {"password": password, "role": role}
    st.session_state["current_user"] = {"username": username, "role": role}
    return None


def signin(username: str, password: str) -> Optional[str]:
    users = st.session_state["users"]
    user = users.get(username)
    if not user or user.get("password") != password:
        return "Invalid username or password"
    st.session_state["current_user"] = {"username": username, "role": user.get("role")}
    return None


def signout():
    st.session_state["current_user"] = None
    st.session_state["job_id"] = None
    st.session_state["feed"] = []
    st.session_state["chat_history"] = []


# ---------------------------
# UI Pieces
# ---------------------------

def auth_ui():
    st.sidebar.header("Account")
    if st.session_state["current_user"]:
        st.sidebar.write(f"Signed in as **{st.session_state['current_user']['username']}** ({st.session_state['current_user']['role']})")
        if st.sidebar.button("Sign out"):
            signout()
            st.experimental_rerun()
        return

    tab = st.sidebar.radio("Auth", ["Sign in", "Sign up"]) 

    if tab == "Sign up":
        with st.sidebar.form("signup_form"):
            su_user = st.text_input("Username")
            su_pass = st.text_input("Password", type="password")
            su_role = st.selectbox("Role", ["User", "Admin"])
            submitted = st.form_submit_button("Create account")
            if submitted:
                err = signup(su_user.strip(), su_pass, su_role)
                if err:
                    st.sidebar.error(err)
                else:
                    st.sidebar.success("Account created and signed in")
                    st.experimental_rerun()

    else:
        with st.sidebar.form("signin_form"):
            si_user = st.text_input("Username")
            si_pass = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Sign in")
            if submitted:
                err = signin(si_user.strip(), si_pass)
                if err:
                    st.sidebar.error(err)
                else:
                    st.sidebar.success("Signed in")
                    st.experimental_rerun()


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


def chat_ui():
    st.subheader("Chat with the analysis")
    if not st.session_state.get("job_id"):
        st.info("Start an analysis first, or provide a job_id to chat against.")
        return

    job_id = st.session_state["job_id"]

    # Show chat history
    for msg in st.session_state["chat_history"]:
        if msg["from"] == "user":
            st.markdown(f"**You:** {msg['text']}")
        else:
            st.markdown(f"**Assistant:** {msg['text']}")

    # Input box
    prompt = st.text_input("Ask a question about the repository or analysis", key="prompt_input")
    if st.button("Send") and prompt:
        st.session_state["chat_history"].append({"from": "user", "text": prompt})

        # Try to call backend ask endpoint (job-scoped)
        try:
            resp = requests.post(f"{BACKEND_URL}/ask/{job_id}", json={"prompt": prompt}, timeout=30)
            if resp.status_code == 200:
                ans = resp.json().get("answer")
                st.session_state["chat_history"].append({"from": "assistant", "text": ans})
            else:
                st.session_state["chat_history"].append({"from": "assistant", "text": f"Backend did not accept prompt: {resp.status_code}."})
        except requests.exceptions.ConnectionError:
            st.session_state["chat_history"].append({"from": "assistant", "text": "Could not reach backend ask endpoint. Ensure server is running and provides /ask/{job_id} or use exported artifacts."})
        except Exception as e:
            st.session_state["chat_history"].append({"from": "assistant", "text": f"Error sending prompt: {e}"})

        # clear the input
        st.session_state["prompt_input"] = ""
        st.experimental_rerun()


# ---------------------------
# App layout
# ---------------------------

def main():
    st.set_page_config(page_title="Research Assistant — Client", layout="wide")
    ensure_session_state()

    st.title("Research Assistant — Client")
    auth_ui()

    if not st.session_state["current_user"]:
        st.info("Please sign in or sign up from the left sidebar to continue.")
        return

    # Main columns: left for actions, right for progress/chat
    left, right = st.columns([2, 3])

    with left:
        upload_and_start_ui()

    with right:
        progress_ui()
        st.markdown("---")
        chat_ui()


if __name__ == "__main__":
    main()
