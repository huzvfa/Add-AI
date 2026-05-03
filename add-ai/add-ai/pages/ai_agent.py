import streamlit as st
import streamlit.components.v1 as components
import base64
import json
import os
import time
import io
import re
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
    "🔬 Science & Engineering": "Focus on scientific explanations and formulas.",
    "📐 Mathematics": "Show step-by-step mathematical working.",
    "💻 Computer Science": "Provide logical and structured explanations.",
    "⚙️ General / Mixed Subjects": "Provide clear and detailed academic explanations."
}

SYSTEM_BASE = """You are Add AI — created by Huzaifa Baig.

MISSION:
- Answer strictly using uploaded study material
- If not found, say: "Not found in provided files."
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

# ── TEXT CHUNKING ─────────────────────

def chunk_text(text, size=3000):
    return [text[i:i+size] for i in range(0, len(text), size)]

# ── LOCAL AI BRAIN (NO API) ─────────────────────

def local_ai_brain(messages):
    question = ""
    for m in reversed(messages):
        if m["role"] == "user":
            question = m["content"].lower()
            break

    file_chunks = []
    for m in messages:
        if m["role"] == "system" and "[FILE PART" in m["content"]:
            file_chunks.append(m["content"])

    if not file_chunks:
        return "⚠️ No study material uploaded."

    q_words = set(re.findall(r'\w+', question))

    scored = []

    for chunk in file_chunks:
        chunk_lower = chunk.lower()
        words = set(re.findall(r'\w+', chunk_lower))
        score = len(q_words.intersection(words))

        if score > 0:
            scored.append((score, chunk))

    if not scored:
        return "Not found in provided files."

    scored.sort(reverse=True, key=lambda x: x[0])

    best_chunks = [c for _, c in scored[:3]]

    answer = "📘 **Answer from your study material:**\n\n"

    for chunk in best_chunks:
        cleaned = chunk.split("]\n", 1)[-1]
        answer += cleaned[:800] + "\n\n---\n\n"

    return answer.strip()

# ── UI ─────────────────────

def render():
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;">
      <div style="display:inline-block;background:rgba(0,245,212,0.08);border:1px solid rgba(0,245,212,0.2);border-radius:100px;padding:0.3rem 1rem;font-size:0.75rem;color:#00f5d4;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">
        ⚡ Autonomous Core • Created by Huzaifa Baig
      </div>
      <h1>Your Academic Super-Intelligence</h1>
      <p>Manage Your Study Ally</p>
    </div>
    """, unsafe_allow_html=True)

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_message" not in st.session_state:
        st.session_state.pending_message = ""
    if "chat_input_widget" not in st.session_state:
        st.session_state.chat_input_widget = ""

    def submit_message():
        if st.session_state.chat_input_widget.strip():
            st.session_state.pending_message = st.session_state.chat_input_widget
        st.session_state.chat_input_widget = ""

    col1, col2, col3 = st.columns([3,1,1])

    with col1:
        subject = st.selectbox("Specialization", list(SUBJECT_PROMPTS.keys()), label_visibility="collapsed")

    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()

    with col3:
        if st.button("📤 Export"):
            export_text = "\n\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            st.download_button("Save", export_text, "chat.txt")

    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Add AI:** {msg['content']}")

    uploaded = st.file_uploader("Upload Study Materials", accept_multiple_files=True)

    st.text_area("Message", key="chat_input_widget")

    st.button("Send ➤", on_click=submit_message)

    # ── MAIN LOGIC ─────────────────────

    if st.session_state.pending_message:
        user_input = st.session_state.pending_message
        st.session_state.pending_message = ""

        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.spinner("Analyzing..."):

            file_data = "\n".join([extract_content(f) for f in uploaded]) if uploaded else ""

            system_msg = {
                "role": "system",
                "content": SYSTEM_BASE + "\n" + SUBJECT_PROMPTS.get(subject, "")
            }

            api_msgs = [system_msg]

            for m in st.session_state.messages[-4:]:
                api_msgs.append(m)

            if file_data:
                chunks = chunk_text(file_data)
                for i, chunk in enumerate(chunks[:5]):
                    api_msgs.append({
                        "role": "system",
                        "content": f"[FILE PART {i+1}]\n{chunk}"
                    })

            api_msgs.append({
                "role": "user",
                "content": user_input
            })

            response = local_ai_brain(api_msgs)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

        st.rerun()

if __name__ == "__main__":
    render()
