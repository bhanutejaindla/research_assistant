import os
import json
import time
from openai import OpenAI
from state_manager import save_state, load_state  # ✅ ensure both exist

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def stream_llm(project_id: int, prompt: str, state: dict, role="analysis_agent", ui_callback=None):
    """
    Stream OpenAI output token-by-token with manual pause/resume support.
    Supports continuation from previously paused state.

    Args:
        project_id: Unique ID for the project.
        prompt: User prompt for LLM.
        state: Mutable dict holding 'partial_output', 'is_paused', etc.
        role: Role name for identification.
        ui_callback: Optional callable to update UI in real-time.
    """
    state_dir = "analysis_states"
    os.makedirs(state_dir, exist_ok=True)

    # ✅ Load previous state if any
    prev_state = load_state(project_id) or {}
    partial_output = prev_state.get("partial_output", state.get("partial_output", ""))
    is_paused = prev_state.get("is_paused", False)

    # ✅ Build message with continuation context
    if partial_output:
        messages = [
            {
                "role": "user",
                "content": f"{prompt}\n\n(Continue from here: {partial_output[-200:]})"
            }
        ]
    else:
        messages = [{"role": "user", "content": prompt}]

    # Update runtime info
    state["current_role"] = role
    state["prompt"] = prompt
    state["status"] = "running"

    try:
        with client.chat.completions.stream(
            model="gpt-4o-mini",
            messages=messages,
        ) as stream:
            for event in stream:
                # 🟡 Check for pause
                if state.get("is_paused"):
                    state["status"] = "paused"
                    state["partial_output"] = partial_output
                    save_state(project_id, state)
                    print(f"⏸️ Paused {role} stream at {len(partial_output)} chars")
                    return partial_output  # stop immediately

                # 🟢 Stream real-time tokens
                if hasattr(event, "delta") and event.delta.get("content"):
                    token = event.delta["content"]
                    partial_output += token
                    state["partial_output"] = partial_output

                    if ui_callback:
                        ui_callback(partial_output)
                    else:
                        print(token, end="", flush=True)

                    time.sleep(0.01)  # smoother updates

            # ✅ Completed successfully
            state["status"] = "completed"
            state["partial_output"] = ""
            print(f"\n✅ Stream completed for {role}")

    except Exception as e:
        state["status"] = "error"
        state["error"] = str(e)
        print(f"❌ Stream failed for {role}: {e}")

    finally:
        # Always save state
        save_state(project_id, state)
        print(f"💾 State saved for project {project_id} ({state['status']})")

    return partial_output
