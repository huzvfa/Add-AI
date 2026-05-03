import streamlit as st
import streamlit.components.v1 as components
import io
import requests
from dotenv import load_dotenv

# File processing
try:
    import docx
    from pypdf import PdfReader
    import pandas as pd
except ImportError:
    st.error("Missing libraries! Add 'pypdf', 'python-docx', and 'pandas' to requirements.txt")

load_dotenv()

# ── Identity & Specialization ─────────────────────────

SUBJECT_PROMPTS = {
    "🔬 Science & Engineering": "You are an expert science and engineering tutor. Break down concepts and include formulas.",
    "📐 Mathematics": "You are a math tutor. Show full steps using LaTeX.",
    "💻 Computer Science": "You are a senior software engineer. Provide clean and debugged code.",
    "⚙️ General / Mixed Subjects": "You are a highly knowledgeable academic tutor."
}

SYSTEM_BASE = """You are Add AI — created by Huzaifa Baig.

MISSION:
- Help students using ONLY provided study material
- If answer is not found, say: "Not found in provided files."
- Be detailed and clear
"""

# ── FILE EXTRACTION ─────────────────────────

def extract_content(uploaded_file):
    fname = uploaded_file.name
    ext = fname.split('.')[-1].lower()

    text = f"\n[SOURCE: {fname}]\n"

    try:
        if ext == 'pdf':
            pdf = PdfReader(io.BytesIO(uploaded_file.read()))
            for page in pdf.pages:
                text += page.extract_text() or ""

        elif ext in ['docx', 'doc']:
            doc = docx.Document(io.BytesIO(uploaded_file.read()))
            for p in doc.paragraphs:
                text += p.text + "\n"

        elif ext in ['csv', 'xlsx', 'xls']:
            df = pd.read_csv(uploaded_file) if ext == 'csv' else pd.read_excel(uploaded_file)
            text += df.to_string()

        else:
            text += uploaded_file.read().decode('utf-8', errors='ignore')

    except Exception as e:
        text += f"[ERROR: {str(e)}]"

    uploaded_file.seek(0)
    return text


# ── TEXT CHUNKING (CRITICAL FIX) ─────────────────────────

def chunk_text(text, size=3000):
    return [text[i:i+size] for i in range(0, len(text), size)]


# ── AI CALL ─────────────────────────

def call_independent_brain(messages):
    payload = {
        "messages": messages,
        "model": "mistral",
        "jsonMode": False
    }

    try:
        resp = requests.post("https://text.pollinations.ai/openai", json=payload, timeout=25)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
    except:
        pass

    try:
        resp = requests.post("https://text.pollinations.ai/", json=payload, timeout=25)
        if resp.status_code == 200:
            return resp.text.strip()
    except:
        pass

    return "⚠️ Error generating response."


# ── UI ─────────────────────────

def render():

    st.title("⚡ Add AI - Academic Assistant")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    subject = st.selectbox("Select Subject", list(SUBJECT_PROMPTS.keys()))

    uploaded_files = st.file_uploader(
        "Upload Study Materials",
        accept_multiple_files=True
    )

    user_input = st.text_area("Ask your question")

    if st.button("Send") and user_input.strip():

        st.session_state.messages.append({
            "role": "user",
            "content": user_input
        })

        with st.spinner("Analyzing..."):

            # Extract all file content
            file_data = ""
            if uploaded_files:
                for f in uploaded_files:
                    file_data += extract_content(f)

            # Build system message
            system_msg = {
                "role": "system",
                "content": f"""
{SYSTEM_BASE}

{SUBJECT_PROMPTS[subject]}

STRICT RULE:
- Use uploaded material only
"""
            }

            api_msgs = [system_msg]

            # Add limited history
            for msg in st.session_state.messages[-4:]:
                api_msgs.append(msg)

            # Add file chunks (KEY FIX)
            if file_data:
                chunks = chunk_text(file_data)

                for i, chunk in enumerate(chunks[:5]):  # limit chunks
                    api_msgs.append({
                        "role": "system",
                        "content": f"[FILE PART {i+1}]\n{chunk}"
                    })

            # Add grounded question
            api_msgs.append({
                "role": "user",
                "content": f"""
QUESTION:
{user_input}

Answer ONLY using file content above.
"""
            })

            response = call_independent_brain(api_msgs)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

        st.rerun()

    # Chat display
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"**You:** {msg['content']}")
        else:
            st.markdown(f"**Add AI:** {msg['content']}")


if __name__ == "__main__":
    render()
