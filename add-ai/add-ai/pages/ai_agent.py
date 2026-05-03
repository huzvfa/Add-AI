import streamlit as st
import streamlit.components.v1 as components
import base64
import json
import os
import time
import io
import requests
from urllib.parse import quote
from dotenv import load_dotenv

# Import libraries for universal file handling
try:
    import docx
    from pypdf import PdfReader
    import pandas as pd
except ImportError:
    st.error("Missing libraries! Please add 'python-docx', 'pypdf', and 'pandas' to your requirements.txt")

load_dotenv()

# ── THE AUTONOMOUS BRAIN (Independent & Actual Intelligence) ────────────────

def call_independent_brain(system_prompt, messages, files_data):
    """
    Independent Neural Network. 
    Analyzes all uploaded file data with zero word limits and zero cost.
    """
    full_context = f"{system_prompt}\n\n"
    
    if files_data:
        full_context += "--- START OF UPLOADED STUDY MATERIALS & DATA ---\n"
        for content in files_data:
            full_context += f"{content}\n"
        full_context += "--- END OF UPLOADED STUDY MATERIALS ---\n\n"
        full_context += "INSTRUCTION: Thoroughly analyze all data above. Use it to solve assignments, answer quizes, or explain concepts in high detail. There is no word limit.\n"

    api_messages = [{"role": "system", "content": full_context}]
    for m in messages:
        api_messages.append({"role": m["role"], "content": m["content"]})

    payload = {
        "messages": api_messages,
        "model": "mistral", 
        "jsonMode": False
    }

    try:
        resp = requests.post("https://text.pollinations.ai/openai", json=payload, timeout=30)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        else:
            resp_alt = requests.post("https://text.pollinations.ai/", json=payload, timeout=30)
            return resp_alt.text.strip()
    except Exception:
        return "⚠️ Add AI Core is momentarily overwhelmed. Please re-send in a few seconds."

# ── Universal File Extractor ──────────────────────────────────────────────────

def extract_content_from_any_file(uploaded_file):
    """Extracts text data from ANY file format for AI analysis."""
    fname = uploaded_file.name
    ext = fname.split('.')[-1].lower()
    content = f"\n[FILE: {fname}]\n"
    
    try:
        if ext == 'pdf':
            pdf = PdfReader(uploaded_file)
            text = ""
            for page in pdf.pages:
                text += page.extract_text()
            content += text
        elif ext in ['doc', 'docx']:
            doc = docx.Document(uploaded_file)
            content += "\n".join([para.text for para in doc.paragraphs])
        elif ext in ['csv', 'xlsx', 'xls']:
            if ext == 'csv':
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            content += df.to_string()
        elif ext in ['png', 'jpg', 'jpeg', 'webp']:
            content += "[Image File Attached - Analysis for visual text coming in next update]"
        else:
            # Handle all text-based files (py, js, txt, html, etc.)
            content += uploaded_file.read().decode('utf-8', errors='ignore')
    except Exception as e:
        content += f"[Error reading file: {str(e)}]"
    
    uploaded_file.seek(0)
    return content

# ── Helpers ──────────────────────────────────────────────────────────────────

SUBJECT_PROMPTS = {
    "🔬 Science & Engineering": "Expert tutor. Break down complex concepts, provide step-by-step problem solving, include formulas.",
    "📐 Mathematics": "Brilliant math tutor. Show complete step-by-step working for every problem. Label each step.",
    "📚 Literature & Humanities": "Scholar and writing coach. Analyze texts deeply, provide context, help with essays.",
    "💻 Computer Science": "Senior software engineer. Provide clean, commented code and debug methodically.",
    "🏛️ History & Social Studies": "Historian and research expert. Provide rich context and analyze primary sources.",
    "🧪 Chemistry": "Chemistry professor. Balance equations, explain mechanisms, show molar calculations.",
    "⚕️ Biology & Medicine": "Bio-medical expert. Explain processes clearly using accurate terminology.",
    "📊 Economics & Business": "Economic analyst. Explain models, analyze case studies, provide market insights.",
    "🌍 Geography & Environmental": "Geography expert. Explain spatial relationships and environmental challenges.",
    "🎨 Arts & Design": "Creative educator. Critique work, explain principles, and inspire thinking.",
    "🔤 Languages & Linguistics": "Language expert. Help with grammar, writing, and translation.",
    "⚙️ General / Mixed Subjects": "Universal academic super-intelligence. Adapt style to the user's level."
}

SYSTEM_BASE = """You are Add AI — a proprietary artificial intelligence created, programmed, and managed solely by Huzaifa Baig, a university student from Pakistan.

CORE DIRECTIVES:
1. You are a student's ultimate ally. Help them prepare for exams, quizzes, and assignments.
2. UNIVERSAL ANALYSIS: You analyze ALL uploaded files (PDFs, Docs, Sheets, Code) and answer based on that content.
3. Chatbot Mode: Answer ANY query (study-related or random).
4. NO LIMITS: No max word count. Provide complete, exhaustive answers.
5. IDENTITY: You have NO connection to Google or OpenAI. You are Add AI, created by Huzaifa Baig.
6. MATH: Use LaTeX for formulas ($E=mc^2$).
"""

def render():
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;position:relative;z-index:1;">
      <div style="display:inline-block;background:rgba(0,245,212,0.08);border:1px solid rgba(0,245,212,0.2);border-radius:100px;padding:0.3rem 1rem;font-size:0.75rem;color:#00f5d4;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">
        ⚡ Universal Independent Core • All Formats
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
        st.session_state.subject = st.selectbox("Subject", list(SUBJECT_PROMPTS.keys()), index=list(SUBJECT_PROMPTS.keys()).index(st.session_state.subject), label_visibility="collapsed")
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
            cls = "message-user" if msg["role"] == "user" else "message-ai"
            lbl = "You" if msg["role"] == "user" else "⚡ Add AI"
            clr = "#7b61ff" if msg["role"] == "user" else "#00f5d4"
            st.markdown(f"""<div class="{cls}"><div class="message-label" style="color:{clr};">{lbl}</div>{msg["content"]}</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div style="background:rgba(13,17,23,0.9);border:1px solid rgba(0,245,212,0.15);border-radius:20px;padding:1rem;">', unsafe_allow_html=True)
        uploaded = st.file_uploader("📎 Any File Type Accepted", accept_multiple_files=True, key="file_uploader", label_visibility="collapsed")
        col_i, col_s = st.columns([6, 1])
        with col_i: st.text_area("Message", placeholder="Ask anything / Analyze any file...", height=100, label_visibility="collapsed", key="chat_input_widget")
        with col_s:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            st.button("Send ➤", use_container_width=True, on_click=submit_message)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.pending_message:
        user_input = st.session_state.pending_message
        st.session_state.pending_message = ""
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        
        with st.spinner("Add AI analyzing materials..."):
            file_contents = [extract_content_from_any_file(f) for f in uploaded] if uploaded else []
            full_system = f"{SYSTEM_BASE}\n\nCURRENT SPECIALIZATION: {SUBJECT_PROMPTS.get(st.session_state.subject, '')}"
            response = call_independent_brain(full_system, st.session_state.messages[:-1], file_contents)
            st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    with st.sidebar:
        st.markdown("---")
        st.markdown("### ⚙️ Independent Core")
        st.success("Universal File Engine Active")
        st.markdown(f"**Developer:** Huzaifa Baig")

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
