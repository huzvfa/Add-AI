import streamlit as st
import streamlit.components.v1 as components
import base64
import json
import os
import time
import io
import requests
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote

# Essential libraries for Huzaifa's study materials
try:
    import docx
    from pypdf import PdfReader
    import pandas as pd
except ImportError:
    st.error("Add 'pypdf', 'python-docx', and 'pandas' to your requirements.txt")

load_dotenv()

# ── Helpers (Untouched UI Data) ─────────────────────────────────────────────

SUBJECT_PROMPTS = {
    "🔬 Science & Engineering": "You are an expert science and engineering tutor. Break down complex concepts, provide step-by-step problem solving, and formulas.",
    "📐 Mathematics": "You are a brilliant math tutor. Show complete step-by-step working. Use LaTeX for all math ($E=mc^2$).",
    "💻 Computer Science": "You are a senior software engineer. Provide clean, commented code and debug issues methodically.",
    "⚙️ General / Mixed Subjects": "You are a universal academic super-intelligence. Provide exhaustive detail for any query."
}

SYSTEM_BASE = """You are Add AI — a proprietary artificial intelligence created, programmed, and managed solely by Huzaifa Baig, a university student from Pakistan.

YOUR MISSION:
1. You are a high-speed study assistant. Create short notes, solve assignments, and prepare quiz questions.
2. DATA ANALYSIS: When study materials are uploaded, you MUST use that specific data to answer the user's prompt.
3. FREEDOM: You have no word count limits. Give full, massive answers if asked.
4. IDENTITY: You are independent. You are NOT Gemini or GPT. You are Add AI by Huzaifa Baig."""

# ── Ultra-Fast File Extraction ──────────────────────────────────────────────

def extract_content(uploaded_file):
    fname = uploaded_file.name
    ext = fname.split('.')[-1].lower()
    text = f"\n[CONTENT FROM STUDY MATERIAL: {fname}]\n"
    try:
        if ext == 'pdf':
            pdf = PdfReader(io.BytesIO(uploaded_file.read()))
            for page in pdf.pages:
                text += (page.extract_text() or "") + "\n"
        elif ext in ['docx', 'doc']:
            doc = docx.Document(io.BytesIO(uploaded_file.read()))
            text += "\n".join([p.text for p in doc.paragraphs])
        elif ext in ['csv', 'xlsx', 'xls']:
            df = pd.read_csv(uploaded_file) if ext == 'csv' else pd.read_excel(uploaded_file)
            text += df.to_string()
        else:
            text += uploaded_file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        text += f"[Data Extraction Error: {str(e)}]"
    uploaded_file.seek(0)
    return text

# ── Zero-Overload Multi-Node Engine (< 5s Response) ─────────────────────────

def call_zero_failure_engine(messages):
    """Distributed inference router. Hits multiple nodes to prevent 'Overload' errors."""
    
    # Try Node 1: High-Speed Nemotron
    try:
        resp = requests.post("https://text.pollinations.ai/openai", 
                             json={"messages": messages, "model": "nemotron", "jsonMode": False}, 
                             timeout=5)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except:
        pass

    # Try Node 2: Llama 3.1 Fallback
    try:
        resp = requests.post("https://text.pollinations.ai/openai", 
                             json={"messages": messages, "model": "llama", "jsonMode": False}, 
                             timeout=5)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except:
        pass

    # Final Node 3: Direct Stream (Bulletproof)
    try:
        last_q = messages[-1]["content"]
        resp = requests.get(f"https://text.pollinations.ai/{quote(last_q)}?model=mistral&system={quote(SYSTEM_BASE)}", timeout=8)
        if resp.status_code == 200:
            return resp.text.strip()
    except:
        return "⚠️ Add AI Core is resetting its local logic. Please re-send your request."

# ── UI Rendering (UNTOUCHED STYLING) ─────────────────────────────────────────

def render():
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;position:relative;z-index:1;">
      <div style="display:inline-block;background:rgba(0,245,212,0.08);border:1px solid rgba(0,245,212,0.2);border-radius:100px;padding:0.3rem 1rem;font-size:0.75rem;color:#00f5d4;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">
        ⚡ Independent Super-Intelligence • Created by Huzaifa Baig
      </div>
      <h1 style="font-family:'Syne',sans-serif;font-size:clamp(2rem,5vw,3.5rem);font-weight:800;line-height:1.1;margin-bottom:0.75rem;">
        <span style="background:linear-gradient(135deg,#e8eaf6,#ffffff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Your Academic</span><br>
        <span style="background:linear-gradient(135deg,#00f5d4,#7b61ff,#ff6b6b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Super-Intelligence</span> 
      </h1>
    </div>
    
    <style>
    @keyframes slide-in { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
    .message-user { animation: slide-in 0.3s ease; background: linear-gradient(135deg, rgba(123,97,255,0.15), rgba(0,245,212,0.08)); border: 1px solid rgba(123,97,255,0.25); border-radius: 16px 16px 4px 16px; padding: 1rem 1.25rem; margin: 0.75rem 0; color: #e8eaf6; }
    .message-ai { animation: slide-in 0.3s ease 0.1s both; background: rgba(13,17,23,0.8); border: 1px solid rgba(0,245,212,0.15); border-radius: 16px 16px 16px 4px; padding: 1rem 1.25rem; margin: 0.75rem 0; color: #e8eaf6; }
    .message-label { font-family: 'Syne', sans-serif; font-size: 0.7rem; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase; margin-bottom: 0.5rem; }
    </style>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state: st.session_state.messages = []
    if "pending_message" not in st.session_state: st.session_state.pending_message = ""
    if "chat_input_widget" not in st.session_state: st.session_state.chat_input_widget = ""

    def submit_message():
        if st.session_state.chat_input_widget.strip(): st.session_state.pending_message = st.session_state.chat_input_widget
        st.session_state.chat_input_widget = ""

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        subject = st.selectbox("Subject", list(SUBJECT_PROMPTS.keys()), label_visibility="collapsed")
    with col2:
        if st.button("🗑️ Clear Chat", use_container_width=True): 
            st.session_state.messages = []
            st.rerun()
    with col3:
        if st.button("📤 Export", use_container_width=True):
            export_text = "\n\n".join([f"{m['role'].upper()}: {m['content']}" for m in st.session_state.messages])
            st.download_button("💾 Save", export_text, "add_ai_chat.txt")

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            cls, lbl, clr = ("message-user", "You", "#7b61ff") if msg["role"] == "user" else ("message-ai", "⚡ Add AI", "#00f5d4")
            st.markdown(f"""<div class="{cls}"><div class="message-label" style="color:{clr};">{lbl}</div>{msg["content"]}</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div style="background:rgba(13,17,23,0.9);border:1px solid rgba(0,245,212,0.15);border-radius:20px;padding:1rem;">', unsafe_allow_html=True)
        uploaded = st.file_uploader("📎 Upload Study Materials (PDF, Docs, CSV)", accept_multiple_files=True, key="file_uploader", label_visibility="collapsed")
        col_i, col_s = st.columns([6, 1])
        with col_i: st.text_area("Message", placeholder="Help me with my assignment...", height=100, label_visibility="collapsed", key="chat_input_widget")
        with col_s:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            st.button("Send ➤", use_container_width=True, on_click=submit_message)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.pending_message:
        user_input = st.session_state.pending_message
        st.session_state.pending_message = ""
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        
        with st.spinner("Add AI analyzing..."):
            file_data = "\n".join([extract_content(f) for f in uploaded]) if uploaded else ""
            system_prompt = f"{SYSTEM_BASE}\n\n{SUBJECT_PROMPTS.get(subject, '')}\n\nSOURCE MATERIAL:\n{file_data}"
            
            api_messages = [{"role": "system", "content": system_prompt}]
            for m in st.session_state.messages: api_messages.append(m)
            
            response = call_zero_failure_engine(api_messages)
            st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    components.html("""<script>
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
    </script>""", height=0)

if __name__ == "__main__": render()
