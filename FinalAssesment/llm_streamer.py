import os
import time
from openai import OpenAI
from state_manager import save_state

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def stream_llm(project_id: int, prompt: str, state: dict, role="analysis_agent", ui_callback=None):
    """
    Stream OpenAI output token-by-token with pause/resume support.
    Saves partial output and updates UI live.
    """
    print(f"🚀 Starting LLM stream for project {project_id} ({role})")
    print(f"🧠 Prompt:\n{prompt[:300]}...\n")

    partial_output = state.get("partial_output", "")
    state["current_role"] = role
    state["status"] = "running"
    save_state(project_id, state)

    # ✅ Support resume from partial output
    if partial_output:
        messages = [
            {"role": "system", "content": "You are a helpful repository assistant."},
            {"role": "user", "content": f"{prompt}\n\n(Continue from here: {partial_output[-200:]})"},
        ]
    else:
        messages = [
            {"role": "system", "content": "You are a helpful repository assistant."},
            {"role": "user", "content": prompt},
        ]

    try:
        with client.chat.completions.stream(
            model="gpt-4o-mini",
            messages=messages,
        ) as stream:
            for event in stream:
                # 🔍 Check if user paused mid-stream
                if state.get("is_paused"):
                    print("⏸️ Stream paused by user")
                    state["status"] = "paused"
                    save_state(project_id, state)
                    return partial_output

                # 🔹 Handle token updates
                if hasattr(event, "delta") and event.delta and "content" in event.delta:
                    token = event.delta["content"]
                    partial_output += token
                    state["partial_output"] = partial_output

                    # Print live to terminal (debug)
                    print(token, end="", flush=True)

                    # Update Streamlit UI
                    if ui_callback:
                        ui_callback(partial_output)

                    time.sleep(0.01)

            print("\n✅ Stream completed successfully.")
            state["status"] = "completed"

    except Exception as e:
        print(f"\n❌ Stream failed: {e}")
        state["status"] = "error"
        state["error"] = str(e)

    finally:
        save_state(project_id, state)
        print(f"💾 Final state saved for project {project_id} ({state['status']})")

    return partial_output
