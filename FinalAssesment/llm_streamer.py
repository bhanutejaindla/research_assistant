import os
import json
import time
from openai import OpenAI
from state_manager import save_state
import streamlit as st

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def stream_llm(project_id: int, prompt: str, state: dict, role="analysis_agent", ui_callback=None):
    """
    Stream OpenAI output token-by-token with manual pause/resume support.
    """
    state_dir = "analysis_states"
    os.makedirs(state_dir, exist_ok=True)

    partial_output = state.get("partial_output", "")
    state.update({
        "current_role": role,
        "prompt": prompt,
        "status": "running"
    })

    try:
        with client.chat.completions.stream(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        ) as stream:

            for event in stream:
                if state.get("is_paused"):
                    state["status"] = "paused"
                    save_state(project_id, state)
                    st.warning("⏸️ Stream paused.")
                    return partial_output

                if hasattr(event, "delta") and event.delta.get("content"):
                    token = event.delta["content"]
                    partial_output += token
                    state["partial_output"] = partial_output

                    # ✅ Update Streamlit UI instantly
                    if ui_callback:
                        ui_callback(partial_output)
                        st.experimental_rerun()  # 🔥 force live update

                    time.sleep(0.02)

            state["status"] = "completed"

    except Exception as e:
        state["status"] = "error"
        state["error"] = str(e)
        st.error(f"❌ Stream failed: {e}")

    finally:
        state["partial_output"] = partial_output
        save_state(project_id, state)

    return partial_output
