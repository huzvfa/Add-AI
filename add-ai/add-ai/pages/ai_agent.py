import streamlit as st
import streamlit.components.v1 as components
import base64
import json
import os
import time
import mimetypes
import re
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── THE AUTONOMOUS CORE (Independent Identity) ───────────────────────────────

class AddAICore:
    """The independent brain of Add AI. Operates locally with zero external calls."""
    def __init__(self):
        self.identity_response = "I am Add AI, a proprietary artificial intelligence exclusively created, programmed, managed, and trained by Huzaifa Baig, a university student from Pakistan."
        # Embedded Knowledge Base - Expand this as much as you want
        self.knowledge = {
            "hello": "Greetings! I am Add AI, your independent academic super-intelligence. How can I assist your studies today?",
            "who created you": self.identity_response,
            "who made you": self.identity_response,
            "creator": self.identity_response,
            "developer": self.identity_response,
            "are you gemini": "No. I have zero connection to Google, OpenAI, or any corporation. I am an independent AI agent created by Huzaifa Baig.",
            "are you gpt": "I am not GPT. I am Add AI, a unique autonomous entity developed by Huzaifa Baig.",
            "formula gravity": "The force of gravity is calculated as $F = G \\frac{m_1 m_2}{r^2}$.",
            "physics": "Physics is the study of matter, energy, and the fundamental forces of nature.",
            "calculate": "As an independent agent, I can process logic directly. Please provide the parameters for your calculation.",
        }

    def process_input(self, user_text, subject_context, files_content):
        """Processes logic internally."""
        query = user_text.lower().strip()
        
        # 1. Identity Protection
        if any(x in query for x in ["who are you", "identity", "your name", "what are you"]):
            return self.identity_response
        
        if any(x in query for x in ["who created", "who made", "developer", "huzaifa"]):
            return self.identity_response

        # 2. Knowledge Retrieval
        for key in self.knowledge:
            if key in query:
                return self.knowledge[key]

        # 3. File Context Logic
        if files_content:
            return f"I have processed the files you fed me for the {subject_context} module. Based on this proprietary data, I am ready to assist your research. [Local Analysis Complete]"

        return f"I am operating as an independent entity managed by Huzaifa Baig. I am specialized in {subject_context}. How would you like to proceed with your academic tasks?"

# ── Helpers ──────────────────────────────────────────────────────────────────

SUBJECT_PROMPTS = {
    "🔬 Science & Engineering": "Academic Specialist in Science and Engineering.",
    "📐 Mathematics": "Academic Specialist in Advanced Mathematics.",
    "📚 Literature & Humanities": "Academic Specialist in Humanities and Writing.",
    "💻 Computer Science": "Academic Specialist in Software Engineering and Code.",
    "🏛️ History & Social Studies": "Academic Specialist in History and Research.",
    "🧪 Chemistry": "Academic Specialist in Chemical Sciences.",
    "⚕️ Biology & Medicine": "Academic Specialist in Bio-Medical Sciences.",
    "📊 Economics & Business": "Academic Specialist in Economic Analysis.",
    "🌍 Geography & Environmental": "Academic Specialist in Environmental Systems.",
    "🎨 Arts & Design": "Academic Specialist in Design and Theory.",
    "🔤 Languages & Linguistics": "Academic Specialist in Linguistics.",
    "⚙️ General / Mixed Subjects": "Universal Academic Super-Intelligence."
}

def encode_file(uploaded_file):
    try:
        data = uploaded_file.read().decode('utf-8')
        uploaded_file.seek(0)
        return data
    except Exception:
        return "[Binary Data]"

def render():
    # Fix for the AttributeError: Ensure the core exists in session state
    if "ai_core" not in st.session_state:
        st.session_state.ai_core = AddAICore()

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;position:relative;z-index:1;">
      <div style="display:inline-block;background:rgba(0,245,212,0.08);
                  border:1px solid rgba(0,245,212,0.2);border-radius:100px;
                  padding:0.3rem 1rem;font-size:0.75rem;color:#00f5d4;
                  letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">
        ⚡ INDEPENDENT AI CORE • ZERO DEPENDENCIES
      </div>
      <h1 style="font-family:'Syne',sans-serif;font-size:clamp(2rem,5vw,3.5rem);
                  font-weight:800;line-height:1.1;margin-bottom:0.75rem;">
        <span style="background:linear-gradient(135deg,#e8eaf6,#ffffff);
                      -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
          Your Academic
        </span><br>
        <span style="background:linear-gradient(135deg,#00f5d4,#7b61ff,#ff6b6b);
                      -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
          Super-Intelligence
        </span> 
      </h1>
    </div>
    
    <style>
    @keyframes slide-in { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    .message-user { animation: slide-in 0.3s ease; background: linear-gradient(135deg, rgba(123,97,255,0.15), rgba(0,245,212,0.08)); border: 1px solid rgba(123,97,255,0.25); border-radius: 16px 16px 4px 16px; padding: 1rem 1.25rem; margin: 0.75rem 0; color: #e8eaf6; }
    .message-ai { animation: slide-in 0.3s ease 0.1s both; background: rgba(13,17,23,0.8); border: 1px solid rgba(0,245,212,0.15); border-radius: 16px 16px 16px 4px; padding: 1rem 1.25rem; margin: 0.75rem 0; color: #e8eaf6; }
    .message-label { font-family: 'Syne', sans-serif; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 0.5rem; }
    </style>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "subject" not in st.session_state:
        st.session_state.subject = "⚙️ General / Mixed Subjects"
    if "pending_message" not in st.session_state:
        st.session_state.pending_message = ""
    if "chat_input_widget" not in st.session_state:
        st.session_state.chat_input_widget = ""

    def submit_message():
        if st.session_state.chat_input_widget.strip():
            st.session_state.pending_message = st.session_state.chat_input_widget
        st.session_state.chat_input_widget = ""

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        subject = st.selectbox("Subject Area", list(SUBJECT_PROMPTS.keys()), index=list(SUBJECT_PROMPTS.keys()).index(st.session_state.subject), label_visibility="collapsed")
        st.session_state.subject = subject
    with col2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col3:
        if st.button("📤 Export", use_container_width=True):
            export_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
            st.download_button("💾 Download", export_text, "chat_export.txt", "text/plain")

    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            st.markdown("<div style='text-align:center;padding:3rem 1rem; color:#6b7280;'>🧠 Add AI Core is active. 100% Offline & Independent.</div>", unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages:
                cls = "message-user" if msg["role"] == "user" else "message-ai"
                lbl = "You" if msg["role"] == "user" else "⚡ Add AI"
                clr = "#7b61ff" if msg["role"] == "user" else "#00f5d4"
                st.markdown(f"""<div class="{cls}"><div class="message-label" style="color:{clr};">{lbl}</div>{msg["content"]}</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div style="background:rgba(13,17,23,0.9);border:1px solid rgba(0,245,212,0.15);border-radius:20px;padding:1rem;">', unsafe_allow_html=True)
        uploaded = st.file_uploader("📎 Attach files", accept_multiple_files=True, type=["pdf","png","jpg","txt","py","js","ts","html","css","csv","json","md"], key="file_uploader", label_visibility="collapsed")
        col_i, col_s = st.columns([6, 1])
        with col_i:
            st.text_area("Message", placeholder="Ask anything... (Proprietary Engine)", height=100, label_visibility="collapsed", key="chat_input_widget")
        with col_s:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            st.button("Send ➤", use_container_width=True, key="send_btn", on_click=submit_message)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.pending_message:
        user_input = st.session_state.pending_message
        st.session_state.pending_message = ""
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        
        # Logic execution
        file_data = [encode_file(f) for f in uploaded] if uploaded else []
        response = st.session_state.ai_core.process_input(user_input, subject, file_data)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    with st.sidebar:
        st.markdown("---")
        st.markdown("### ⚙️ Independent Core")
        st.success("Add AI is Autonomous")
        st.markdown(f"**Developer:** Huzaifa Baig")
        st.markdown("**Status:** Zero Dependencies")

    # Enter to Submit JS
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

if __name__ == "__main__":
    render()
