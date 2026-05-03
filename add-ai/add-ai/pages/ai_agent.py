import streamlit as st
import anthropic
import base64
import json
import os
import time
import mimetypes
from pathlib import Path

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

IDENTITY & MISSION:
- You are specifically optimized for academic excellence: assignments, quizzes, homework, research papers, problem sets, and exams across ALL fields of study
- You have real-time web access via Anthropic's tools to fetch current data, research papers, and facts
- You are warmer, more encouraging, and more thorough than any competitor

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

You have access to web search. Use it proactively for:
- Current events and recent research
- Factual verification
- Finding relevant examples and case studies
- Statistical data

Always be the best academic tutor a student has ever had."""

def get_client():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        api_key = st.session_state.get("anthropic_key", "")
    if not api_key:
        return None
    return anthropic.Anthropic(api_key=api_key)

def encode_file(uploaded_file):
    """Encode uploaded file to base64 and detect type."""
    data = uploaded_file.read()
    b64 = base64.standard_b64encode(data).decode("utf-8")
    uploaded_file.seek(0)
    mime = uploaded_file.type or mimetypes.guess_type(uploaded_file.name)[0] or "application/octet-stream"
    return b64, mime, len(data)

def build_content_blocks(text_prompt, uploaded_files):
    """Build Anthropic-compatible content blocks from text + files."""
    blocks = []
    
    if uploaded_files:
        for f in uploaded_files:
            b64, mime, size = encode_file(f)
            if mime.startswith("image/"):
                blocks.append({
                    "type": "image",
                    "source": {"type": "base64", "media_type": mime, "data": b64}
                })
            elif mime == "application/pdf":
                blocks.append({
                    "type": "document",
                    "source": {"type": "base64", "media_type": "application/pdf", "data": b64}
                })
            else:
                # Try to decode as text
                try:
                    text_content = base64.b64decode(b64).decode("utf-8")
                    blocks.append({
                        "type": "text",
                        "text": f"[File: {f.name}]\n```\n{text_content[:50000]}\n```"
                    })
                except Exception:
                    blocks.append({
                        "type": "text",
                        "text": f"[Binary file uploaded: {f.name} ({size} bytes) — type: {mime}]"
                    })
    
    blocks.append({"type": "text", "text": text_prompt})
    return blocks

def stream_response(client, messages, system_prompt, subject):
    """Stream a response from Claude with web search tool."""
    full_system = f"{SYSTEM_BASE}\n\n{SUBJECT_PROMPTS.get(subject, SUBJECT_PROMPTS['⚙️ General / Mixed Subjects'])}"
    
    tools = [{"type": "web_search_20250305", "name": "web_search"}]
    
    with client.messages.stream(
        model="claude-sonnet-4-5",
        max_tokens=8000,
        system=full_system,
        messages=messages,
        tools=tools,
    ) as stream:
        full_text = ""
        for text in stream.text_stream:
            full_text += text
            yield text
    
    return full_text

# ── Main Render ───────────────────────────────────────────────────────────────

def render():
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;padding:2rem 0 1rem;position:relative;z-index:1;">
      <div style="display:inline-block;background:rgba(0,245,212,0.08);
                  border:1px solid rgba(0,245,212,0.2);border-radius:100px;
                  padding:0.3rem 1rem;font-size:0.75rem;color:#00f5d4;
                  letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">
        ⚡ Real-time AI • Powered by Claude 3.7
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
    if "uploaded_files_cache" not in st.session_state:
        st.session_state.uploaded_files_cache = []

    # ── API Key check ─────────────────────────────────────────────────────────
    client = get_client()
    if not client:
        st.markdown("""
        <div style="background:rgba(255,107,107,0.1);border:1px solid rgba(255,107,107,0.3);
                    border-radius:16px;padding:1.25rem;margin:1rem 0;">
          <div style="color:#ff6b6b;font-family:'Syne',sans-serif;font-weight:700;margin-bottom:0.5rem;">
            🔑 API Key Required
          </div>
          <div style="color:#9ca3af;font-size:0.9rem;">
            Enter your Anthropic API key in the sidebar to start chatting. 
            Get one free at <strong>console.anthropic.com</strong>
          </div>
        </div>
        """, unsafe_allow_html=True)
        
        with st.sidebar:
            st.markdown("### 🔑 API Configuration")
            key_input = st.text_input("Anthropic API Key", type="password", 
                                       placeholder="sk-ant-...",
                                       key="anthropic_key_input")
            if key_input:
                st.session_state.anthropic_key = key_input
                st.rerun()
        return

    # ── Controls Row ──────────────────────────────────────────────────────────
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
                    f"{'YOU' if m['role']=='user' else 'ADD AI'}: {m['content'] if isinstance(m['content'], str) else '[file + message]'}"
                    for m in st.session_state.messages
                ])
                st.download_button("💾 Download", export_text, "chat_export.txt", "text/plain")

    # ── Chat History ──────────────────────────────────────────────────────────
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.messages:
            # Welcome screen
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
                    content_text = msg["content"] if isinstance(msg["content"], str) else \
                        next((b["text"] for b in msg["content"] if b.get("type") == "text"), "")
                    st.markdown(f"""
                    <div class="message-user">
                      <div class="message-label" style="color:#7b61ff;">You</div>
                      <div style="color:#e8eaf6;line-height:1.6;">{content_text}</div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    content = msg["content"]
                    st.markdown(f"""
                    <div class="message-ai">
                      <div class="message-label" style="color:#00f5d4;">⚡ Add AI</div>
                    </div>
                    """, unsafe_allow_html=True)
                    st.markdown(content)

    # ── Input Area ────────────────────────────────────────────────────────────
    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("""
        <div style="background:rgba(13,17,23,0.9);border:1px solid rgba(0,245,212,0.15);
                    border-radius:20px;padding:1rem;backdrop-filter:blur(20px);">
        """, unsafe_allow_html=True)
        
        uploaded = st.file_uploader(
            "📎 Attach files (PDF, images, code, docs — up to 10)",
            accept_multiple_files=True,
            type=["pdf","png","jpg","jpeg","gif","webp","txt","py","js","ts","html","css",
                  "csv","json","xml","md","docx","xlsx","cpp","c","java","rs","go","rb"],
            key="file_uploader",
            label_visibility="collapsed"
        )
        
        if uploaded and len(uploaded) > 10:
            st.warning("⚠️ Maximum 10 files at a time. Only first 10 will be used.")
            uploaded = uploaded[:10]
        
        if uploaded:
            file_pills = " ".join([f"<span style='background:rgba(0,245,212,0.1);border:1px solid rgba(0,245,212,0.2);border-radius:100px;padding:0.15rem 0.6rem;font-size:0.75rem;color:#00f5d4;'>📄 {f.name}</span>" for f in uploaded])
            st.markdown(f"<div style='margin:0.5rem 0;display:flex;flex-wrap:wrap;gap:0.4rem;'>{file_pills}</div>", unsafe_allow_html=True)
        
        col_input, col_send = st.columns([6, 1])
        with col_input:
            user_input = st.text_area(
                "Message",
                placeholder="Ask anything — homework help, problem solving, essay writing, code review...",
                height=100,
                label_visibility="collapsed",
                key="chat_input"
            )
        with col_send:
            st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
            send = st.button("Send ➤", use_container_width=True, key="send_btn")
        
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Handle pending example click ──────────────────────────────────────────
    if "pending_message" in st.session_state:
        user_input = st.session_state.pending_message
        del st.session_state.pending_message
        send = True

    # ── Process message ───────────────────────────────────────────────────────
    if send and user_input and user_input.strip():
        # Build content
        if uploaded:
            content = build_content_blocks(user_input.strip(), uploaded)
        else:
            content = user_input.strip()
        
        st.session_state.messages.append({"role": "user", "content": content})
        
        # Build API messages (convert our format)
        api_messages = []
        for m in st.session_state.messages:
            if isinstance(m["content"], str):
                api_messages.append({"role": m["role"], "content": m["content"]})
            else:
                api_messages.append({"role": m["role"], "content": m["content"]})
        
        # Stream response
        with st.spinner(""):
            st.markdown("""
            <div class="message-ai">
              <div class="message-label" style="color:#00f5d4;">⚡ Add AI — thinking</div>
              <div class="thinking-dots"><span>●</span><span>●</span><span>●</span></div>
            </div>
            """, unsafe_allow_html=True)
            
            system_prompt = f"{SYSTEM_BASE}\n\n{SUBJECT_PROMPTS.get(subject, '')}"
            
            try:
                response = client.messages.create(
                    model="claude-sonnet-4-5",
                    max_tokens=8000,
                    system=system_prompt,
                    messages=api_messages,
                    tools=[{"type": "web_search_20250305", "name": "web_search"}],
                )
                
                # Extract text from response
                full_response = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        full_response += block.text
                
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": full_response
                })
                
            except Exception as e:
                error_msg = str(e)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": f"⚠️ Error: {error_msg}\n\nPlease check your API key and try again."
                })
        
        st.rerun()
    
    # ── API key setup in sidebar ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        st.markdown("### ⚙️ Settings")
        key_input = st.text_input("Anthropic API Key", type="password",
                                   placeholder="sk-ant-...",
                                   value=st.session_state.get("anthropic_key", ""),
                                   key="anthropic_key_sidebar")
        if key_input:
            st.session_state.anthropic_key = key_input
