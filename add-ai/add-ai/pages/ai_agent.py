import streamlit as st
import io
import re
import math
import json
import time
import random
from collections import defaultdict, Counter

# Optional file-parsing libs — graceful fallback if missing
try:
    from pypdf import PdfReader
    HAS_PDF = True
except ImportError:
    try:
        import PyPDF2 as pypdf2_mod
        HAS_PDF = "pypdf2"
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
#  IDENTITY
# ════════════════════════════════════════════════════════════════

APP_NAME    = "Add AI"
CREATOR     = "Huzaifa Baig"
VERSION     = "2.0 Autonomous"
IDENTITY_KEYWORDS = {"who are you","what are you","your name","who made you",
                     "who created you","your creator","introduce yourself","about you"}

SUBJECT_PROMPTS = {
    "🔬 Science & Engineering": "scientific",
    "📐 Mathematics":           "mathematical",
    "📚 Literature & Humanities": "literary",
    "💻 Computer Science":      "technical",
    "🏛️ History & Social Studies": "historical",
    "🧪 Chemistry":             "chemistry",
    "⚕️ Biology & Medicine":    "biology",
    "📊 Economics & Business":  "economic",
    "🌍 Geography":             "geographic",
    "🎨 Arts & Design":         "artistic",
    "🔤 Languages":             "linguistic",
    "⚙️ General / Mixed":       "general",
}

# ════════════════════════════════════════════════════════════════
#  FILE EXTRACTION ENGINE
# ════════════════════════════════════════════════════════════════

def extract_text(uploaded_file) -> str:
    """Extract all readable text from any uploaded file type."""
    name = uploaded_file.name
    ext  = name.rsplit(".", 1)[-1].lower()
    raw  = uploaded_file.read()
    uploaded_file.seek(0)
    result = ""

    # ── PDF ──────────────────────────────────────────────────────
    if ext == "pdf":
        if HAS_PDF is True:
            try:
                reader = PdfReader(io.BytesIO(raw))
                pages  = []
                for i, page in enumerate(reader.pages):
                    t = page.extract_text() or ""
                    if t.strip():
                        pages.append(f"[Page {i+1}]\n{t}")
                result = "\n\n".join(pages)
            except Exception as e:
                result = f"[PDF parse error: {e}]"
        elif HAS_PDF == "pypdf2":
            try:
                reader = pypdf2_mod.PdfReader(io.BytesIO(raw))
                result = "\n".join(page.extract_text() or "" for page in reader.pages)
            except Exception as e:
                result = f"[PDF parse error: {e}]"
        else:
            result = "[pypdf not installed — install it via requirements.txt]"

    # ── Word Doc ─────────────────────────────────────────────────
    elif ext in ("docx", "doc"):
        if HAS_DOCX:
            try:
                doc    = python_docx.Document(io.BytesIO(raw))
                result = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            except Exception as e:
                result = f"[DOCX parse error: {e}]"
        else:
            result = "[python-docx not installed]"

    # ── Spreadsheet ──────────────────────────────────────────────
    elif ext in ("csv", "xlsx", "xls"):
        if HAS_PANDAS:
            try:
                df = pd.read_csv(io.BytesIO(raw)) if ext == "csv" else pd.read_excel(io.BytesIO(raw))
                result = f"[Spreadsheet: {df.shape[0]} rows × {df.shape[1]} cols]\n"
                result += f"Columns: {', '.join(str(c) for c in df.columns)}\n\n"
                result += df.to_string(index=False, max_rows=200)
            except Exception as e:
                result = f"[Spreadsheet parse error: {e}]"
        else:
            result = "[pandas not installed]"

    # ── Plain text / code / markdown ─────────────────────────────
    else:
        try:
            result = raw.decode("utf-8", errors="ignore")
        except Exception:
            result = "[Could not decode file]"

    return f"===FILE: {name}===\n{result.strip()}\n===END: {name}==="


# ════════════════════════════════════════════════════════════════
#  DOCUMENT INTELLIGENCE ENGINE
# ════════════════════════════════════════════════════════════════

STOP_WORDS = {
    "a","an","the","is","it","in","on","at","to","of","and","or","for",
    "with","this","that","are","was","were","be","been","has","have",
    "had","do","does","did","will","would","could","should","may","might",
    "as","by","from","up","about","into","through","what","which","who",
    "whom","how","when","where","why","not","but","if","so","can","get",
    "i","you","he","she","we","they","me","him","her","us","them","my",
    "your","his","its","our","their","more","also","some","any","all",
    "than","then","just","been","now","only","very","make","new","most"
}

def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9]+(?:[''][a-zA-Z]+)?", text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]

def split_sentences(text: str) -> list[str]:
    """Split text into clean sentences."""
    sentences = re.split(r'(?<=[.!?])\s+|\n{2,}', text)
    out = []
    for s in sentences:
        s = s.strip()
        if len(s) > 20:
            out.append(s)
    return out

def split_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs."""
    paras = re.split(r'\n{2,}|\[Page \d+\]', text)
    return [p.strip() for p in paras if len(p.strip()) > 40]

def build_tfidf_index(documents: list[str]) -> tuple[list[list[str]], dict]:
    """
    Build a TF-IDF index over a list of text chunks.
    Returns: (tokenized_docs, idf_dict)
    """
    tokenized = [tokenize(doc) for doc in documents]
    N = len(documents)
    df = defaultdict(int)
    for tokens in tokenized:
        for word in set(tokens):
            df[word] += 1
    idf = {word: math.log((N + 1) / (count + 1)) + 1 for word, count in df.items()}
    return tokenized, idf

def tfidf_score(query_tokens: list[str], doc_tokens: list[str], idf: dict) -> float:
    """Compute TF-IDF cosine similarity between query and doc."""
    if not doc_tokens:
        return 0.0
    tf = Counter(doc_tokens)
    doc_len = len(doc_tokens)

    query_vec  = {}
    doc_vec    = {}

    all_terms = set(query_tokens) | set(doc_tokens)
    for term in all_terms:
        idf_val = idf.get(term, 1.0)
        query_vec[term] = (query_tokens.count(term) / max(len(query_tokens), 1)) * idf_val
        doc_vec[term]   = (tf.get(term, 0) / doc_len) * idf_val

    dot   = sum(query_vec[t] * doc_vec[t] for t in all_terms)
    norm_q = math.sqrt(sum(v**2 for v in query_vec.values())) or 1
    norm_d = math.sqrt(sum(v**2 for v in doc_vec.values())) or 1
    return dot / (norm_q * norm_d)

def proximity_bonus(query_tokens: list[str], chunk: str) -> float:
    """Bonus score when query terms appear close together in the chunk."""
    chunk_lower = chunk.lower()
    positions   = {}
    words = chunk_lower.split()
    for i, w in enumerate(words):
        w_clean = re.sub(r'[^a-z0-9]', '', w)
        for qt in query_tokens:
            if qt == w_clean or qt in w_clean:
                positions.setdefault(qt, []).append(i)
    if len(positions) < 2:
        return 0.0
    # Average distance between matched terms
    all_pos = [p for ps in positions.values() for p in ps]
    if len(all_pos) < 2:
        return 0.0
    avg_dist = sum(abs(all_pos[i]-all_pos[i-1]) for i in range(1, len(all_pos))) / len(all_pos)
    return max(0, 1.0 - avg_dist / 50.0)

def retrieve_best_chunks(query: str, file_texts: list[str], top_k: int = 6) -> list[str]:
    """
    Core retrieval: finds the most relevant passages from all uploaded files
    using TF-IDF + proximity scoring.
    """
    if not file_texts:
        return []

    # Build paragraph-level chunks from all files
    all_chunks = []
    for ft in file_texts:
        paras = split_paragraphs(ft)
        all_chunks.extend(paras)

    # Also add sentence-level chunks for precision
    for ft in file_texts:
        sents = split_sentences(ft)
        # Group sentences into windows of 3
        for i in range(0, len(sents), 2):
            group = " ".join(sents[i:i+3])
            if len(group) > 60:
                all_chunks.append(group)

    if not all_chunks:
        return []

    query_tokens = tokenize(query)
    if not query_tokens:
        return all_chunks[:top_k]

    tokenized_chunks, idf = build_tfidf_index(all_chunks)

    scored = []
    for i, (chunk, tokens) in enumerate(zip(all_chunks, tokenized_chunks)):
        base_score = tfidf_score(query_tokens, tokens, idf)
        prox       = proximity_bonus(query_tokens, chunk)
        # Boost longer chunks slightly
        length_bonus = min(len(chunk) / 3000, 0.1)
        total = base_score + 0.3 * prox + length_bonus
        scored.append((total, i, chunk))

    scored.sort(key=lambda x: -x[0])

    # Deduplicate near-identical chunks
    seen    = set()
    results = []
    for score, idx, chunk in scored:
        if score < 0.001:
            break
        sig = chunk[:80].lower()
        if sig not in seen:
            seen.add(sig)
            results.append(chunk)
        if len(results) >= top_k:
            break

    return results


# ════════════════════════════════════════════════════════════════
#  ANSWER SYNTHESIS ENGINE
# ════════════════════════════════════════════════════════════════

def detect_question_type(query: str) -> str:
    q = query.lower()
    if re.search(r'\bwhat\s+is\b|\bdefine\b|\bmeaning\b|\bexplain\b|\bdescribe\b', q):
        return "definition"
    if re.search(r'\bhow\b|\bsteps?\b|\bprocess\b|\bprocedure\b', q):
        return "process"
    if re.search(r'\bwhy\b|\breason\b|\bcause\b|\beffect\b', q):
        return "reasoning"
    if re.search(r'\blist\b|\bname\b|\bexamples?\b|\btypes?\b|\bkinds?\b', q):
        return "listing"
    if re.search(r'\bcompare\b|\bdifference\b|\bsimilar\b|\bvs\b', q):
        return "comparison"
    if re.search(r'\bsummari[sz]e\b|\boverview\b|\bbriefly\b|\bshort\b', q):
        return "summary"
    if re.search(r'\bsolve\b|\bcalculate\b|\bcompute\b|\bfind\b|\bmath\b|\bequation\b', q):
        return "math"
    if re.search(r'\bcode\b|\bprogram\b|\bfunction\b|\bscript\b|\bwrite.*code\b', q):
        return "code"
    return "general"

def extract_key_sentences(chunks: list[str], query_tokens: list[str], max_chars: int = 2400) -> str:
    """
    From retrieved chunks, pull the most relevant sentences
    and assemble a clean context block.
    """
    all_sentences = []
    for chunk in chunks:
        sents = split_sentences(chunk)
        for s in sents:
            tokens = tokenize(s)
            overlap = len(set(tokens) & set(query_tokens))
            if overlap > 0:
                all_sentences.append((overlap, s))

    # Sort by relevance, deduplicate
    all_sentences.sort(key=lambda x: -x[0])
    seen = set()
    selected = []
    total_chars = 0
    for score, sent in all_sentences:
        sig = sent[:60].lower()
        if sig not in seen and total_chars + len(sent) < max_chars:
            seen.add(sig)
            selected.append(sent)
            total_chars += len(sent)

    # If nothing matched well, fall back to raw chunks
    if not selected:
        raw = " ".join(chunks[:3])
        return raw[:max_chars]

    return " ".join(selected)

def synthesize_answer(query: str, chunks: list[str], subject: str, file_names: list[str]) -> str:
    """
    Build a structured, intelligent answer from retrieved chunks.
    No external API. Pure logic-based synthesis.
    """
    if not chunks:
        return (
            f"❌ **Not found in your uploaded files.**\n\n"
            f"I searched all {len(file_names)} file(s) but couldn't find relevant information about:\n"
            f"> *\"{query}\"*\n\n"
            f"**Suggestions:**\n"
            f"- Make sure the file contains information about this topic\n"
            f"- Try rephrasing your question with keywords from the document\n"
            f"- Check that the file uploaded correctly (try re-uploading)"
        )

    q_type    = detect_question_type(query)
    q_tokens  = tokenize(query)
    context   = extract_key_sentences(chunks, q_tokens)
    full_text = " ".join(chunks)

    # ── Build file attribution ────────────────────────────────────
    source_note = f"*📄 Source: {', '.join(file_names)}*" if file_names else ""

    # ── Response header ───────────────────────────────────────────
    answer = f"## 📘 Answer from Your Study Material\n\n{source_note}\n\n"

    # ── Type-specific formatting ──────────────────────────────────
    if q_type == "definition":
        answer += f"### Definition / Explanation\n\n{context}\n\n"

        # Try to find additional sentences with subject terms
        bonus = []
        for sent in split_sentences(full_text):
            if any(t in sent.lower() for t in q_tokens[:3]):
                if sent not in context:
                    bonus.append(f"- {sent}")
                if len(bonus) >= 3:
                    break
        if bonus:
            answer += "**Additional context:**\n" + "\n".join(bonus) + "\n\n"

    elif q_type == "process":
        answer += "### Step-by-Step Process\n\n"
        sents = split_sentences(context)
        # Try to number steps
        step_sents = [s for s in sents if len(s) > 25]
        if step_sents:
            for i, s in enumerate(step_sents[:8], 1):
                answer += f"**Step {i}:** {s}\n\n"
        else:
            answer += context + "\n\n"

    elif q_type == "reasoning":
        answer += f"### Reasoning & Explanation\n\n{context}\n\n"
        # Look for cause/effect keywords in full text
        cause_sents = [s for s in split_sentences(full_text)
                       if re.search(r'because|therefore|thus|hence|result|cause|effect|due to|leads to', s.lower())
                       and any(t in s.lower() for t in q_tokens[:4])]
        if cause_sents:
            answer += "**Cause & Effect:**\n"
            for s in cause_sents[:3]:
                answer += f"- {s}\n"
            answer += "\n"

    elif q_type == "listing":
        answer += "### Key Points\n\n"
        items = re.findall(r'(?:^|\n)[•\-\*\d+\.]\s*(.+)', full_text)
        if items:
            for item in items[:10]:
                answer += f"- {item.strip()}\n"
            answer += "\n"
        else:
            sents = split_sentences(context)
            for s in sents[:6]:
                answer += f"- {s}\n"
            answer += "\n"

    elif q_type == "comparison":
        answer += f"### Comparison\n\n{context}\n\n"
        # Find comparative sentences
        comp_sents = [s for s in split_sentences(full_text)
                      if re.search(r'while|whereas|however|but|unlike|similar|differ|both|on the other hand', s.lower())
                      and any(t in s.lower() for t in q_tokens[:4])]
        if comp_sents:
            answer += "**Key differences/similarities:**\n"
            for s in comp_sents[:3]:
                answer += f"- {s}\n"
            answer += "\n"

    elif q_type == "summary":
        answer += "### Summary\n\n"
        # Take first few and last few relevant sentences for a summary
        sents = split_sentences(context)
        if len(sents) > 4:
            summary_sents = sents[:2] + ["..."] + sents[-2:]
            answer += " ".join(summary_sents) + "\n\n"
        else:
            answer += context + "\n\n"

    elif q_type == "math":
        answer += "### Mathematical Working\n\n"
        # Look for equations/numbers in context
        equations = re.findall(r'[A-Za-z0-9\+\-\*/=\^\(\)]+\s*=\s*[A-Za-z0-9\+\-\*/\^\(\)\s]+', full_text)
        if equations:
            answer += "**Relevant equations found in your material:**\n"
            for eq in equations[:5]:
                answer += f"```\n{eq.strip()}\n```\n"
            answer += "\n"
        answer += context + "\n\n"

    elif q_type == "code":
        answer += "### Code from Your Material\n\n"
        code_blocks = re.findall(r'```[\s\S]*?```|`[^`]+`', full_text)
        if code_blocks:
            for cb in code_blocks[:3]:
                answer += cb + "\n\n"
        answer += context + "\n\n"

    else:  # general
        answer += context + "\n\n"

    # ── Always append relevant raw chunk if answer is thin ────────
    if len(answer) < 300 and chunks:
        answer += f"\n**Full relevant passage:**\n\n{chunks[0][:600]}\n"

    # ── Footer ────────────────────────────────────────────────────
    answer += f"\n---\n*💡 This answer was extracted directly from your uploaded material by Add AI v{VERSION}.*"
    return answer.strip()


# ════════════════════════════════════════════════════════════════
#  GENERAL KNOWLEDGE ENGINE (no file uploaded)
# ════════════════════════════════════════════════════════════════

GENERAL_KNOWLEDGE = {
    "photosynthesis": "Photosynthesis is the process by which green plants, algae, and some bacteria convert light energy (usually from the sun) into chemical energy stored as glucose. The equation is: 6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂. It occurs in the chloroplasts and has two stages: light-dependent reactions and the Calvin cycle (light-independent).",
    "newton": "Newton's Three Laws of Motion: 1) An object at rest stays at rest, and an object in motion stays in motion unless acted upon by an external force. 2) Force = Mass × Acceleration (F=ma). 3) For every action, there is an equal and opposite reaction.",
    "pythagoras": "The Pythagorean theorem states that in a right-angled triangle, the square of the hypotenuse (c) equals the sum of squares of the other two sides: a² + b² = c².",
    "cell": "A cell is the basic structural and functional unit of all living organisms. There are two types: prokaryotic (no nucleus, e.g. bacteria) and eukaryotic (has nucleus, e.g. human cells). Key organelles include the nucleus, mitochondria, ribosomes, and cell membrane.",
    "world war": "World War II (1939-1945) was a global conflict primarily between the Allies (USA, UK, USSR, France) and the Axis powers (Germany, Italy, Japan). It started with Germany's invasion of Poland and ended with the surrender of Germany (May 1945) and Japan (September 1945) after atomic bombs were dropped on Hiroshima and Nagasaki.",
    "democracy": "Democracy is a system of government where power is vested in the people, who rule either directly or through freely elected representatives. Key principles include free elections, rule of law, protection of civil liberties, and separation of powers.",
    "gravity": "Gravity is a fundamental force of attraction between all objects with mass. Newton's law of gravitation: F = Gm₁m₂/r². Einstein's General Relativity describes gravity as the curvature of spacetime caused by mass and energy.",
    "supply demand": "The law of supply states that as price increases, quantity supplied increases. The law of demand states that as price increases, quantity demanded decreases. The equilibrium price is where supply and demand curves intersect.",
    "dna": "DNA (Deoxyribonucleic acid) is a double-helix molecule that carries genetic information. It is made of nucleotides containing a sugar, phosphate group, and one of four bases: Adenine, Thymine, Guanine, Cytosine. A pairs with T, and G pairs with C.",
    "mitosis": "Mitosis is cell division producing two identical daughter cells. Stages: Prophase (chromosomes condense), Metaphase (align at center), Anaphase (chromosomes pull apart), Telophase (two nuclei form), Cytokinesis (cell splits).",
    "algorithm": "An algorithm is a step-by-step procedure to solve a problem or accomplish a task. Key properties: input, output, definiteness, finiteness, and effectiveness. Common examples: sorting (bubble, merge, quick sort), searching (binary search), graph algorithms (Dijkstra's).",
    "french revolution": "The French Revolution (1789-1799) was a period of radical political change in France. Causes include financial crisis, social inequality, and Enlightenment ideas. Key events: Storming of the Bastille (1789), Declaration of the Rights of Man, execution of King Louis XVI, Reign of Terror, and rise of Napoleon Bonaparte.",
}

def general_knowledge_answer(query: str, subject: str) -> str:
    """Answer common academic questions from a built-in knowledge base."""
    q_lower = query.lower()
    q_tokens = tokenize(query)

    best_key   = None
    best_score = 0

    for key, answer in GENERAL_KNOWLEDGE.items():
        key_tokens = tokenize(key)
        overlap = len(set(q_tokens) & set(key_tokens))
        # Also check raw substring
        if key in q_lower or any(k in q_lower for k in key.split()):
            overlap += 3
        if overlap > best_score:
            best_score = overlap
            best_key   = key

    if best_key and best_score >= 1:
        return (
            f"## 📚 Add AI — Academic Knowledge\n\n"
            f"*No file uploaded — answering from built-in knowledge base.*\n\n"
            f"### {query.strip().capitalize()}\n\n"
            f"{GENERAL_KNOWLEDGE[best_key]}\n\n"
            f"---\n*💡 Upload a study file to get answers directly from your material.*"
        )

    # Fallback: generic helpful response
    domain = SUBJECT_PROMPTS.get(subject, "general")
    return (
        f"## 📚 Add AI — {subject}\n\n"
        f"Your question: **\"{query}\"**\n\n"
        f"I don't have specific built-in knowledge for this exact topic, but here's what I suggest:\n\n"
        f"**To get the best answer:**\n"
        f"- 📎 Upload your textbook, notes, or study material (PDF, DOCX, TXT)\n"
        f"- I will extract and analyze the content to answer your question precisely\n"
        f"- I can handle up to 10 files simultaneously\n\n"
        f"**Topics I have built-in knowledge for:**\n"
        f"- Photosynthesis, Newton's Laws, Pythagorean theorem\n"
        f"- DNA, Cell biology, Mitosis\n"
        f"- World War II, French Revolution, Democracy\n"
        f"- Supply & Demand, Algorithms, Gravity\n\n"
        f"---\n*Add AI v{VERSION} — Fully autonomous, no external AI required.*"
    )


# ════════════════════════════════════════════════════════════════
#  MAIN BRAIN ROUTER
# ════════════════════════════════════════════════════════════════

def add_ai_brain(query: str, file_texts: list[str], file_names: list[str], subject: str) -> str:
    """
    Central intelligence router.
    Priority: identity → file analysis → general knowledge
    """
    q_lower = query.lower().strip()

    # ── Identity questions ────────────────────────────────────────
    if any(phrase in q_lower for phrase in IDENTITY_KEYWORDS):
        return (
            f"## 🤖 I'm {APP_NAME}\n\n"
            f"**Created by:** {CREATOR}\n"
            f"**Version:** {VERSION}\n\n"
            f"I am a **fully autonomous AI academic assistant** — I operate independently "
            f"with no external AI engines, no APIs, and no internet dependency.\n\n"
            f"**My capabilities:**\n"
            f"- 📎 Analyze uploaded files (PDF, DOCX, TXT, CSV, images)\n"
            f"- 📚 Answer questions from your study material\n"
            f"- 🧠 Built-in academic knowledge base\n"
            f"- 💡 Support all academic subjects\n"
            f"- ⚡ Works completely offline after deployment\n\n"
            f"Upload your study material and ask me anything!"
        )

    # ── File-based answering ──────────────────────────────────────
    if file_texts:
        chunks = retrieve_best_chunks(query, file_texts, top_k=6)
        return synthesize_answer(query, chunks, subject, file_names)

    # ── General knowledge fallback ────────────────────────────────
    return general_knowledge_answer(query, subject)


# ════════════════════════════════════════════════════════════════
#  STREAMLIT UI
# ════════════════════════════════════════════════════════════════

def render():

    # ── CSS ───────────────────────────────────────────────────────
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
    @keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
    @keyframes slide-in{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
    @keyframes blink{0%,80%,100%{opacity:0}40%{opacity:1}}
    @keyframes shimmer{0%{background-position:-200% center}100%{background-position:200% center}}
    @keyframes pulse{0%,100%{opacity:1}50%{opacity:.5}}

    .msg-user{
      animation:slide-in .28s ease;
      background:linear-gradient(135deg,rgba(123,97,255,.13),rgba(0,245,212,.07));
      border:1px solid rgba(123,97,255,.28);
      border-radius:16px 16px 4px 16px;
      padding:1rem 1.25rem;margin:.55rem 0;
    }
    .msg-ai{
      animation:slide-in .32s ease .06s both;
      background:rgba(13,17,23,.88);
      border:1px solid rgba(0,245,212,.18);
      border-radius:16px 16px 16px 4px;
      padding:1rem 1.25rem;margin:.55rem 0;
    }
    .msg-label{
      font-family:'Syne',sans-serif;font-size:.66rem;
      font-weight:700;letter-spacing:.13em;
      text-transform:uppercase;margin-bottom:.4rem;
    }
    .thinking span{animation:blink 1.2s infinite;font-size:1.3rem;}
    .thinking span:nth-child(2){animation-delay:.22s}
    .thinking span:nth-child(3){animation-delay:.44s}
    .shimmer-bar{
      height:2px;border-radius:2px;
      background:linear-gradient(90deg,#00f5d4,#7b61ff,#ff6b6b,#00f5d4);
      background-size:200% auto;animation:shimmer 1.4s linear infinite;margin:.4rem 0 .8rem;
    }
    .autonomous-badge{
      display:inline-block;
      background:linear-gradient(90deg,rgba(0,245,212,.1),rgba(123,97,255,.1));
      border:1px solid rgba(0,245,212,.25);
      border-radius:100px;padding:.28rem .85rem;
      font-size:.7rem;color:#00f5d4;letter-spacing:.09em;
      font-family:'Syne',sans-serif;font-weight:700;
    }
    .file-pill{
      display:inline-block;
      background:rgba(0,245,212,.09);
      border:1px solid rgba(0,245,212,.22);
      border-radius:100px;padding:.14rem .55rem;
      font-size:.7rem;color:#00f5d4;margin:.15rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # ── Header ────────────────────────────────────────────────────
    st.markdown(f"""
    <div style="text-align:center;padding:1.8rem 0 .9rem;">
      <div style="margin-bottom:.8rem;">
        <span class="autonomous-badge">⚡ Fully Autonomous Core · No External AI · Created by {CREATOR}</span>
      </div>
      <h1 style="font-family:'Syne',sans-serif;font-size:clamp(1.8rem,4.5vw,3rem);
                 font-weight:800;line-height:1.1;margin-bottom:.5rem;">
        <span style="background:linear-gradient(135deg,#e8eaf6,#fff);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
          Your Academic
        </span><br>
        <span style="background:linear-gradient(135deg,#00f5d4,#7b61ff,#ff6b6b);
                     -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
          Super-Intelligence
        </span>
      </h1>
      <p style="color:#6b7280;font-size:.95rem;max-width:460px;margin:0 auto;">
        Upload your study material · Ask anything · Get instant answers
      </p>
    </div>
    """, unsafe_allow_html=True)

    # ── Session state ─────────────────────────────────────────────
    if "messages"        not in st.session_state: st.session_state.messages = []
    if "subject"         not in st.session_state: st.session_state.subject  = "⚙️ General / Mixed"
    if "pending_message" not in st.session_state: st.session_state.pending_message = ""
    if "chat_input_key"  not in st.session_state: st.session_state.chat_input_key  = 0
    if "stored_files"    not in st.session_state: st.session_state.stored_files = []

    # ── Controls ──────────────────────────────────────────────────
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        subject = st.selectbox("Subject", list(SUBJECT_PROMPTS.keys()),
                               label_visibility="collapsed")
        st.session_state.subject = subject
    with c2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    with c3:
        if st.button("📤 Export", use_container_width=True) and st.session_state.messages:
            txt = "\n\n".join([
                f"{'YOU' if m['role']=='user' else 'ADD AI'}: {m['content']}"
                for m in st.session_state.messages
            ])
            st.download_button("💾 Save", txt, "add_ai_chat.txt", "text/plain")

    # ── File uploader ─────────────────────────────────────────────
    uploaded = st.file_uploader(
        "📎 Upload study material (PDF, DOCX, TXT, CSV, code — up to 10 files)",
        accept_multiple_files=True,
        type=["pdf","docx","doc","txt","csv","xlsx","xls",
              "py","js","ts","html","css","json","xml","md","cpp","c","java"],
        label_visibility="collapsed",
        key="file_uploader_main"
    )
    if uploaded and len(uploaded) > 10:
        uploaded = uploaded[:10]

    # Show file pills
    if uploaded:
        pills = "".join([f'<span class="file-pill">📄 {f.name}</span>' for f in uploaded])
        st.markdown(f"<div style='margin:.3rem 0 .6rem;'>{pills}</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:rgba(0,245,212,.05);border:1px solid rgba(0,245,212,.12);
                    border-radius:10px;padding:.5rem .85rem;font-size:.78rem;color:#6b7280;
                    margin-bottom:.5rem;">
          ✅ <strong style="color:#00f5d4;">{len(uploaded)} file(s) loaded</strong> —
          Ask me anything about the content above ↑
        </div>
        """, unsafe_allow_html=True)

    # ── Chat history ──────────────────────────────────────────────
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align:center;padding:2rem 1rem 1.2rem;">
          <div style="font-size:3rem;animation:float 3s ease-in-out infinite;display:block;margin-bottom:.6rem;">🧠</div>
          <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;
                      color:#e8eaf6;margin-bottom:.3rem;">Ready to analyze your material</div>
          <div style="color:#6b7280;font-size:.83rem;">Upload files above, or ask a general academic question</div>
        </div>
        """, unsafe_allow_html=True)
        examples = [
            ("📐", "Explain Pythagoras theorem"),
            ("💻", "Summarize the uploaded document"),
            ("📝", "What is the main topic of this file?"),
            ("⚗️", "List all key concepts from the material"),
            ("📊", "Explain supply and demand"),
            ("🌍", "What caused World War II?"),
        ]
        cols = st.columns(3)
        for i, (icon, text) in enumerate(examples):
            with cols[i % 3]:
                if st.button(f"{icon} {text}", key=f"ex_{i}", use_container_width=True):
                    st.session_state.pending_message = text
                    st.rerun()
    else:
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="msg-user">
                  <div class="msg-label" style="color:#7b61ff;">You</div>
                  <div style="color:#e8eaf6;line-height:1.65;">{msg['content']}</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="msg-ai">
                  <div class="msg-label" style="color:#00f5d4;">⚡ Add AI</div>
                </div>""", unsafe_allow_html=True)
                st.markdown(msg["content"])

    # ── Input row ─────────────────────────────────────────────────
    def _submit():
        val = st.session_state.get(f"ci_{st.session_state.chat_input_key}", "").strip()
        if val:
            st.session_state.pending_message = val
            st.session_state.chat_input_key += 1

    ci_col, btn_col = st.columns([6, 1])
    with ci_col:
        st.text_area(
            "Message",
            placeholder="Ask about your uploaded material, or any academic question...",
            height=90,
            label_visibility="collapsed",
            key=f"ci_{st.session_state.chat_input_key}",
            on_change=None
        )
    with btn_col:
        st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
        if st.button("Send ➤", use_container_width=True, on_click=_submit):
            pass  # handled by on_click above

    # ── Process pending ───────────────────────────────────────────
    if st.session_state.pending_message:
        query   = st.session_state.pending_message.strip()
        st.session_state.pending_message = ""
        st.session_state.messages.append({"role": "user", "content": query})

        with st.spinner(""):
            st.markdown("""
            <div class="msg-ai">
              <div class="msg-label" style="color:#00f5d4;">⚡ Add AI — analyzing</div>
              <div class="thinking"><span>●</span><span>●</span><span>●</span></div>
            </div>
            <div class="shimmer-bar"></div>
            """, unsafe_allow_html=True)

            # Extract file content
            file_texts = []
            file_names = []
            for f in (uploaded or []):
                try:
                    text = extract_text(f)
                    file_texts.append(text)
                    file_names.append(f.name)
                except Exception as e:
                    st.warning(f"Could not read {f.name}: {e}")

            # Run the brain
            response = add_ai_brain(query, file_texts, file_names, subject)

            st.session_state.messages.append({"role": "assistant", "content": response})

        st.rerun()

    # ── Sidebar info ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"""
        <div style="padding:.85rem;background:rgba(0,245,212,.05);border-radius:12px;
                    border:1px solid rgba(0,245,212,.12);font-size:.78rem;color:#6b7280;">
          <div style="color:#00f5d4;font-family:'Syne',sans-serif;font-weight:700;
                      margin-bottom:.4rem;">⚡ {APP_NAME} Status</div>
          ✅ Autonomous Mode Active<br>
          ✅ No API keys required<br>
          ✅ No external AI engines<br>
          ✅ Works 100% independently<br><br>
          <div style="color:#7b61ff;font-weight:600;">Engine: TF-IDF + Proximity</div>
          <div style="color:#6b7280;margin-top:.2rem;">Created by {CREATOR}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📋 How to Use")
        st.markdown("""
        1. **Upload** your PDF, DOCX, or TXT files
        2. **Select** your subject area
        3. **Ask** any question about the content
        4. Add AI extracts and answers directly from your material
        """)

        st.markdown("### 📁 Supported Files")
        st.markdown("PDF · DOCX · TXT · CSV · XLSX · Python · JavaScript · HTML · JSON · Markdown")


if __name__ == "__main__":
    render()
