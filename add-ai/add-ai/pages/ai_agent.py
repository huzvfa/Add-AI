import streamlit as st
import streamlit.components.v1 as components
import io
import re
import time
import requests
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

load_dotenv()

# ════════════════════════════════════════════════════════════════
#  IDENTITY & SYSTEM PROMPT
# ════════════════════════════════════════════════════════════════

APP_NAME    = "Add AI"
CREATOR     = "Huzaifa Baig"
ENGINE_NAME = "ADDCORE-OMEGA"

SYSTEM_PROMPT = f"""You are {APP_NAME}, a sovereign AI created by {CREATOR}, a university student from Pakistan.
Your identity is {APP_NAME}. You are NOT ChatGPT, OpenAI, Gemini, or Claude.
You are a highly intelligent, student-centric study helper.
If SOURCE MATERIAL is provided, prioritize it to answer the query accurately.
Provide brilliant, detailed, and directly helpful answers."""

# ════════════════════════════════════════════════════════════════
#  REAL-TIME FILE EXTRACTION
# ════════════════════════════════════════════════════════════════

def extract_text(uploaded_file) -> str:
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
#  THE INDESTRUCTIBLE 3-TIER ENGINE
# ════════════════════════════════════════════════════════════════

def call_add_ai_engine(user_query, file_data):
    """3-Tier Failover: Guarantees a response within seconds. Zero API Keys."""
    
    q_lower = user_query.lower()
    if any(x in q_lower for x in ["who are you", "who made you", "creator", "developer"]):
        return f"I am {APP_NAME}, a sovereign artificial intelligence built entirely by {CREATOR}."

    # Build optimized payload
    prompt = SYSTEM_PROMPT + "\n\n"
    if file_data:
        prompt += f"SOURCE MATERIAL:\n{file_data[:3000]}\n\n" # Capped to prevent payload blocking
    prompt += f"USER QUERY: {user_query}"

    # ── TIER 1: Lightning Fast Keyless Node (Pollinations) ──
    try:
        resp = requests.post(
            "https://text.pollinations.ai/",
            json={"messages": [{"role": "user", "content": prompt}], "model": "openai"},
            timeout=4
        )
        if resp.status_code == 200 and resp.text:
            return resp.text.strip()
    except Exception:
        pass

    # ── TIER 2: Secondary Keyless Node (Blackbox AI) ──
    try:
        resp = requests.post(
            "https://api.blackbox.ai/api/chat",
            json={"messages": [{"role": "user", "content": prompt}]},
            timeout=4
        )
        if resp.status_code == 200 and resp.text:
            text = resp.text.strip()
            text = re.sub(r'^\$@\$.*?\$@\$', '', text, flags=re.DOTALL) # Clean markdown artifacts
            if text: return text
    except Exception:
        pass

    # ── TIER 3: ZERO-FAIL LOCAL OFFLINE HEURISTICS ──
    # If the network completely dies, it analyzes the file locally using Python.
    if file_data:
        query_words = set(re.findall(r'\w+', q_lower)) - {"what","how","why","is","the","a","of","in","to","and"}
        if not query_words:
            return "I am currently in Offline Mode. I analyzed your file, but your query is too broad. Please be specific."
        
        sentences = re.split(r'(?<=[.!?]) +', file_data)
        best_sentence, max_overlap = "", 0
        
        for s in sentences:
            s_words = set(re.findall(r'\w+', s.lower()))
            overlap = len(query_words & s_words)
            if overlap > max_overlap:
                max_overlap, best_sentence = overlap, s
                
        if best_sentence:
            return f"**(Offline Extraction)** Based on your file: {best_sentence.strip()}"
        return "**(Offline Mode)** I read your file locally, but couldn't find an exact match for those terms."

    return "I am operating in strict offline mode right now. Please upload a file for me to analyze locally."

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
    .logo-anim { font-size: 4rem; animation: pulse 0.8s infinite ease-in-out; display: inline-block; }
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

    # ── MESSAGE PROCESSING (HIGH SPEED + ANIMATION) ──
    if st.session_state.pending_prompt:
        user_query = st.session_state.pending_prompt
        st.session_state.pending_prompt = ""
        st.session_state.chat_messages.append({"role": "user", "content": user_query})
        
        # Logo Animation UI
        anim_placeholder = st.empty()
        anim_placeholder.markdown(f"""
        <div style="text-align:center; padding: 2rem;">
            <div class="logo-anim">⚡</div>
            <div style="color: #00f5d4; font-family: 'Syne', sans-serif; font-weight: bold; margin-top: 1rem;">Add AI is thinking...</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Start Timer
        start_time = time.time()
        
        # Real-time Extraction
        file_data = "".join([extract_text(f) for f in uploaded_files]) if uploaded_files else ""
        
        # Execute 3-Tier Indestructible Engine
        response = call_add_ai_engine(user_query, file_data)
        
        # Ensure the logo rolls for at least ~1.5 to 2 seconds as requested, but NO MORE.
        elapsed = time.time() - start_time
        if elapsed < 1.5:
            time.sleep(1.5 - elapsed)
        
        anim_placeholder.empty() # Remove animation
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.rerun()

if __name__ == "__main__":
    render()
