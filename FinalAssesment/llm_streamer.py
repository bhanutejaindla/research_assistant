import os, json
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def stream_llm(project_id: int, prompt: str, state: dict, role="analysis_agent"):
    """
    Stream OpenAI output token-by-token with manual pause/resume support.
    Saves partial output to disk on pause.
    """
    state_dir = "analysis_states"
    os.makedirs(state_dir, exist_ok=True)
    state_path = os.path.join(state_dir, f"state_project_{project_id}.json")

    partial_output = state.get("partial_output", "")
    state["current_role"] = role

    from streamlit import session_state as st_session
    placeholder = st_session.get("placeholder", None)

    with client.chat.completions.stream(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
    ) as stream:
        for event in stream:
            # Check pause flag
            if state.get("is_paused"):
                with open(state_path, "w") as f:
                    json.dump(state, f, indent=2)
                print(f"⏸️ Paused during {role} stream at {len(partial_output)} chars")
                break

            if event.type == "message.delta" and event.delta.get("content"):
                token = event.delta["content"]
                partial_output += token
                state["partial_output"] = partial_output
                if placeholder:
                    placeholder.markdown(partial_output)

        else:
            # Stream finished naturally
            state["partial_output"] = partial_output
            with open(state_path, "w") as f:
                json.dump(state, f, indent=2)
            print(f"✅ Stream finished for {role}")

    return partial_output
