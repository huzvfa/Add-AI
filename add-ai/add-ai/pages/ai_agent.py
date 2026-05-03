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

# Essential libraries
try:
    import docx
    from pypdf import PdfReader
    import pandas as pd
except ImportError:
    st.error("Missing libraries! Add 'pypdf', 'python-docx', and 'pandas' to requirements.txt")

load_dotenv()

# ── Identity & Specialization ─────────────────────

SUBJECT_PROMPTS = {
    "🔬 Science & Engineering": "You are an expert science and engineering tutor. Break down complex concepts and include formulas.",
    "📐 Mathematics": "You are a math tutor. Show full working using LaTeX.",
    "💻 Computer Science": "You are a senior software engineer. Provide clean, debugged code.",
    "⚙️ General / Mixed Subjects": "You are an advanced academic tutor."
}

SYSTEM_BASE = """You are Add AI — created by Huzaifa Baig.

MISSION:
- Help students using ONLY provided study material
- If answer is not found, say: "Not found in provided files."
- Be detailed and clear
"""

# ── FILE EXTRACTION ─────────────────────

def extract_content(uploaded_file):
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
        text += f"[Data Extraction Error: {str(e)}]"

    uploaded_file.seek(0)
    return text


# ── TEXT CHUNKING (FIX) ─────────────────────

def chunk_text(text, size=3000):
    return [text[i:i+size] for i in range(0, len(text), size)]


# ── AI CALL (STABLE) ─────────────────────

def call_independent_brain(messages):
    payload = {
        "messages": messages,
        "model": "mistral",
        "jsonMode": False
    }

    # Primary
    try:
        resp = requests.post(
            "https://text.pollinations.ai/openai",
            json=payload,
            timeout=30
        )
        if resp.status_code == 200:
            data = resp.json()
            if "choices" in data:
                return data["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print("Primary failed:", e)

    # Fallback
    try:
        resp = requests.post(
            "https://text.pollinations.ai/",
            json=payload,
            timeout=30
        )
        if resp.status_code == 200 and resp.text:
            return resp.text.strip()
    except Exception as e:
        print("Fallback failed:", e)

    return "⚠️ Add AI failed to generate a response. Try again."


# ── UI (UNCHANGED) ─────────────────────

def render():
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;position:relative;z-index:1;">
      <div style="display:inline-block;background:rgba(0,245,212,0.08);border:1px solid rgba(0,245,212,0.2);border-radius:100px;padding:0.3rem 1rem;font-size:0.75rem;color:#00f5d4;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">
        ⚡ Autonomous Core • Created by Huzaifa Baig
      </div>
      <h1 style="font-family:'Syne',sans-serif;font-size:clamp(2rem,5vw,3.5rem);font-weight:800;line-height:1.1;margin-bottom:0.75rem;">
        <span style="background:linear-gradient(135deg,#e8eaf6,#ffffff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Your Academic</span><br>
        <span style="background:linear-gradient(135deg,#00f5d4,#7b61ff,#ff6b6b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Super-Intelligence</span> 
      </h1>
      <p style="color:#6b7280;font-size:1.05rem;">Manage Your Study Ally</p>
    </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state: st.session_state.messages = []
    if "pending_message" not in st.session_state: st.session_state.pending_message = ""
    if "chat_input_widget" not in st.session_state: st.session_state.chat_input_widget = ""

    def submit_message():
        if st.session_state.chat_input_widget.strip():
            st.session_state.pending_message = st.session_state.chat_input_widget
        st.session_state.chat_input_widget = ""

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        subject = st.selectbox("Specialization", list(SUBJECT_PROMPTS.keys()), label_visibility="collapsed")
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
        uploaded = st.file_uploader("📎 Upload Study Materials", accept_multiple_files=True, key="file_uploader", label_visibility="collapsed")

        col_i, col_s = st.columns([6, 1])
        with col_i:
            st.text_area("Message", placeholder="Explain this file in detail...", height=100, label_visibility="collapsed", key="chat_input_widget")
        with col_s:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            st.button("Send ➤", use_container_width=True, on_click=submit_message)

        st.markdown("</div>", unsafe_allow_html=True)

    # ── FIXED LOGIC ONLY ─────────────────────

    if st.session_state.pending_message:
        user_input = st.session_state.pending_message
        st.session_state.pending_message = ""

        st.session_state.messages.append({"role": "user", "content": user_input.strip()})

        with st.spinner("Add AI analyzing..."):

            # Extract files
            file_data = "\n".join([extract_content(f) for f in uploaded]) if uploaded else ""

            # System message
            system_msg = {
                "role": "system",
                "content": f"""
{SYSTEM_BASE}

{SUBJECT_PROMPTS.get(subject, '')}

STRICT RULE:
- Answer ONLY using uploaded material
- If not found, say: Not found in provided files
"""
            }

            api_msgs = [system_msg]

            # Short memory
            for m in st.session_state.messages[-4:]:
                api_msgs.append(m)

            # Inject file chunks
            if file_data:
                chunks = chunk_text(file_data)
                for i, chunk in enumerate(chunks[:5]):
                    api_msgs.append({
                        "role": "system",
                        "content": f"[FILE PART {i+1}]\n{chunk}"
                    })

            # Grounded question
            api_msgs.append({
                "role": "user",
                "content": f"""
USER QUESTION:
{user_input}

Answer strictly using the uploaded material above.
"""
            })

            response = call_independent_brain(api_msgs)

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


if __name__ == "__main__":
    render()
