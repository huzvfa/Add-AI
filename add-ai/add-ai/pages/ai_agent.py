import streamlit as st
import streamlit.components.v1 as components
import io
import re
import time
import requests
import numpy as np
from dotenv import load_dotenv

# ── Local Machine Learning Libraries (The Ultimate Fix) ──
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_ML = True
except ImportError:
    HAS_ML = False

# ── File Extractors ──
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

APP_NAME    = "Add AI"
CREATOR     = "Huzaifa Baig"
ENGINE_NAME = "ADDCORE-OMEGA"

SYSTEM_PROMPT = f"""You are {APP_NAME}, a sovereign AI created by {CREATOR}. 
You are a highly intelligent, student-centric study helper.
Answer questions directly and intelligently."""

def extract_text(uploaded_file) -> str:
    ext  = uploaded_file.name.rsplit(".", 1)[-1].lower()
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
            result = pd.read_csv(io.BytesIO(raw)).to_string() if ext == "csv" else pd.read_excel(io.BytesIO(raw)).to_string()
        else:
            result = raw.decode("utf-8", errors="ignore")
    except Exception:
        pass
    return result

def local_semantic_search(query, document):
    """LOCAL NLP ENGINE: Runs purely on CPU. Never fails, never needs internet."""
    if not HAS_ML: return "Local ML libraries missing. Add scikit-learn to requirements.txt"
    
    # Break document into sentences
    sentences = re.split(r'(?<=[.!?]) +|\n+', document)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 10]
    
    if not sentences: return document[:1000] # Return raw if unstructured

    # Vectorize and mathematically find the exact answer
    vectorizer = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = vectorizer.fit_transform(sentences)
        query_vec = vectorizer.transform([query])
        sims = cosine_similarity(query_vec, tfidf_matrix).flatten()
        
        # Get top 3 most relevant sentences
        best_indices = np.argsort(sims)[-3:]
        best_sentences = [sentences[i] for i in best_indices if sims[i] > 0.05]
        
        if best_sentences:
            return f"**(Local ML Extraction):** " + " ".join(best_sentences)
        return "I analyzed the document locally, but found no direct mathematical correlation to your query. Please rephrase."
    except Exception as e:
        return f"Local extraction error: {str(e)}"

def call_add_ai_engine(user_query, file_data):
    """High-Speed Router. Tries API for 3 seconds, then instantly falls back to Local NLP."""
    q_lower = user_query.lower()
    if any(x in q_lower for x in ["who are you", "creator", "developer"]):
        return f"I am {APP_NAME}, a sovereign artificial intelligence built entirely by {CREATOR}."

    # 1. Attempt Network API (With Anti-Bot Headers)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json"
    }
    
    prompt = SYSTEM_PROMPT + f"\n\nDATA:\n{file_data[:3000]}\n\nQUERY: {user_query}" if file_data else f"{SYSTEM_PROMPT}\n\nQUERY: {user_query}"
    
    try:
        resp = requests.post("https://text.pollinations.ai/", json={"messages": [{"role": "user", "content": prompt}]}, headers=headers, timeout=3)
        if resp.status_code == 200 and resp.text: return resp.text.strip()
    except Exception:
        pass

    # 2. Local Machine Learning Fallback (ZERO LATENCY, ZERO API)
    if file_data:
        return local_semantic_search(user_query, file_data)
    
    return "I am currently disconnected from the global network. Please upload a file and I will analyze it locally."

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

    for m in st.session_state.chat_messages:
        cls, lbl, clr = ("msg-user", "You", "#7b61ff") if m["role"] == "user" else ("msg-ai", f"⚡ {APP_NAME}", "#00f5d4")
        st.markdown(f'<div class="{cls}"><div class="msg-label" style="color:{clr};">{lbl}</div>{m["content"]}</div>', unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    uploaded_files = st.file_uploader("📎 Upload Study Materials", accept_multiple_files=True)
    
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

    if st.session_state.pending_prompt:
        user_query = st.session_state.pending_prompt
        st.session_state.pending_prompt = ""
        st.session_state.chat_messages.append({"role": "user", "content": user_query})
        
        anim_placeholder = st.empty()
        anim_placeholder.markdown(f"""<div style="text-align:center; padding: 2rem;"><div class="logo-anim">⚡</div></div>""", unsafe_allow_html=True)
        
        file_data = "".join([extract_text(f) for f in uploaded_files]) if uploaded_files else ""
        response = call_add_ai_engine(user_query, file_data)
        
        anim_placeholder.empty()
        st.session_state.chat_messages.append({"role": "assistant", "content": response})
        st.rerun()

if __name__ == "__main__":
    render()
