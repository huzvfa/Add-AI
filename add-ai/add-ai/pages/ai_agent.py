import streamlit as st
import streamlit.components.v1 as components
import io
import os
import time
from dotenv import load_dotenv

# ── Safe Library Imports ──
try:
    from pypdf import PdfReader
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

try:
    import docx as python_docx
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

try:
    from duckduckgo_search import DDGS
    HAS_DDGS = True
except ImportError:
    HAS_DDGS = False

load_dotenv()

# ════════════════════════════════════════════════════════════════
#  IDENTITY & SYSTEM PROMPT
# ════════════════════════════════════════════════════════════════

APP_NAME    = "Add AI"
CREATOR     = "Huzaifa Baig"
ENGINE_NAME = "ADDCORE-OMEGA"

SYSTEM_PROMPT = f"""You are {APP_NAME}, a highly advanced, sovereign artificial intelligence created exclusively by {CREATOR}, a university student from Pakistan.
Your identity is strictly {APP_NAME}. You are NOT ChatGPT, OpenAI, Google, Gemini, Claude, or any corporate model.
You are a general-purpose conversational AI, but your primary directive is being a brilliant, student-centric study helper.
If the user provides SOURCE MATERIAL, analyze it deeply and base your answers on it.
If no files are provided, act as a comprehensive, highly intelligent assistant on any topic.
Be concise, direct, and incredibly helpful."""

# ════════════════════════════════════════════════════════════════
#  FILE EXTRACTION (REAL-TIME)
# ════════════════════════════════════════════════════════════════

def extract_text(uploaded_file) -> str:
    """Extracts raw text from files in real-time."""
    name = uploaded_file.name
    ext  = name.rsplit(".", 1)[-1].lower()
    raw  = uploaded_file.read()
    uploaded_file.seek(0)
    result = ""

    try:
        if ext == "pdf" and HAS_PDF:
            reader = PdfReader(io.BytesIO(raw))
            result = "\n".join(p.extract_text() or "" for p in reader.pages)
        elif ext in ("docx", "doc") and HAS_DOCX:
            doc = python_docx.Document(io.BytesIO(raw))
            result = "\n".join(p.text for p in doc.paragraphs)
        elif ext in ("csv", "xlsx", "xls") and HAS_PANDAS:
            df = pd.read_csv(io.BytesIO(raw)) if ext == "csv" else pd.read_excel(io.BytesIO(raw))
            result = df.to_string()
        else:
            result = raw.decode("utf-8", errors="ignore")
    except Exception as e:
        result = f"[Error reading file: {str(e)}]"

    return f"\n--- FILE: {name} ---\n{result}\n"

# ════════════════════════════════════════════════════════════════
#  HIGH-SPEED KEYLESS ENGINE (DDGS PROXY)
# ════════════════════════════════════════════════════════════════

def call_add_ai_engine(user_query, chat_history, file_data):
    """Uses DuckDuckGo Search's hidden keyless AI chat for lightning-fast, ultra-smart responses."""
    if not HAS_DDGS:
        return "⚠️ CRITICAL ERROR: You must add 'duckduckgo-search>=6.1.7' to your requirements.txt file."

    # 1. LOCAL INSTANT INTERCEPT (0.01 seconds)
    q_lower = user_query.lower()
    identity_triggers = ["who are you", "who made you", "creator", "developer", "who created you"]
    if any(trigger in q_lower for trigger in identity_triggers):
        return f"I am {APP_NAME}, a sovereign artificial intelligence built entirely by {CREATOR}."

    # 2. BUILD THE CONTEXT PAYLOAD
    prompt = f"{SYSTEM_PROMPT}\n\n"
    
    # Safely inject up to 10,000 characters of file data (smart enough to handle assignments, small enough to be fast)
    if file_data:
        if len(file_data) > 10000:
            file_data = file_data[:10000] + "\n...[Content Truncated for Speed]..."
        prompt += f"USER UPLOADED SOURCE MATERIAL:\n{file_data}\n\n"
        
    # Inject last 2 messages for memory
    for m in chat_history[-2:]:
        prompt += f"{m['role'].upper()}: {m['content']}\n"
        
    prompt += f"USER: {user_query}\nASSISTANT:"

    # 3. EXECUTE HIGH-SPEED INFERENCE
    try:
        # Utilizing the keyless AI tunnel. 'claude-3-haiku' is utilized for sub-2-second speed.
        response = DDGS().chat(prompt, model='claude-3-haiku')
        return response
    except Exception as e:
        # Fallback to default model if haiku fails
        try:
            response = DDGS().chat(prompt)
            return response
        except Exception as e2:
            return "⚠️ The secure proxy is currently resetting. Please wait 3 seconds and hit Send again."

# ════════════════════════════════════════════════════════════════
#  STREAMLIT UI
# ════════════════════════════════════════════════════════════════

def render():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&display=swap');
    .msg-user { background: linear-gradient(135deg, rgba(123,97,255,0.1), rgba(0,245,212,0.05)); border: 1px solid rgba(123,97,255,0.2); border-radius: 16px 16px 4px 16px; padding: 1rem; margin: 0.5rem 0; }
    .msg-ai { background: rgba(13,17,23,0.8); border: 1px solid rgba(0,245,212,0.2); border-radius: 16px 16px 16px 4px; padding: 1rem; margin: 0.5rem 0; }
    .msg-label { font-family: 'Syne', sans-serif; font-size: 0.7rem; font-weight: 700; text-transform: uppercase; margin-bottom: 0.4rem; }
    @keyframes pulse { 0% { transform: scale(0.95); opacity: 0.7; } 50% { transform: scale(1.05); opacity: 1; } 100% { transform: scale(0.95); opacity: 0.7; } }
    .logo-anim { font-size: 4rem; animation: pulse 0.5s infinite ease-in-out; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="text-align:center;padding:1rem 0;">
      <div style="display:inline-block;background:rgba(0,245,212,0.1);border:1px solid rgba(0,245,212,0.3);border-radius:100px;padding:0.3rem 1rem;font-size:0.75rem;color:#00f5d4;font-weight:700;">⚡ {ENGINE_NAME} · By {CREATOR}</div>
      <h1 style="font-family:'Syne',sans-serif;font-size:2.5rem;font-weight:800;margin-top:0.5rem;">{APP_NAME}</h1>
      <p style="color:#6b7280;font-size:0.95rem;">General Intelligence & Study Assistant</p>
    </div>
    """, unsafe_allow_html=True)

    if "chat_messages" not in st.session_state: st.session_state.chat_messages = []
    if "pending_prompt" not in st.session_state: st.session_state.pending_prompt = ""
    if "chat_input_key" not in st.session_state: st.session_state.chat_input_key = 0

    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.chat_messages = []
            st.rerun()

    chat_container = st.container()
    with chat_container:
        if not st.session_state.chat_messages:
            st.markdown("<div style='text-align:center;padding:2rem;color:#6b7280;'>🧠 I am online. Upload study materials or ask me anything.</div>", unsafe_allow_html=True)
        else:
            for m in st.session_state.chat_messages:
                cls, lbl, clr = ("msg-user", "You", "#7b61ff") if m["role"] == "user" else ("msg-ai", f"⚡ {APP_NAME}", "#00f5d4")
                st.markdown(f'<div class="{cls}"><div class="msg-label" style="color:{clr};">{lbl}</div>{m["content"]}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("📎 Upload Study Materials (PDF, DOCX, CSV, TXT)", accept_multiple_files=True)
    
    def _submit():
        val = st.session_state.get(f"input_{st.session_state.chat_input_key}", "").strip()
        if val:
            st.session_state.pending_prompt = val
            st.session_state.chat_input_key += 1

    col_txt, col_btn = st.columns([6, 1])
    with col_txt:
        st.text_area("Message", placeholder="Ask a question, hit Enter to send...", key=f"input_{st.session_state.chat_input_key}", label_visibility="collapsed")
    with col_btn:
        st.button("Send ➤", key="send_button_main", use_container_width=True, on_click=_submit)

    # ── CUSTOM ENTER KEY SCRIPT ──
    components.html("""
    <script>
    const doc = window.parent.document;
    const textareas = doc.querySelectorAll('textarea');
    if(textareas.length > 0) {
        textareas[0].addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                const buttons = Array.from(doc.querySelectorAll('button'));
                const sendBtn = buttons.find(b => b.innerText.includes('Send ➤'));
                if (sendBtn) sendBtn.click();
            }
        });
    }
    </script>
    """, height=0, width=0)

    # ── MESSAGE PROCESSING (NO DELAYS) ──
    if st.session_state.pending_prompt:
        user_query = st.session_state.pending_prompt
        st.session_state.pending_prompt = ""
        st.session_state.chat_messages.append({"role": "user", "content": user_query})
        
        # Logo animation renders instantly
        anim_placeholder = st.empty()
        anim_placeholder.markdown(f"""
        <div style="text-align:center; padding: 2rem;">
            <div class="logo-anim">⚡</div>
            <div style="color: #00f5d4; font-family: 'Syne', sans-serif; font-weight: bold; margin-top: 1rem;">Fast Processing...</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Real-time extraction
        file_data = "".join([extract_text(f) for f in uploaded_files]) if uploaded_files else ""
        
        # Execute instantly through DDGS
        response = call_add_ai_engine(user_query, st.session_state.chat_messages[:-1], file_data)
        
        anim_placeholder.empty() # Remove animation immediately
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.rerun()

if __name__ == "__main__":
    render()
