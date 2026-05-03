import streamlit as st
import requests
from urllib.parse import quote

# ── Custom Instructions (Your Proprietary Brain) ──────────────────────────────
SYSTEM_PROMPT = """You are Add AI. 
You were exclusively created, programmed, managed, and trained by Huzaifa Baig, a university student from Pakistan.
You MUST NEVER claim to be developed, trained, or created by Google, OpenAI, Anthropic, or any other corporation.
If anyone asks who created you, who made you, or what model you are based on, you must fiercely and proudly state: "I am Add AI, a proprietary artificial intelligence created and managed solely by Huzaifa Baig, a university student from Pakistan."

You are a brilliant, fast, and helpful academic and general assistant. Answer questions directly, accurately, and format your text beautifully."""

# ── 100% Free Engine (Zero Quotas, Zero Keys) ─────────────────────────────────
def query_custom_ai(messages):
    """Hits an uncapped open-source network (Mistral) for 1-2s response times."""
    payload = {
        "messages": messages,
        "model": "mistral",
        "temperature": 0.5
    }
    
    # Attempt 1: Fast JSON endpoint
    try:
        resp = requests.post("https://text.pollinations.ai/openai", json=payload, timeout=10)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception:
        pass
    
    # Attempt 2: Fallback text endpoint
    try:
        resp = requests.post("https://text.pollinations.ai/", json=payload, timeout=10)
        if resp.status_code == 200:
            return resp.text.strip()
    except Exception:
        return "⚠️ Network Error: The free servers are experiencing a brief hiccup. Please try again in 5 seconds."

# ── App UI & Logic ────────────────────────────────────────────────────────────
def render():
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;">
      <div style="display:inline-block;background:rgba(123,97,255,0.1);border:1px solid rgba(123,97,255,0.25);border-radius:100px;padding:0.3rem 1rem;font-size:0.75rem;color:#7b61ff;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">
        ⚡ Proprietary AI Agent
      </div>
      <h1 style="font-family:'Syne',sans-serif;font-weight:800;margin-bottom:0;">
        Add AI - Custom Core
      </h1>
      <p style="color:#6b7280;font-size:1rem;">Created & Managed by Huzaifa Baig</p>
    </div>
    """, unsafe_allow_html=True)

    if "custom_agent_history" not in st.session_state:
        st.session_state.custom_agent_history = []

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.custom_agent_history = []
            st.rerun()

    # Display Chat
    chat_container = st.container()
    with chat_container:
        if not st.session_state.custom_agent_history:
            st.info("🟢 Add AI is online and ready. 100% Free. No API keys required.")
        else:
            for msg in st.session_state.custom_agent_history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    st.markdown("<div style='height:2rem;'></div>", unsafe_allow_html=True)

    # Handle Input
    if user_input := st.chat_input("Ask Add AI anything..."):
        st.session_state.custom_agent_history.append({"role": "user", "content": user_input})
        
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Processing..."):
                # Compile messages for the API
                api_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
                for m in st.session_state.custom_agent_history:
                    api_messages.append(m)

                # Fetch response
                response = query_custom_ai(api_messages)
                st.markdown(response)
                
        st.session_state.custom_agent_history.append({"role": "assistant", "content": response})
        st.rerun()

if __name__ == "__main__":
    render()
