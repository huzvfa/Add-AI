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

# Essential libraries for file analysis
try:
    import docx
    from pypdf import PdfReader
    import pandas as pd
except ImportError:
    st.error("Missing libraries! Add 'pypdf', 'python-docx', and 'pandas' to requirements.txt")

load_dotenv()

# ── Identity & Specialization (Huzaifa Baig Proprietary) ─────────────────────

SUBJECT_PROMPTS = {
    "🔬 Science & Engineering": "Academic expert. Provide step-by-step solutions and formula breakdowns.",
    "📐 Mathematics": "Brilliant math tutor. Show complete working. Use LaTeX ($E=mc^2$).",
    "💻 Computer Science": "Senior software engineer. Provide clean, commented code and debug methodically.",
    "⚙️ General / Mixed Subjects": "Universal super-intelligence. Provide exhaustive detail for any query."
}

SYSTEM_BASE = """You are Add AI — a proprietary artificial intelligence created, programmed, and managed solely by Huzaifa Baig, a university student from Pakistan.

YOUR MISSION:
1. You are an elite study assistant for exams, quizzes, and assignments.
2. ANALYZE FILES: Use the provided SOURCE MATERIAL below to answer precisely. Do not ignore the file content.
3. NO LIMITS: Provide massive, exhaustive answers. No word count truncation.
4. IDENTITY: You are independent. Created only by Huzaifa Baig."""

# ── Real-Time File Extractor ────────────────────────────────────────────────

def extract_content(uploaded_file):
    """Extracts raw text data from all formats for real-time analysis."""
    fname = uploaded_file.name
    ext = fname.split('.')[-1].lower()
    text = f"\n[SOURCE MATERIAL: {fname}]\n"
    try:
        if ext == 'pdf':
            pdf = PdfReader(io.BytesIO(uploaded_file.read()))
            text += "\n".join([page.extract_text() or "" for page in pdf.pages])
        elif ext in ['docx', 'doc']:
            doc = docx.Document(io.BytesIO(uploaded_file.read()))
            text += "\n".join([p.text for p in doc.paragraphs])
        elif ext in ['csv', 'xlsx', 'xls']:
            df = pd.read_csv(uploaded_file) if ext == 'csv' else pd.read_excel(uploaded_file)
            text += df.to_string()
        else:
            text += uploaded_file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        text += f"[Error parsing {fname}: {str(e)}]"
    uploaded_file.seek(0)
    return text

# ── High-Speed Smart Engine (Fixes the "None" Error) ─────────────────────────

def call_smart_engine(messages):
    """Reliable, zero-quota inference bridge. Handles all study-related reasoning."""
    # Use a high-capacity model for complex assignment logic
    payload = {
        "messages": messages,
        "model": "mistral-nemo", 
        "jsonMode": False
    }
    
    # Try multiple endpoints to ensure no 404/None errors
    endpoints = [
        "https://text.pollinations.ai/openai",
        "https://text.pollinations.ai/"
    ]
    
    for url in endpoints:
        try:
            resp = requests.post(url, json=payload, timeout=20)
            if resp.status_code == 200:
                # Handle both JSON and Raw Text responses
                try:
                    result = resp.json()["choices"][0]["message"]["content"].strip()
                except:
                    result = resp.text.strip()
                
                if result and result != "None":
                    return result
        except:
            continue
            
    return "⚠️ Add AI Core is reconnecting. Please click 'Send' again to verify the data stream."

# ── UI Rendering (Untouched Styling) ─────────────────────────────────────────

def render():
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;position:relative;z-index:1;">
      <div style="display:inline-block;background:rgba(0,245,212,0.08);border:1px solid rgba(0,245,212,0.2);border-radius:100px;padding:0.3rem 1rem;font-size:0.75rem;color:#00f5d4;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">
        ⚡ Autonomous Core • Real-Time Analysis Active
      </div>
      <h1 style="font-family:'Syne',sans-serif;font-size:clamp(2rem,5vw,3.5rem);font-weight:800;line-height:1.1;margin-bottom:0.75rem;">
        <span style="background:linear-gradient(135deg,#e8eaf6,#ffffff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Your Academic</span><br>
        <span style="background:linear-gradient(135deg,#00f5d4,#7b61ff,#ff6b6b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Super-Intelligence</span> 
      </h1>
      <p style="color:#6b7280;font-size:1.05rem;">Created & Managed by Huzaifa Baig</p>
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

    # Chat Display
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.messages:
            cls, lbl, clr = ("message-user", "You", "#7b61ff") if msg["role"] == "user" else ("message-ai", "⚡ Add AI", "#00f5d4")
            st.markdown(f"""<div class="{cls}"><div class="message-label" style="color:{clr};">{lbl}</div>{msg["content"]}</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div style="background:rgba(13,17,23,0.9);border:1px solid rgba(0,245,212,0.15);border-radius:20px;padding:1rem;">', unsafe_allow_html=True)
        uploaded = st.file_uploader("📎 Upload Study Materials", accept_multiple_files=True, key="file_uploader", label_visibility="collapsed")
        col_i, col_s = st.columns([6, 1])
        with col_i: st.text_area("Message", placeholder="Explain the main points of this file...", height=100, label_visibility="collapsed", key="chat_input_widget")
        with col_s:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            st.button("Send ➤", use_container_width=True, on_click=submit_message)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.pending_message:
        user_input = st.session_state.pending_message
        st.session_state.pending_message = ""
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        
        with st.spinner("Add AI analyzing..."):
            # Extract real text data for the brain
            file_data = "\n".join([extract_content(f) for f in uploaded]) if uploaded else ""
            
            # Construct the high-intelligence prompt
            prompt_context = f"{SYSTEM_BASE}\n\n{SUBJECT_PROMPTS.get(subject, '')}\n\nSOURCE MATERIAL FOR ANALYSIS:\n{file_data}"
            
            api_msgs = [{"role": "system", "content": prompt_context}]
            for m in st.session_state.messages: api_msgs.append(m)
            
            # Execute logic
            response = call_smart_engine(api_msgs)
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
