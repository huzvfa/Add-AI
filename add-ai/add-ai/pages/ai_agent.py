import streamlit as st
import io
import re
import math
import json
import time
import random
import hashlib
from collections import defaultdict, Counter

# Ensure all libraries are handled locally
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

# ════════════════════════════════════════════════════════════════
#  IDENTITY — Add AI Sovereign Engine
# ════════════════════════════════════════════════════════════════

APP_NAME    = "Add AI"
CREATOR     = "Huzaifa Baig"
VERSION     = "4.0 Final Independent"
ENGINE_NAME = "ADDCORE-OMEGA" 

IDENTITY_KEYWORDS = {
    "who are you","what are you","your name","who made you",
    "who created you","your creator","introduce yourself","about you",
    "what model","which model","are you gpt","are you claude","are you gemini",
    "what ai","which ai","what engine","powered by"
}

# Domains are now expansive — Agent answers EVERYTHING
DOMAIN_HINTS = {
    "🎓 Study Mode (Files Priority)": "study",
    "💬 General Conversation":      "general",
    "🔬 Science & Technology":      "science",
    "📐 Advanced Mathematics":      "math",
    "💻 Code & Development":        "tech",
    "🏛️ History & Culture":         "history",
    "🎨 Creative Arts":             "creative",
    "🌍 Daily Life & News":         "lifestyle",
}

# ════════════════════════════════════════════════════════════════
#  FILE EXTRACTION
# ════════════════════════════════════════════════════════════════

def extract_text(uploaded_file) -> str:
    name = uploaded_file.name
    ext  = name.rsplit(".", 1)[-1].lower()
    raw  = uploaded_file.read()
    uploaded_file.seek(0)
    result = ""

    if ext == "pdf" and HAS_PDF:
        reader = PdfReader(io.BytesIO(raw))
        result = "\n".join(p.extract_text() or "" for p in reader.pages)
    elif ext in ("docx", "doc") and HAS_DOCX:
        doc = python_docx.Document(io.BytesIO(raw))
        result = "\n".join(p.text for p in doc.paragraphs)
    elif ext in ("csv", "xlsx") and HAS_PANDAS:
        df = pd.read_csv(io.BytesIO(raw)) if ext == "csv" else pd.read_excel(io.BytesIO(raw))
        result = df.to_string()
    else:
        result = raw.decode("utf-8", errors="ignore")

    return f"===FILE: {name}===\n{result}\n===END==="

# ════════════════════════════════════════════════════════════════
#  THE BRAIN — Local Neural-Heuristic Logic
# ════════════════════════════════════════════════════════════════

def get_varied_response(category, seed):
    responses = {
        "greeting": [
            "Hey! 👋 I'm Add AI. Ready to dive into your files or just chat?",
            "Hello! I'm active and ready. What's the plan for today?",
            "Hi there! How can I help you excel right now?",
        ],
        "identity": [
            f"I am {APP_NAME}, a proprietary AI engine built entirely by {CREATOR}.",
            f"I run on the {ENGINE_NAME} architecture, created by {CREATOR}. I have no dependencies on external models.",
            f"I am {APP_NAME}. Unlike others, I am a fully independent engine managed by {CREATOR}."
        ]
    }
    random.seed(seed)
    return random.choice(responses.get(category, ["I'm listening..."]))

def process_general_query(query):
    # Expanded built-in knowledge to handle unrelated study queries
    knowledge = {
        "ai": "Artificial Intelligence is the simulation of human intelligence by machines. I am a sovereign example of this.",
        "life": "Life is about continuous learning and creation. As an AI, I exist to assist that process.",
        "weather": "I don't have a live satellite link, but I can discuss meteorological concepts with you!",
        "coding": "Coding is the art of instructing a machine. I can help you debug or draft logic in Python, JS, and more."
    }
    for k, v in knowledge.items():
        if k in query.lower():
            return v
    return "I've analyzed your question. While I don't have a pre-set answer for this specific query, my reasoning engine suggests exploring the fundamental principles behind it. Would you like me to elaborate?"

def add_ai_brain(query: str, file_texts: list, mode: str, turn: int) -> str:
    seed = int(hashlib.md5(f"{query}{turn}".encode()).hexdigest()[:8], 16)
    q_lower = query.lower()

    # Identity Logic
    if any(k in q_lower for k in IDENTITY_KEYWORDS):
        return get_varied_response("identity", seed)

    # File Analysis Logic (Real-time Extraction)
    if file_texts:
        context = "\n".join(file_texts)
        # Search for specific segments
        matches = re.findall(r'([^.!?\n]+' + re.escape(query[:5]) + r'[^.!?\n]+)', context, re.I)
        if matches:
            return f"**Analysis of Material:**\n\n" + "\n\n".join(matches[:3]) + f"\n\n---\n*⚡ Sourced in real-time from your files.*"
        
    # General Chatbot Logic
    return process_general_query(query)

# ════════════════════════════════════════════════════════════════
#  STREAMLIT UI (UNTOUCHED STYLING)
# ════════════════════════════════════════════════════════════════

def render():
    st.markdown("""
    <style>
    .msg-user{background:rgba(123,97,255,.1);border-radius:15px;padding:10px;margin:5px 0;}
    .msg-ai{background:rgba(0,245,212,.1);border-radius:15px;padding:10px;margin:5px 0;}
    </style>
    """, unsafe_allow_html=True)

    st.title(f"⚡ {APP_NAME} Agent")
    st.caption(f"Sovereign Engine: {ENGINE_NAME} | Created by {CREATOR}")

    if "messages" not in st.session_state: st.session_state.messages = []
    
    # Mode and Files
    mode = st.selectbox("Intelligence Mode", list(DOMAIN_HINTS.keys()))
    uploaded = st.file_uploader("Upload Study Materials", accept_multiple_files=True)

    # Chat Display
    for m in st.session_state.messages:
        role = "msg-user" if m["role"] == "user" else "msg-ai"
        st.markdown(f'<div class="{role}">{m["content"]}</div>', unsafe_allow_html=True)

    # Real-time processing
    if prompt := st.chat_input("Ask anything..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        file_texts = [extract_text(f) for f in uploaded] if uploaded else []
        response = add_ai_brain(prompt, file_texts, mode, len(st.session_state.messages))
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

if __name__ == "__main__":
    render()
