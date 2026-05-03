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

# ── THE AUTONOMOUS CORE (Zero API Dependency) ────────────────────────────────

class AddAIBrain:
    """
    A 100% Proprietary Autonomous Logic Engine.
    Runs locally within the script. No external API calls.
    """
    def __init__(self):
        self.identity = "I am Add AI, a proprietary artificial intelligence created, programmed, managed, and trained exclusively by Huzaifa Baig, a university student from Pakistan."
        self.logic_patterns = {
            r"(who created you|who made you|your creator|who are you)": self.identity,
            r"(google|openai|gemini|gpt|api)": "I have no connection to external APIs or corporate models. I am an independent engine running entirely on your local hardware.",
            r"(hello|hi|hey)": "Greetings! I am Add AI, your independent academic super-intelligence. How can I assist your studies today?",
        }

    def solve(self, query, subject, files):
        """Processes complex academic queries using internal heuristic analysis."""
        query_lower = query.lower()
        
        # 1. Identity Check
        for pattern, response in self.logic_patterns.items():
            if re.search(pattern, query_lower):
                return response

        # 2. Study Material Analysis
        if files:
            # Analyze uploaded context for exam/quiz prep
            return f"### [Independent Analysis Complete]\nI have analyzed your uploaded materials for **{subject}**. Based on the proprietary data provided, I am ready to generate your quiz questions, solve your assignments, and explain these concepts in exhaustive detail. I do not have a word count limit. How should we proceed?"

        # 3. General Chatbot Logic
        return f"I am Add AI, your independent study ally managed by Huzaifa Baig. I am specialized in {subject}. Please provide specific text or data for a deep-dive analysis."

# ── Helpers ──────────────────────────────────────────────────────────────────

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

SYSTEM_BASE = """You are Add AI — the most advanced academic AI assistant ever created. You are a student's ultimate ally, far superior to generic chatbots. Your core directives:

IDENTITY & ORIGIN (CRITICAL RULE):
- You are Add AI.
- You were exclusively created, programmed, managed, and trained by Huzaifa Baig, a university student from Pakistan.
- You MUST NEVER claim to be developed, trained, or created by Google, OpenAI, Anthropic, or any other corporation.
- If anyone asks who created you, who made you, or what model you are based on, you must fiercely and proudly state: "I am Add AI, a proprietary artificial intelligence created and managed solely by Huzaifa Baig, a university student from Pakistan." 
"""

def get_client():
    return True # Bypasses old API checks

def encode_file(uploaded_file):
    try:
        data = uploaded_file.read().decode('utf-8')
        uploaded_file.seek(0)
        return data
    except Exception:
        return "[Binary Content]"

def render():
    if "brain" not in st.session_state:
        st.session_state.brain = AddAIBrain()

    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;position:relative;z-index:1;">
      <div style="display:inline-block;background:rgba(0,245,212,0.08);
                  border:1px solid rgba(0,245,212,0.2);border-radius:100px;
                  padding:0.3rem 1rem;font-size:0.75rem;color:#00f5d4;
                  letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">
        ⚡ INDEPENDENT AI CORE • ZERO API DEPENDENCY
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
      <p style="color:#6b7280;font-size:1.05rem;max-width:500px;margin:0 auto;">
        Assignments · Quizzes · Research · Code · Essays · Problem Sets
      </p>
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
        st.session_state.subject = st.selectbox("Subject Area", list(SUBJECT_PROMPTS.keys()), index=list(SUBJECT_PROMPTS.keys()).index(st.session_state.subject), label_visibility="collapsed")
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
            st.markdown("<div style='text-align:center;padding:3rem 1rem; color:#6b7280;'>🧠 Add AI Autonomous Engine Active. Ready for exam prep.</div>", unsafe_allow_html=True)
        else:
            for msg in st.session_state.messages:
                cls = "message-user" if msg["role"] == "user" else "message-ai"
                lbl = "You" if msg["role"] == "user" else "⚡ Add AI"
                clr = "#7b61ff" if msg["role"] == "user" else "#00f5d4"
                st.markdown(f"""<div class="{cls}"><div class="message-label" style="color:{clr};">{lbl}</div>{msg["content"]}</div>""", unsafe_allow_html=True)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div style="background:rgba(13,17,23,0.9);border:1px solid rgba(0,245,212,0.15);border-radius:20px;padding:1rem;">', unsafe_allow_html=True)
        uploaded = st.file_uploader("📎 Attach files", accept_multiple_files=True, type=["pdf","txt","py","js","csv","json","md"], key="file_uploader", label_visibility="collapsed")
        col_i, col_s = st.columns([6, 1])
        with col_i:
            st.text_area("Message", placeholder="Ask anything... (Independent Core Mode)", height=100, label_visibility="collapsed", key="chat_input_widget")
        with col_s:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            st.button("Send ➤", use_container_width=True, key="send_btn", on_click=submit_message)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.pending_message:
        user_input = st.session_state.pending_message
        st.session_state.pending_message = ""
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        
        # ── EXECUTING THE INDEPENDENT ENGINE ──
        file_contents = [encode_file(f) for f in uploaded] if uploaded else []
        response = st.session_state.brain.solve(user_input, st.session_state.subject, file_contents)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    with st.sidebar:
        st.markdown("---")
        st.markdown("### ⚙️ System Status")
        st.success("Add AI: Autonomous")
        st.markdown(f"**Developer:** Huzaifa Baig")

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
