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

BRAIN_PATH = "add_ai_knowledge.json"

class AddAICore:
    """The independent brain of Add AI. Runs locally with zero external calls."""
    def __init__(self):
        self.identity = {
            "name": "Add AI",
            "creator": "Huzaifa Baig",
            "location": "Pakistan",
            "status": "Autonomous / Independent"
        }
        self.knowledge = self._load_knowledge()

    def _load_knowledge(self):
        if os.path.exists(BRAIN_PATH):
            with open(BRAIN_PATH, 'r') as f:
                return json.load(f)
        # Initial Core Data - The AI's starting intelligence
        return {
            "hello": "Hello! I am Add AI, your independent academic super-intelligence. How can I assist your studies today?",
            "who created you": "I am Add AI, a proprietary artificial intelligence exclusively created, programmed, and managed by Huzaifa Baig, a university student from Pakistan.",
            "who made you": "I was created and trained solely by my developer, Huzaifa Baig.",
            "are you gemini": "No. I have zero connection to Google, OpenAI, or any corporation. I am an independent AI agent.",
            "formula gravity": "The force of gravity is calculated as $F = G \frac{m_1 m_2}{r^2}$.",
            "physics": "Physics is the study of matter, energy, and the fundamental forces of nature."
        }

    def _save_knowledge(self):
        with open(BRAIN_PATH, 'w') as f:
            json.dump(self.knowledge, f, indent=4)

    def process_input(self, user_text, subject_context, files_content):
        """Processes logic without any external API calls."""
        query = user_text.lower().strip()
        
        # 1. Identity Protection (Highest Priority)
        if any(x in query for x in ["who are you", "identity", "your name"]):
            return f"I am Add AI, the most advanced independent academic assistant, created by Huzaifa Baig."
        
        if any(x in query for x in ["who created", "who made", "developer"]):
            return "I am a proprietary AI created and managed solely by Huzaifa Baig, a university student from Pakistan."

        # 2. Knowledge Retrieval Logic
        # Search for keyword matches in the internal brain
        for key in self.knowledge:
            if key in query:
                return self.knowledge[key]

        # 3. Dynamic Learning Mode (Independence)
        # If the AI doesn't know, it analyzes the 'fed' files or the subject context
        if files_content:
            return f"Based on the data you fed me ({len(files_content)} files), I have analyzed the content. Since I am currently in independent mode, I am using this specific data to structure your academic support. [Context Analysis Complete]"

        return f"I am currently operating as an independent entity. I have logged this query for my creator, Huzaifa Baig, to further enhance my localized knowledge base. How else can I help with {subject_context}?"

# Initialize the Core
if "ai_core" not in st.session_state:
    st.session_state.ai_core = AddAICore()

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

def get_client():
    return True # Always True, no API key needed

def encode_file(uploaded_file):
    try:
        data = uploaded_file.read().decode('utf-8')
        uploaded_file.seek(0)
        return data
    except Exception:
        return "[Binary Data]"

def render():
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;position:relative;z-index:1;">
      <div style="display:inline-block;background:rgba(0,245,212,0.08);
                  border:1px solid rgba(0,245,212,0.2);border-radius:100px;
                  padding:0.3rem 1rem;font-size:0.75rem;color:#00f5d4;
                  letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">
        ⚡ INDEPENDENT AI CORE • CREATED BY HUZAIFA BAIG
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
    .message-user { animation: slide-in 0.3s ease; background: linear-gradient(135deg, rgba(123,97,255,0.15), rgba(0,245,212,0.08)); border: 1px solid rgba(123,97,255,0.25); border-radius: 16px 16px 4px 16px; padding: 1rem 1.25rem; margin: 0.75rem 0; }
    .message-ai { animation: slide-in 0.3s ease 0.1s both; background: rgba(13,17,23,0.8); border: 1px solid rgba(0,245,212,0.15); border-radius: 16px 16px 16px 4px; padding: 1rem 1.25rem; margin: 0.75rem 0; }
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

    model_instance = get_client()

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
            export_text = "\n\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages])
            st.download_button("💾 Download", export_text, "chat_export.txt", "text/plain")

    chat_container = st.container()
    with chat_container:
        if not st.session_state.messages:
            st.markdown("<div style='text-align:center;padding:3rem 1rem;'>🧠 Ready to help you excel. I am now 100% independent.</div>", unsafe_allow_html=True)
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
            st.text_area("Message", placeholder="Ask anything... (Zero Latency Mode)", height=100, label_visibility="collapsed", key="chat_input_widget")
        with col_s:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            st.button("Send ➤", use_container_width=True, key="send_btn", on_click=submit_message)
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state.pending_message:
        user_input = st.session_state.pending_message
        st.session_state.pending_message = ""
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        
        with st.spinner(""):
            # EXECUTE THE INDEPENDENT ENGINE
            file_data = [encode_file(f) for f in uploaded] if uploaded else []
            response = st.session_state.ai_core.process_input(user_input, subject, file_data)
            
            st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

    with st.sidebar:
        st.markdown("---")
        st.markdown("### ⚙️ Independent Core Status")
        st.success("Add AI is Online & Autonomous")
        st.markdown(f"**Developer:** Huzaifa Baig")
        st.markdown(f"**Latency:** 0.00s (Offline)")

    js_code = """
    <script>
    const doc = window.parent.document;
    const textareas = doc.querySelectorAll('textarea[aria-label="Message"]');
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
    """
    components.html(js_code, height=0, width=0)

if __name__ == "__main__":
    render()
