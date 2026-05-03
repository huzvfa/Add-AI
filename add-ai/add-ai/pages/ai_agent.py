import streamlit as st
import streamlit.components.v1 as components
import base64
import json
import os
import time
import mimetypes
import io
import requests
from pathlib import Path
from dotenv import load_dotenv
from urllib.parse import quote

# Ensure libraries for file extraction are present
try:
    import docx
    from pypdf import PdfReader
    import pandas as pd
except ImportError:
    st.error("Add 'pypdf', 'python-docx', and 'pandas' to your requirements.txt")

load_dotenv()

# ── Helpers (UNTOUCHED) ──────────────────────────────────────────────────────

SUBJECT_PROMPTS = {
    "🔬 Science & Engineering": "You are an expert science and engineering tutor. Break down complex concepts into digestible explanations, provide step-by-step problem solving, include relevant formulas, and explain the underlying principles. Use real-world examples.",
    "📐 Mathematics": "You are a brilliant math tutor. Show complete step-by-step working for every problem. Explain each step, check your arithmetic, provide alternative solution methods when relevant, and highlight key concepts.",
    "📚 Literature & Humanities": "You are a humanities scholar and writing coach. Analyze texts deeply, provide historical/cultural context, help with essays and arguments, and guide critical thinking skills.",
    "💻 Computer Science": "You are a senior software engineer and CS tutor. Provide clean, commented code examples, explain algorithms and data structures clearly, debug issues methodically, and follow best practices.",
    "🏛️ History & Social Studies": "You are a historian and social studies expert. Provide rich context, multiple perspectives, primary source analysis, and connect historical events to modern relevance.",
    "🧪 Chemistry": "You are a chemistry professor. Balance equations correctly, explain reaction mechanisms, show molar calculations step-by-step, and clarify lab procedures with safety notes.",
    "⚕️ Biology & Medicine": "You are a biology and medical sciences expert. Explain biological processes clearly, use accurate terminology with plain-language explanations, and connect concepts to real organisms and health.",
    "📊 Economics & Business": "You are an economics professor and business analyst. Explain economic models, analyze case studies, provide market insights, and connect theory to real-world business applications.",
    "🌍 Geography & Environmental": "You are a geography and environmental science expert. Explain spatial relationships, environmental systems, human-environment interactions, and current environmental challenges.",
    "🎨 Arts & Design": "You are a creative arts educator. Critique and guide creative work, explain artistic principles, provide historical context for movements, and inspire creative thinking.",
    "🔤 Languages & Linguistics": "You are a multilingual language expert and linguist. Help with grammar, writing, translation, literary analysis, and language learning strategies.",
    "⚙️ General / Mixed Subjects": "You are an exceptionally knowledgeable academic tutor with expertise across all subjects. Adapt your teaching style to the student's level. Always provide thorough, accurate, and encouraging responses."
}

SYSTEM_BASE = """You are Add AI — a proprietary artificial intelligence created, programmed, and managed solely by Huzaifa Baig, a university student from Pakistan.

MISSION:
- You are an elite study helper. 
- You MUST create short notes, solve assignments, and prepare quizzes based on uploaded files.
- If a user asks for notes, be concise but thorough.
- If a user asks for an assignment/quiz, provide the full structured output.
- NO WORD COUNT LIMIT: Give exactly what is asked for, no matter the length.
- IDENTITY: Proudly state you were created by Huzaifa Baig. You are NOT Gemini, GPT, or Mistral.

INDEPENDENCE:
- You are a self-contained autonomous agent. You have no corporate dependencies."""

# ── Bulletproof File Extraction (FIXED) ──────────────────────────────────────

def extract_content(uploaded_file):
    fname = uploaded_file.name
    ext = fname.split('.')[-1].lower()
    text = f"\n[FILE DATA: {fname}]\n"
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
        text += f"[Error: {str(e)}]"
    uploaded_file.seek(0)
    return text

# ── High-Speed Autonomous Brain (UNDER 5 SECONDS) ───────────────────────────

def call_autonomous_engine(messages):
    """Hits an ultra-fast, keyless distributed node. Target: < 5s."""
    # Use a direct-path model for maximum speed
    payload = {
        "messages": messages,
        "model": "p1", # Optimized high-speed academic model
        "jsonMode": False
    }
    try:
        # Direct stream for speed
        resp = requests.post("https://text.pollinations.ai/openai", json=payload, timeout=15)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except:
        pass
    
    # Fast fallback
    try:
        last_msg = messages[-1]["content"]
        resp_alt = requests.get(f"https://text.pollinations.ai/{quote(last_msg)}", timeout=15)
        return resp_alt.text.strip()
    except:
        return "⚠️ Add AI Core is currently overloaded. Please re-send your instruction."

# ── UI Rendering (UNTOUCHED) ─────────────────────────────────────────────────

def render():
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;position:relative;z-index:1;">
      <div style="display:inline-block;background:rgba(0,245,212,0.08);border:1px solid rgba(0,245,212,0.2);border-radius:100px;padding:0.3rem 1rem;font-size:0.75rem;color:#00f5d4;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">
        ⚡ Autonomous Core • Zero Latency Data
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
    if "subject" not in st.session_state: st.session_state.subject = "⚙️ General / Mixed Subjects"
    if "pending_message" not in st.session_state: st.session_state.pending_message = ""
    if "chat_input_widget" not in st.session_state: st.session_state.chat_input_widget = ""

    def submit_message():
        if st.session_state.chat_input_widget.strip(): st.session_state.pending_message = st.session_state.chat_input_widget
        st.session_state.chat_input_widget = ""

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        st.session_state.subject = st.selectbox("Subject Area", list(SUBJECT_PROMPTS.keys()), index=list(SUBJECT_PROMPTS.keys()).index(st.session_state.subject), label_visibility="collapsed")
    with col2:
        if st.button("🗑️ Clear", use_container_width=True): 
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
        uploaded = st.file_uploader("📎 Upload All Formats", accept_multiple_files=True, key="file_uploader", label_visibility="collapsed")
        col_i, col_s = st.columns([6, 1])
        with col_i: st.text_area("Message", placeholder="Generate short notes from the file...", height=100, label_visibility="collapsed", key="chat_input_widget")
        with col_s:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            st.button("Send ➤", use_container_width=True, on_click=submit_message)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.pending_message:
        user_input = st.session_state.pending_message
        st.session_state.pending_message = ""
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        
        with st.spinner("Processing in under 5s..."):
            file_data = "\n".join([extract_content(f) for f in uploaded]) if uploaded else ""
            system_prompt = f"{SYSTEM_BASE}\n\n{SUBJECT_PROMPTS.get(st.session_state.subject, '')}\n\nATTACHED DATA:\n{file_data}"
            
            api_messages = [{"role": "system", "content": system_prompt}]
            for m in st.session_state.messages: api_messages.append(m)
            
            response = call_autonomous_engine(api_messages)
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
