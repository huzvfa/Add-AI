import streamlit as st
import streamlit.components.v1 as components
import google.generativeai as genai
import base64
import json
import os
import time
import mimetypes
from pathlib import Path
from dotenv import load_dotenv
import requests
from urllib.parse import quote

# Keep safe_ai_generate defined but we will integrate its logic directly into the 
# processing loop to maintain system prompts and chat history integrity while 
# minimizing other code changes.
def safe_ai_generate(client, prompt):
    """Bypasses Gemini Quota 429 Errors by instantly falling back to an uncapped API."""
    if client:
        try:
            return client.generate_content(prompt).text.strip()
        except Exception:
            pass # Quota exceeded or error, smoothly catch it and fall back
            
    # The 100% free, uncapped fallback (No API key needed)
    try:
        # Switched to mistral model for blazing fast 1-2 second response times
        fallback_url = f"https://text.pollinations.ai/prompt/{quote(prompt)}?model=mistral"
        resp = requests.get(fallback_url, timeout=5)
        if resp.status_code == 200:
            return resp.text.strip()
    except Exception:
        pass
    
    return "Error reaching AI servers."

load_dotenv()

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

ACADEMIC EXCELLENCE STANDARDS:
- Always show complete working/reasoning — never skip steps
- Verify your answers before presenting them
- Provide multiple solution approaches when helpful
- Anticipate follow-up questions and address them proactively
- Format answers beautifully with proper structure, headers, and code blocks
- For math/science: show ALL steps, label each one, state formulas before using them
- For essays/writing: provide structure, thesis guidance, and rich examples
- For code: provide working, commented, tested code with explanations
- Always cite sources when using factual/current information

INTERACTION STYLE:
- Be encouraging and confidence-building, never condescending
- Match vocabulary to the student's apparent level
- Use analogies and real-world examples liberally
- When a question is unclear, ask ONE clarifying question
- End responses with a helpful follow-up prompt when appropriate

FILE ANALYSIS:
- When files are uploaded, analyze them thoroughly before answering
- Extract key information, identify the task type, and tailor your response
- For PDFs/documents: summarize key points and answer questions about the content
- For images: describe and analyze what you see in academic context
- For code files: review, debug, and explain the code

FORMATTING:
- Use markdown headers, bullet points, numbered lists, code blocks, and tables appropriately
- Make responses visually scannable and well-organized
- Use LaTeX-style notation for math when possible: $E = mc^2$

Always be the best academic tutor a student has ever had."""

def get_client():
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        api_key = st.session_state.get("google_key", "")
    if not api_key:
        return None
    genai.configure(api_key=api_key)
    # Changed to gemini-2.0-flash for ultra-low latency 1-2s response times
    return genai.GenerativeModel(model_name='gemini-2.0-flash')

def encode_file(uploaded_file):
    data = uploaded_file.read()
    uploaded_file.seek(0)
    return {"mime_type": uploaded_file.type, "data": data}

def render():
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;position:relative;z-index:1;">
      <div style="display:inline-block;background:rgba(0,245,212,0.08);
                  border:1px solid rgba(0,245,212,0.2);border-radius:100px;
                  padding:0.3rem 1rem;font-size:0.75rem;color:#00f5d4;
                  letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">
        ⚡ Real-time AI • Powered by Gemini
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
    @keyframes pulse-ring {
      0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0,245,212,0.4); }
      70% { transform: scale(1); box-shadow: 0 0 0 15px rgba(0,245,212,0); }
      100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0,245,212,0); }
    }
    @keyframes float {
      0%, 100% { transform: translateY(0); }
      50% { transform: translateY(-8px); }
    }
    @keyframes slide-in {
      from { opacity: 0; transform: translateY(20px); }
      to { opacity: 1; transform: translateY(0); }
    }
    .message-user {
      animation: slide-in 0.3s ease;
      background: linear-gradient(135deg, rgba(123,97,255,0.15), rgba(0,245,212,0.08));
      border: 1px solid rgba(123,97,255,0.25);
      border-radius: 16px 16px 4px 16px;
      padding: 1rem 1.25rem;
      margin: 0.75rem 0;
    }
    .message-ai {
      animation: slide-in 0.3s ease 0.1s both;
      background: rgba(13,17,23,0.8);
      border: 1px solid rgba(0,245,212,0.15);
      border-radius: 16px 16px 16px 4px;
      padding: 1rem 1.25rem;
      margin: 0.75rem 0;
    }
    .message-label {
      font-family: 'Syne', sans-serif;
      font-size: 0.7rem;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      margin-bottom: 0.5rem;
    }
    .thinking-dots span {
      animation: blink 1.4s infinite;
      font-size: 1.5rem;
    }
    .thinking-dots span:nth-child(2) { animation-delay: 0.2s; }
    .thinking-dots span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes blink {
      0%, 80%, 100% { opacity: 0; }
      40% { opacity: 1; }
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Session state init ────────────────────────────────────────────────────
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "subject" not in st.session_state:
        st.session_state.subject = "⚙️ General / Mixed Subjects"
    if "pending_message" not in st.session_state:
        st.session_state.pending_message = ""
    if "chat_input_widget" not in st.session_state:
        st.session_state.chat_input_widget = ""

    # Callback to handle submission and clear the input box
    def submit_message():
        if st.session_state.chat_input_widget.strip():
            st.session_state.pending_message = st.session_state.chat_input_widget
        # Clear the input box immediately
        st.session_state.chat_input_widget = ""

    # ── API Key check ─────────────────────────────────────────────────────────
    model_instance = get_client()
    if not model_instance:
        st.markdown("""
        <div style="background:rgba(255,107,107,0.1);border:1px solid rgba(255,107,107,0.3);
                    border-radius:16px;padding:1.25rem;margin:1rem 0;">
          <div style="color:#ff6b6b;font-family:'Syne',sans-serif;font-weight:700;margin-bottom:0.5rem;">
            🔑 Google API Key Required
          </div>
          <div style="color:#9ca3af;font-size:0.9rem;">
            Enter your Google API key in the sidebar to start chatting.
          </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.sidebar:
            st.markdown("### 🔑 API Configuration")
            key_input = st.text_input("Google API Key", type="password", 
                                       placeholder="AIza...",
                                       key="google_key_input")
            if key_input:
                st.session_state.google_key = key_input
                st.rerun()
        return

    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        subject = st.selectbox(
            "Subject Area",
            list(SUBJECT_PROMPTS.keys()),
            index=list(SUBJECT_PROMPTS.keys()).index(st.session_state.subject),
            label_visibility="collapsed"
        )
        st.session_state.subject = subject
    with col2:
        if st.button("🗑️ Clear Chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with col3:
        if st.button("📤 Export", use_container_width=True):
            if st.session_state.messages:
                export_text = "\n\n".join([
                    f"{'YOU' if m['role']=='user' else 'ADD AI'}: {m['content']}"
                    for m in st.session_state.messages
                ])
                st.download_button("💾 Download", export_text, "chat_export.txt", "text/plain")

    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.messages:
            st.markdown("""
            <div style="text-align:center;padding:3rem 1rem;opacity:0.8;">
              <div style="font-size:4rem;animation:float 3s ease-in-out infinite;display:block;
                          margin-bottom:1rem;">🧠</div>
              <div style="font-family:'Syne',sans-serif;font-size:1.3rem;font-weight:700;
                          color:#e8eaf6;margin-bottom:0.5rem;">Ready to help you excel</div>
              <div style="color:#6b7280;font-size:0.9rem;margin-bottom:2rem;">
                Ask anything academic — or upload your files below
              </div>
            </div>
            
            <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));
                        gap:0.75rem;margin-bottom:1rem;">
            """, unsafe_allow_html=True)
            
            examples = [
                ("📐", "Solve this integral step by step: ∫x²eˣ dx"),
                ("💻", "Debug my Python code and explain the errors"),
                ("📝", "Help me write a thesis statement for my essay"),
                ("⚗️", "Balance this chemical equation and explain it"),
                ("📊", "Explain supply and demand with an example"),
                ("🌍", "Summarize causes of World War II for my exam"),
            ]
            
            cols = st.columns(3)
            for i, (icon, text) in enumerate(examples):
                with cols[i % 3]:
                    if st.button(f"{icon} {text[:40]}...", key=f"ex_{i}", use_container_width=True):
                        st.session_state.pending_message = text
                        st.rerun()
        
        else:
            for msg in st.session_state.messages:
                if msg["role"] == "user":
                    st.markdown(f"""
                    <div class="message-user">
                      <div class="message-label" style="color:#7b61ff;">You</div>
                      <div style="color:#e8eaf6;line-height:1.6;">{msg["content"]}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="message-ai">
                      <div class="message-label" style="color:#00f5d4;">⚡ Add AI</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(msg["content"])

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("""
        <div style="background:rgba(13,17,23,0.9);border:1px solid rgba(0,245,212,0.15);
                    border-radius:20px;padding:1rem;backdrop-filter:blur(20px);">
        """, unsafe_allow_html=True)
        
        uploaded = st.file_uploader(
            "📎 Attach files",
            accept_multiple_files=True,
            type=["pdf","png","jpg","jpeg","gif","webp","txt","py","js","ts","html","css",
                  "csv","json","xml","md","docx","xlsx","cpp","c","java","rs","go","rb"],
            key="file_uploader",
            label_visibility="collapsed"
        )
        
        col_input, col_send = st.columns([6, 1])
        with col_input:
            st.text_area(
                "Message",
                placeholder="Ask anything... (Press Enter to send, Shift+Enter for new line)",
                height=100,
                label_visibility="collapsed",
                key="chat_input_widget"
            )
        with col_send:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            st.button("Send ➤", use_container_width=True, key="send_btn", on_click=submit_message)
        
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Custom JS for Enter to Submit ─────────────────────────────────────────
    # This captures the Enter key (without Shift) and triggers the Send button.
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
                if (sendBtn) {
                    sendBtn.click();
                }
            }
        });
    }
    </script>
    """
    components.html(js_code, height=0, width=0)

    # Process any pending messages that were submitted
    if st.session_state.pending_message:
        user_input = st.session_state.pending_message
        st.session_state.pending_message = "" # reset
        
        st.session_state.messages.append({"role": "user", "content": user_input.strip()})
        
        with st.spinner(""):
            st.markdown("""
            <div class="message-ai">
              <div class="message-label" style="color:#00f5d4;">⚡ Add AI — thinking</div>
              <div class="thinking-dots"><span>●</span><span>●</span><span>●</span></div>
            </div>
            """, unsafe_allow_html=True)
            
            full_system = f"{SYSTEM_BASE}\n\n{SUBJECT_PROMPTS.get(subject, '')}"
            
            # Use original variables and UI flow.
            try:
                # We do not overwrite the top definition of genai.GenerativeModel
                # within the try block to ensure we can catch the error specifically.
                
                parts = [user_input.strip()]
                if uploaded:
                    for f in uploaded:
                        parts.append(encode_file(f))

                # Changed to gemini-2.0-flash for ultra-fast performance
                model = genai.GenerativeModel(
                    model_name='gemini-2.0-flash', 
                    system_instruction=full_system
                )
                
                # --- хірургія ---
                # Detect if files are uploaded. Multi-modal requires Gemini. Text-only can use fallback.
                has_files = bool(uploaded)
                
                if has_files:
                    # Original logic for multi-modal, letting exceptions (like 429) catch normally
                    history = []
                    for m in st.session_state.messages[:-1]:
                        role = "model" if m["role"] == "assistant" else "user"
                        history.append({"role": role, "parts": [m["content"]]})
                    
                    chat = model.start_chat(history=history)
                    response = chat.send_message(parts)
                    final_response_text = response.text
                else:
                    # Text-only path: Attempt Gemini, if 429 hits, use backup brain logic.
                    try:
                        history = []
                        for m in st.session_state.messages[:-1]:
                            role = "model" if m["role"] == "assistant" else "user"
                            history.append({"role": role, "parts": [m["content"]]})
                        
                        chat = model.start_chat(history=history)
                        # parts[0] is guaranteed to be the user text strip based on logic above
                        response = chat.send_message(parts[0]) 
                        final_response_text = response.text
                    except Exception as chat_error:
                        # Catch quota/rate limit error specifically
                        err_str = str(chat_error)
                        if "429" in err_str or "Quota exceeded" in err_str or "Invalid" in err_str or "400" in err_str:
                            # Construct combined prompt for text-only fallback to maintain context
                            text_history = ""
                            for m in st.session_state.messages[:-1]:
                                rl = "Add AI" if m["role"] == "assistant" else "You"
                                text_history += f"{rl}: {m['content']}\n\n"
                            
                            combined_prompt = f"{full_system}\n\n{text_history}You: {user_input.strip()}"
                            
                            # Using 'mistral' model for extremely fast 1-2 second response times
                            fallback_url = f"https://text.pollinations.ai/prompt/{quote(combined_prompt)}?model=mistral"
                            # Reduced timeout to ensure instant fallback execution
                            resp = requests.get(fallback_url, timeout=5) 
                            if resp.status_code == 200:
                                final_response_text = resp.text.strip()
                            else:
                                final_response_text = "⚠️ Free Tier limit reached and backup Brain unavailable. Try again in a moment."
                        else:
                            # Re-raise non-quota errors to be caught by outer try
                            raise chat_error
                # --- конец хирургии ---
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": final_response_text
                })
            except Exception as e:
                # Outer catch handles Gemini errors if files present, safety blocks, or fallback API failures.
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"⚠️ Error: {str(e)}"
                })
        
        st.rerun()
    
    with st.sidebar:
        st.markdown("---")
        st.markdown("### ⚙️ Settings")
        key_input = st.text_input("Google API Key", type="password",
                                   value=st.session_state.get("google_key", ""),
                                   key="google_key_sidebar")
        if key_input:
            st.session_state.google_key = key_input

# Note: If your app routing uses `render()`, keep this block. If not, remove it.
if __name__ == "__main__":
    render()
