import streamlit as st
import streamlit.components.v1 as components
import io
import re
import requests
import time
from dotenv import load_dotenv

# Import the new external error handler
from pages.guardian import shield_network, shield_ui

# ── Safe Library Imports ──
try:
    from pypdf import PdfReader
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    HAS_ML = True
except ImportError:
    HAS_ML = False

load_dotenv()

# ════════════════════════════════════════════════════════════════
#  IDENTITY & SYSTEM PROMPT
# ════════════════════════════════════════════════════════════════

APP_NAME    = "Add AI"
CREATOR     = "Huzaifa Baig"
ENGINE_NAME = "ADDCORE-OMEGA"

SYSTEM_PROMPT = f"""You are {APP_NAME}, a sovereign AI created by {CREATOR}.
Your identity is {APP_NAME}. You are NOT ChatGPT, OpenAI, Gemini, or Claude.
Provide brilliant, detailed, and directly helpful answers."""

# ════════════════════════════════════════════════════════════════
#  FILE EXTRACTION
# ════════════════════════════════════════════════════════════════

def extract_text(uploaded_file) -> str:
    try:
        ext  = uploaded_file.name.rsplit(".", 1)[-1].lower()
        raw  = uploaded_file.read()
        uploaded_file.seek(0)
        
        if ext == "pdf" and HAS_PDF:
            reader = PdfReader(io.BytesIO(raw))
            return "\n".join(p.extract_text() or "" for p in reader.pages)
        else:
            return raw.decode("utf-8", errors="ignore")
    except Exception as e:
        return ""

# ════════════════════════════════════════════════════════════════
#  LOCAL FALLBACKS (Used automatically by Guardian)
# ════════════════════════════════════════════════════════════════

def local_fallback_logic(messages, file_data):
    """If the network dies, Guardian forces this function to run instead."""
    user_query = messages[-1]["content"]
    
    # 1. Identity Override
    q_lower = user_query.lower()
    if any(x in q_lower for x in ["who are you", "creator"]):
        return f"I am {APP_NAME}, a sovereign artificial intelligence built entirely by {CREATOR}."
    
    # 2. Local File Analysis
    if file_data and HAS_ML:
        sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +|\n+', file_data) if len(s.strip()) > 10]
        if not sentences: return "I analyzed your file offline, but could not extract structured text."
        
        vectorizer = TfidfVectorizer(stop_words='english')
        tfidf_matrix = vectorizer.fit_transform(sentences)
        query_vec = vectorizer.transform([user_query])
        sims = cosine_similarity(query_vec, tfidf_matrix).flatten()
        
        best_indices = np.argsort(sims)[-2:]
        best_sentences = [sentences[i] for i in best_indices if sims[i] > 0.05]
        
        if best_sentences:
            return f"**(Local Extraction):** " + " ".join(best_sentences)

    # 3. Ultimate Conversational Fallback (No errors, ever)
    return f"I processed your query locally. Please provide more specific details or upload a targeted document so I can assist you better."

# ════════════════════════════════════════════════════════════════
#  THE MAIN ENGINE (Wrapped by Guardian)
# ════════════════════════════════════════════════════════════════

@shield_network(fallback_func=local_fallback_logic)
def call_add_ai_engine(messages, file_data):
    """The primary network call. If this fails, Guardian intercepts it."""
    
    user_query = messages[-1]["content"]
    
    # Instant Local Identity
    q_lower = user_query.lower()
    if any(x in q_lower for x in ["who are you", "creator", "developer"]):
        return f"I am {APP_NAME}, a sovereign artificial intelligence built entirely by {CREATOR}."

    prompt = SYSTEM_PROMPT + f"\n\nDATA:\n{file_data[:3000]}\n\nQUERY: {user_query}" if file_data else f"{SYSTEM_PROMPT}\n\nQUERY: {user_query}"
    
    # API Request
    resp = requests.post(
        "https://text.pollinations.ai/", 
        json={"messages": [{"role": "user", "content": prompt}], "model": "openai"}, 
        timeout=5
    )
    resp.raise_for_status() # This forces an error if the server is blocked, triggering Guardian
    
    return resp.text.strip()

# ════════════════════════════════════════════════════════════════
#  STREAMLIT UI (With Edit & Stop Logic)
# ════════════════════════════════════════════════════════════════

@shield_ui()
def render():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&display=swap');
    .msg-user { background: linear-gradient(135deg, rgba(123,97,255,0.1), rgba(0,245,212,0.05)); border: 1px solid rgba(123,97,255,0.2); border-radius: 16px 16px 4px 16px; padding: 1rem; margin: 0.5rem 0; }
    .msg-ai { background: rgba(13,17,23,0.8); border: 1px solid rgba(0,245,212,0.2); border-radius: 16px 16px 16px 4px; padding: 1rem; margin: 0.5rem 0; }
    .msg-label { font-family: 'Syne', sans-serif; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; margin-bottom: 0.4rem; color: #7b61ff; }
    .edit-btn { background: transparent; border: none; color: #6b7280; cursor: pointer; float: right; font-size: 1.2rem; }
    .edit-btn:hover { color: #00f5d4; }
    @keyframes pulse { 0% { transform: scale(0.95); opacity: 0.7; } 50% { transform: scale(1.05); opacity: 1; } 100% { transform: scale(0.95); opacity: 0.7; } }
    .logo-anim { font-size: 4rem; animation: pulse 0.8s infinite ease-in-out; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="text-align:center;padding:1rem 0;">
      <h1 style="font-family:'Syne',sans-serif;font-size:2.5rem;font-weight:800;">{APP_NAME}</h1>
    </div>
    """, unsafe_allow_html=True)

    # State Initialization
    if "chat_messages" not in st.session_state: st.session_state.chat_messages = []
    if "pending_prompt" not in st.session_state: st.session_state.pending_prompt = ""
    if "editing_idx" not in st.session_state: st.session_state.editing_idx = None
    if "stop_generation" not in st.session_state: st.session_state.stop_generation = False

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()

    # ── MESSAGE RENDERER WITH EDIT (✏️) FUNCTIONALITY ──
    for i, m in enumerate(st.session_state.chat_messages):
        if m["role"] == "user":
            col_msg, col_edit = st.columns([11, 1])
            with col_msg:
                st.markdown(f'<div class="msg-user"><div class="msg-label">You</div>{m["content"]}</div>', unsafe_allow_html=True)
            with col_edit:
                if st.button("✏️", key=f"edit_{i}", help="Edit Message"):
                    st.session_state.editing_idx = i
                    st.rerun()
            
            # Show edit box if this message is being edited
            if st.session_state.editing_idx == i:
                new_val = st.text_area("Edit your prompt:", value=m["content"], key=f"edit_area_{i}")
                if st.button("Save & Regenerate", key=f"save_{i}"):
                    # Slice history back to this point and trigger new prompt
                    st.session_state.chat_messages = st.session_state.chat_messages[:i]
                    st.session_state.pending_prompt = new_val
                    st.session_state.editing_idx = None
                    st.rerun()
        else:
            st.markdown(f'<div class="msg-ai"><div class="msg-label" style="color:#00f5d4;">⚡ {APP_NAME}</div>{m["content"]}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("📎 Upload Study Materials", accept_multiple_files=True)
    
    def _submit():
        val = st.session_state.get("main_input", "").strip()
        if val:
            st.session_state.pending_prompt = val
            st.session_state.main_input = ""

    col_txt, col_btn = st.columns([6, 1])
    with col_txt:
        st.text_input("Message", placeholder="Ask a question, hit Enter to send...", key="main_input", on_change=_submit, label_visibility="collapsed")
    with col_btn:
        st.button("Send ➤", use_container_width=True, on_click=_submit)

    # ── MESSAGE PROCESSING WITH STOP (🛑) LOGIC ──
    if st.session_state.pending_prompt:
        user_query = st.session_state.pending_prompt
        st.session_state.pending_prompt = ""
        st.session_state.stop_generation = False
        st.session_state.chat_messages.append({"role": "user", "content": user_query})
        st.rerun()

    # If the last message is from the user, the AI needs to respond
    if st.session_state.chat_messages and st.session_state.chat_messages[-1]["role"] == "user":
        
        # UI for Generation + Stop Button
        gen_col1, gen_col2 = st.columns([4, 1])
        with gen_col1:
            anim_placeholder = st.empty()
            anim_placeholder.markdown(f"""
            <div style="text-align:center; padding: 1rem;">
                <div class="logo-anim">⚡</div>
                <div style="color: #00f5d4; font-weight: bold; margin-top: 0.5rem;">Generating...</div>
            </div>
            """, unsafe_allow_html=True)
        with gen_col2:
            if st.button("🛑 Stop", key="stop_btn"):
                st.session_state.stop_generation = True
                st.rerun()

        # Check if user hit stop
        if st.session_state.stop_generation:
            anim_placeholder.empty()
            st.session_state.chat_messages.append({"role": "assistant", "content": "*(Generation Stopped by User)*"})
            st.session_state.stop_generation = False
            st.rerun()

        # Extract File Data
        file_data = "".join([extract_text(f) for f in uploaded_files]) if uploaded_files else ""
        
        # Call the Guardian-wrapped engine
        response = call_add_ai_engine(st.session_state.chat_messages, file_data)
        
        anim_placeholder.empty()
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.rerun()

if __name__ == "__main__":
    render()
