import streamlit as st
import io
import re
import math
import json
import time
import random
import hashlib
from collections import defaultdict, Counter

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
#  IDENTITY — Add AI is its own engine
# ════════════════════════════════════════════════════════════════

APP_NAME    = "Add AI"
CREATOR     = "Huzaifa Baig"
VERSION     = "3.0 Sovereign"
ENGINE_NAME = "ADDCORE-1"   # Our own engine identity, like GPT-4 or Claude

IDENTITY_KEYWORDS = {
    "who are you","what are you","your name","who made you",
    "who created you","your creator","introduce yourself","about you",
    "what model","which model","are you gpt","are you claude","are you gemini",
    "what ai","which ai","what engine","powered by"
}

# Domain hints (NOT restrictive — agent answers ANYTHING)
DOMAIN_HINTS = {
    "🎓 Study Mode (focus on uploaded files)": "study",
    "💬 General Conversation":                  "general",
    "🔬 Science & Engineering":                 "science",
    "📐 Mathematics":                           "math",
    "📚 Literature & Humanities":               "literature",
    "💻 Computer Science":                      "tech",
    "🏛️ History & Social Studies":              "history",
    "🎨 Creative & Arts":                       "creative",
    "💼 Business & Career":                     "business",
    "🌍 Daily Life & Lifestyle":                "lifestyle",
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

    if ext == "pdf":
        if HAS_PDF is True:
            try:
                reader = PdfReader(io.BytesIO(raw))
                pages = []
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
                result = "\n".join(p.extract_text() or "" for p in reader.pages)
            except Exception as e:
                result = f"[PDF parse error: {e}]"
        else:
            result = "[pypdf not installed]"
    elif ext in ("docx", "doc"):
        if HAS_DOCX:
            try:
                doc = python_docx.Document(io.BytesIO(raw))
                result = "\n".join(p.text for p in doc.paragraphs if p.text.strip())
            except Exception as e:
                result = f"[DOCX parse error: {e}]"
        else:
            result = "[python-docx not installed]"
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
    else:
        try:
            result = raw.decode("utf-8", errors="ignore")
        except Exception:
            result = "[Could not decode file]"

    # Hash for cache invalidation (so re-uploads re-analyze)
    fhash = hashlib.md5(raw).hexdigest()[:8]
    return f"===FILE: {name} [{fhash}]===\n{result.strip()}\n===END==="


# ════════════════════════════════════════════════════════════════
#  TEXT INTELLIGENCE PRIMITIVES
# ════════════════════════════════════════════════════════════════

STOP_WORDS = {
    "a","an","the","is","it","in","on","at","to","of","and","or","for",
    "with","this","that","are","was","were","be","been","has","have",
    "had","do","does","did","will","would","could","should","may","might",
    "as","by","from","up","about","into","through","what","which","who",
    "whom","how","when","where","why","not","but","if","so","can","get",
    "i","you","he","she","we","they","me","him","her","us","them","my",
    "your","his","its","our","their","more","also","some","any","all",
    "than","then","just","now","only","very","make","new","most","tell"
}

def tokenize(text: str) -> list:
    words = re.findall(r"[a-zA-Z0-9]+(?:[''][a-zA-Z]+)?", text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]

def split_sentences(text: str) -> list:
    sentences = re.split(r'(?<=[.!?])\s+|\n{2,}', text)
    return [s.strip() for s in sentences if len(s.strip()) > 20]

def split_paragraphs(text: str) -> list:
    paras = re.split(r'\n{2,}|\[Page \d+\]', text)
    return [p.strip() for p in paras if len(p.strip()) > 40]

def build_tfidf_index(docs):
    tokenized = [tokenize(d) for d in docs]
    N = len(docs)
    df = defaultdict(int)
    for tokens in tokenized:
        for w in set(tokens):
            df[w] += 1
    idf = {w: math.log((N + 1) / (c + 1)) + 1 for w, c in df.items()}
    return tokenized, idf

def tfidf_score(qt, dt, idf):
    if not dt: return 0.0
    tf = Counter(dt)
    dl = len(dt)
    qv, dv = {}, {}
    terms = set(qt) | set(dt)
    for t in terms:
        i = idf.get(t, 1.0)
        qv[t] = (qt.count(t) / max(len(qt), 1)) * i
        dv[t] = (tf.get(t, 0) / dl) * i
    dot = sum(qv[t] * dv[t] for t in terms)
    nq = math.sqrt(sum(v*v for v in qv.values())) or 1
    nd = math.sqrt(sum(v*v for v in dv.values())) or 1
    return dot / (nq * nd)

def proximity_bonus(qt, chunk):
    cl = chunk.lower()
    words = cl.split()
    pos = {}
    for i, w in enumerate(words):
        wc = re.sub(r'[^a-z0-9]', '', w)
        for q in qt:
            if q == wc or q in wc:
                pos.setdefault(q, []).append(i)
    if len(pos) < 2: return 0.0
    allp = sorted([p for ps in pos.values() for p in ps])
    if len(allp) < 2: return 0.0
    avg = sum(abs(allp[i]-allp[i-1]) for i in range(1, len(allp))) / len(allp)
    return max(0, 1.0 - avg / 50.0)

def retrieve_best_chunks(query, file_texts, top_k=6):
    if not file_texts: return []
    chunks = []
    for ft in file_texts:
        chunks.extend(split_paragraphs(ft))
    for ft in file_texts:
        sents = split_sentences(ft)
        for i in range(0, len(sents), 2):
            grp = " ".join(sents[i:i+3])
            if len(grp) > 60: chunks.append(grp)
    if not chunks: return []
    qt = tokenize(query)
    if not qt: return chunks[:top_k]
    tokenized, idf = build_tfidf_index(chunks)
    scored = []
    for i, (c, t) in enumerate(zip(chunks, tokenized)):
        s = tfidf_score(qt, t, idf) + 0.3 * proximity_bonus(qt, c) + min(len(c)/3000, 0.1)
        scored.append((s, i, c))
    scored.sort(key=lambda x: -x[0])
    seen, results = set(), []
    for s, i, c in scored:
        if s < 0.001: break
        sig = c[:80].lower()
        if sig not in seen:
            seen.add(sig)
            results.append(c)
        if len(results) >= top_k: break
    return results


# ════════════════════════════════════════════════════════════════
#  QUESTION CLASSIFIER (richer than before)
# ════════════════════════════════════════════════════════════════

def classify_intent(query: str) -> dict:
    q = query.lower().strip()
    intent = {
        "type": "general",
        "is_greeting": False,
        "is_thanks": False,
        "is_smalltalk": False,
        "is_opinion": False,
        "is_creative": False,
    }
    if re.match(r'^(hi|hello|hey|yo|sup|good\s*(morning|evening|afternoon))', q):
        intent["is_greeting"] = True
    if re.search(r'\b(thanks|thank you|appreciate)\b', q):
        intent["is_thanks"] = True
    if re.search(r'\b(how are you|how\'s it going|whats up|what\'s up)\b', q):
        intent["is_smalltalk"] = True
    if re.search(r'\b(what do you think|your opinion|do you (like|believe|prefer))\b', q):
        intent["is_opinion"] = True
    if re.search(r'\b(write|create|generate|compose|draft|make me) (a|an|some)?\s*(poem|story|song|essay|joke|email)\b', q):
        intent["is_creative"] = True

    if re.search(r'\bwhat\s+is\b|\bdefine\b|\bmeaning\b', q): intent["type"] = "definition"
    elif re.search(r'\bexplain\b|\bdescribe\b', q): intent["type"] = "explain"
    elif re.search(r'\bhow\b|\bsteps?\b|\bprocess\b', q): intent["type"] = "process"
    elif re.search(r'\bwhy\b|\breason\b|\bcause\b', q): intent["type"] = "reasoning"
    elif re.search(r'\blist\b|\bname\b|\bexamples?\b|\btypes?\b', q): intent["type"] = "listing"
    elif re.search(r'\bcompare\b|\bdifference\b|\bvs\b', q): intent["type"] = "comparison"
    elif re.search(r'\bsummari[sz]e\b|\boverview\b|\bbriefly\b', q): intent["type"] = "summary"
    elif re.search(r'\bsolve\b|\bcalculate\b|\bcompute\b', q): intent["type"] = "math"
    elif re.search(r'\bcode\b|\bprogram\b|\bfunction\b', q): intent["type"] = "code"
    return intent


# ════════════════════════════════════════════════════════════════
#  RESPONSE VARIETY ENGINE — fixes "same answer" problem
# ════════════════════════════════════════════════════════════════

def get_seed(query: str, turn: int) -> int:
    """Deterministic but varies per turn — so repeated questions get fresh phrasing."""
    h = hashlib.md5(f"{query}::{turn}".encode()).hexdigest()
    return int(h[:8], 16)

OPENERS_DEFINITION = [
    "Here's how I'd explain it:",
    "Let me break this down for you:",
    "In simple terms:",
    "The core idea is this:",
    "Think of it like this:",
]
OPENERS_EXPLAIN = [
    "Sure — here's the explanation:",
    "Let's walk through it:",
    "Here's what's going on:",
    "I'll explain it step by step:",
    "Good question. Here's the deal:",
]
OPENERS_GENERAL = [
    "Here's my take:",
    "Alright, let's get into it:",
    "Here's what I think:",
    "Let me share what I know:",
    "Here you go:",
]

def pick(options, seed):
    return options[seed % len(options)]


# ════════════════════════════════════════════════════════════════
#  DOCUMENT-GROUNDED ANSWER SYNTHESIS
# ════════════════════════════════════════════════════════════════

def extract_key_sentences(chunks, qt, max_chars=2400):
    sents = []
    for c in chunks:
        for s in split_sentences(c):
            tokens = tokenize(s)
            overlap = len(set(tokens) & set(qt))
            if overlap > 0:
                sents.append((overlap, s))
    sents.sort(key=lambda x: -x[0])
    seen, picked, total = set(), [], 0
    for sc, s in sents:
        sig = s[:60].lower()
        if sig not in seen and total + len(s) < max_chars:
            seen.add(sig)
            picked.append(s)
            total += len(s)
    if not picked:
        return " ".join(chunks[:3])[:max_chars]
    return " ".join(picked)

def synthesize_from_files(query, chunks, file_names, intent, seed):
    qt = tokenize(query)
    context = extract_key_sentences(chunks, qt)
    full = " ".join(chunks)

    src = f"*📄 Drawn from: {', '.join(file_names)}*"
    opener = pick(OPENERS_EXPLAIN, seed)

    answer = f"{opener}\n\n{src}\n\n"

    t = intent["type"]
    if t == "definition":
        answer += f"**Definition:**\n{context}\n\n"
    elif t == "process":
        sents = split_sentences(context)
        answer += "**Process:**\n\n"
        steps = [s for s in sents if len(s) > 25][:8]
        if steps:
            for i, s in enumerate(steps, 1):
                answer += f"**{i}.** {s}\n\n"
        else:
            answer += context + "\n\n"
    elif t == "reasoning":
        answer += f"**Why this happens:**\n{context}\n\n"
        cs = [s for s in split_sentences(full)
              if re.search(r'because|therefore|thus|hence|due to|leads to', s.lower())
              and any(t in s.lower() for t in qt[:4])]
        if cs:
            answer += "**Cause & effect:**\n" + "\n".join(f"- {s}" for s in cs[:3]) + "\n\n"
    elif t == "listing":
        items = re.findall(r'(?:^|\n)[•\-\*\d+\.]\s*(.+)', full)
        answer += "**Key points:**\n"
        if items:
            for i in items[:10]: answer += f"- {i.strip()}\n"
        else:
            for s in split_sentences(context)[:6]: answer += f"- {s}\n"
        answer += "\n"
    elif t == "comparison":
        answer += f"**Comparison:**\n{context}\n\n"
    elif t == "summary":
        sents = split_sentences(context)
        if len(sents) > 4:
            answer += " ".join(sents[:2]) + " ... " + " ".join(sents[-2:]) + "\n\n"
        else:
            answer += context + "\n\n"
    elif t == "math":
        eqs = re.findall(r'[A-Za-z0-9\+\-\*/=\^\(\)]+\s*=\s*[A-Za-z0-9\+\-\*/\^\(\)\s]+', full)
        if eqs:
            answer += "**Equations from your file:**\n"
            for e in eqs[:5]: answer += f"```\n{e.strip()}\n```\n"
        answer += context + "\n\n"
    elif t == "code":
        cb = re.findall(r'```[\s\S]*?```|`[^`]+`', full)
        if cb:
            for c in cb[:3]: answer += c + "\n\n"
        answer += context + "\n\n"
    else:
        answer += context + "\n\n"

    if len(answer) < 350 and chunks:
        answer += f"\n**More context:**\n{chunks[0][:600]}\n"

    answer += f"\n---\n*⚡ {ENGINE_NAME} engine · sourced from your file*"
    return answer


# ════════════════════════════════════════════════════════════════
#  GENERAL CONVERSATIONAL ENGINE — answers ANY question
# ════════════════════════════════════════════════════════════════

GREETINGS = [
    "Hey! 👋 What's on your mind today?",
    "Hi there! How can I help?",
    "Hello! Ready when you are — ask me anything.",
    "Hey 👋 What would you like to explore?",
]
THANKS_REPLIES = [
    "You're welcome! Happy to help.",
    "Anytime! Ask me more if you need.",
    "Glad I could help 🙌",
    "No problem at all!",
]
SMALLTALK_REPLIES = [
    "I'm running smoothly — ready to dig into anything you throw at me. What's up?",
    "Doing great, thanks for asking! What are we working on?",
    "All systems running. What can I help you with today?",
]

# Built-in knowledge — broad, not just academic
KNOWLEDGE_BASE = {
    # Science
    "photosynthesis": "Photosynthesis is how plants make food. They take in CO₂ from the air and water from the soil, then use sunlight to convert these into glucose (sugar) and oxygen. The equation is 6CO₂ + 6H₂O + light → C₆H₁₂O₆ + 6O₂. It happens in chloroplasts.",
    "newton laws": "Newton gave us 3 laws: (1) Objects keep doing what they're doing unless a force acts on them (inertia). (2) F = m × a — force equals mass times acceleration. (3) Every action has an equal and opposite reaction.",
    "gravity": "Gravity is the force pulling objects with mass toward each other. Newton said F = G·m₁·m₂/r². Einstein later showed gravity is actually the curving of spacetime caused by mass.",
    "dna": "DNA is a double-helix molecule storing genetic instructions. It's made of nucleotides with four bases — A, T, G, C — pairing as A-T and G-C. It tells your cells how to build proteins.",
    "evolution": "Evolution is how species change over generations through natural selection. Individuals with helpful traits survive and reproduce more, passing those traits on. Darwin proposed this in 1859.",
    "atom": "An atom is the smallest unit of matter that retains an element's properties. It has a nucleus (protons + neutrons) surrounded by electrons. Different elements have different numbers of protons.",
    "black hole": "A black hole is a region of space where gravity is so strong that nothing — not even light — can escape. They form when massive stars collapse. The boundary is called the event horizon.",
    
    # Math
    "pythagoras": "In a right triangle, the square of the longest side (hypotenuse) equals the sum of squares of the other two sides: a² + b² = c².",
    "pi": "Pi (π) ≈ 3.14159 is the ratio of a circle's circumference to its diameter. It's irrational — its decimals never end or repeat.",
    "calculus": "Calculus is the math of change. Differentiation finds rates of change (slopes). Integration finds totals (areas). Newton and Leibniz invented it in the 1600s.",
    
    # History
    "world war 2": "WWII (1939–1945) was a global conflict. The Allies (USA, UK, USSR, France) fought the Axis (Germany, Italy, Japan). It started with Germany invading Poland and ended after atomic bombs hit Hiroshima and Nagasaki.",
    "world war 1": "WWI (1914–1918) was triggered by the assassination of Archduke Franz Ferdinand. It involved trench warfare across Europe, killed 20+ million people, and led to the Treaty of Versailles.",
    "french revolution": "From 1789–1799, French citizens overthrew the monarchy. Causes: financial crisis, inequality, Enlightenment ideas. Famous events: Storming of the Bastille, execution of Louis XVI, rise of Napoleon.",
    "cold war": "The Cold War (1947–1991) was a tense rivalry between the USA and USSR — no direct fighting, but proxy wars, nuclear arms race, and the space race. Ended with the Soviet Union's collapse.",
    
    # Tech
    "ai": "Artificial Intelligence is software that performs tasks needing human-like intelligence — recognizing patterns, understanding language, making decisions. Modern AI uses machine learning trained on huge datasets.",
    "blockchain": "Blockchain is a distributed ledger where data is stored in linked 'blocks' across many computers. It's tamper-resistant because changing one block breaks the whole chain. Powers Bitcoin and other cryptocurrencies.",
    "internet": "The Internet is a global network of connected computers communicating via standardized protocols (TCP/IP). It started as ARPANET in 1969 and went public in the 1990s.",
    "algorithm": "An algorithm is a step-by-step recipe for solving a problem. Examples: sorting (bubble sort, quicksort), searching (binary search), pathfinding (Dijkstra's). Every program is built from algorithms.",
    "machine learning": "Machine learning is AI that learns from data instead of being explicitly programmed. Types: supervised (with labels), unsupervised (find patterns), and reinforcement (learn by trial).",
    
    # Lifestyle / general
    "happiness": "Research suggests happiness comes from strong relationships, purpose, gratitude, regular exercise, sleep, and helping others — not from money or possessions beyond a basic threshold.",
    "productivity": "Top productivity tips: work in focused 25–90 minute blocks, eliminate distractions, do hardest work first, get 7–8h sleep, exercise, take real breaks, and say no more often.",
    "stress": "To manage stress: breathe deeply, exercise, sleep well, talk to someone, break problems into small steps, limit caffeine, and accept what you can't control.",
    
    # Business
    "supply demand": "Supply and demand: when prices rise, suppliers want to sell more but buyers want less. The market settles at an equilibrium price where both meet.",
    "marketing": "Marketing is connecting products with people who want them. Modern marketing uses content, social media, SEO, ads, and storytelling — focused on solving the customer's problem.",
}

def general_knowledge_match(query: str):
    q = query.lower()
    qt = tokenize(query)
    best, best_score = None, 0
    for key, ans in KNOWLEDGE_BASE.items():
        kt = tokenize(key)
        score = len(set(qt) & set(kt)) * 2
        if key in q: score += 5
        for w in key.split():
            if w in q: score += 2
        if score > best_score:
            best_score = score
            best = (key, ans)
    if best and best_score >= 2:
        return best
    return None

def reasoning_response(query: str, intent: dict, seed: int) -> str:
    """When no knowledge match, generate a thoughtful, varied response."""
    q = query.strip()
    qt = tokenize(query)
    
    if intent["is_creative"]:
        return creative_response(query, seed)
    if intent["is_opinion"]:
        return opinion_response(query, seed)

    # Question-type-aware response
    t = intent["type"]
    opener = pick(OPENERS_GENERAL, seed)
    
    if t == "definition":
        topic = " ".join(qt[:4]) if qt else "this"
        templates = [
            f"{opener}\n\n**{topic.title()}** refers to a concept I don't have detailed built-in info on. To give you a precise answer, could you:\n\n- Share a bit more context\n- Or upload a file with the relevant material\n\nI can also try to reason about it if you tell me what domain it's from (science, business, history, etc.).",
            f"Without more context I can only speak generally about *{topic}*. {opener.lower()} my best general framing is that this likely relates to a concept that has multiple definitions depending on the field. Tell me which field you mean and I'll get specific.",
        ]
        return pick(templates, seed)
    
    if t == "process":
        return f"{opener}\n\nGreat 'how-to' question. To give you accurate steps for **{q}**, I'd love a bit more context — what's your starting point, and what's the goal?\n\nIf you upload a guide or notes, I'll extract the exact steps. Otherwise, share the situation and I'll reason through it with you."
    
    if t == "reasoning":
        return f"{opener}\n\nThat's a 'why' question — those usually have layered answers. For **{q}**, the reasoning depends on context. Tell me a bit more about what triggered the question (a situation, a fact you read, etc.) and I'll dig into the cause-and-effect with you."

    # Generic but thoughtful
    fallbacks = [
        f"{opener}\n\nI hear you asking about **{q}**. I don't have a pre-loaded answer for that exact topic, but I can help in two ways:\n\n1. **Upload material** — I'll analyze it word-by-word and answer from there.\n2. **Give me more context** — explain a bit more and I'll reason it through with you.\n\nWhich works for you?",
        f"Hmm, **{q}** — interesting one. I run a fully autonomous reasoning engine ({ENGINE_NAME}), so I don't pull from the live internet. If you want a precise answer:\n\n- Drop a file related to it 📎\n- Or rephrase with more detail and I'll work through it with you.",
        f"{opener}\n\nLet's tackle this together. For **{q}**, share either:\n- A document I can analyze, or\n- More context (what field, what level of detail you want)\n\nMy strength is deep file analysis + reasoning, not internet recall.",
    ]
    return pick(fallbacks, seed)

def creative_response(query: str, seed: int) -> str:
    q = query.lower()
    if "poem" in q:
        poems = [
            "Here's a short poem for you:\n\n*The screen glows soft, the ideas flow,\nA quiet hum, a steady go.\nWords meet thoughts, and thoughts meet light,\nWe build together through the night.*",
            "How about this:\n\n*Lines of code, lines of verse,\nDifferent tongues, the same universe.\nWe ask, we seek, we type, we find —\nA kind of magic in the mind.*",
        ]
        return pick(poems, seed)
    if "joke" in q:
        jokes = [
            "Why did the developer go broke? Because he used up all his cache. 💸",
            "I told my computer I needed a break. It said: 'No problem — I'll go to sleep.' 😴",
            "Why don't scientists trust atoms? Because they make up everything. ⚛️",
        ]
        return pick(jokes, seed)
    if "story" in q:
        return "Here's a quick one:\n\n*The robot looked at the sky for the first time. It had been told the stars were just fusion reactors very far away. But standing there in the silence, it wondered if maybe — just maybe — the humans had missed something the equations couldn't capture.*\n\nWant me to expand it?"
    return f"Tell me a bit more about what you want me to create — topic, length, mood — and I'll write something fresh for you."

def opinion_response(query: str, seed: int) -> str:
    return pick([
        "I'll share a perspective, though remember it's just one angle: ",
        "Here's how I'd think about it: ",
        "My take, for what it's worth: ",
    ], seed) + "this depends on what you value most. If you tell me what matters to you in this situation, I can reason through the tradeoffs with you instead of giving a generic answer."


# ════════════════════════════════════════════════════════════════
#  THE BRAIN
# ════════════════════════════════════════════════════════════════

def add_ai_brain(query: str, file_texts: list, file_names: list, mode: str, turn: int) -> str:
    q_lower = query.lower().strip()
    seed = get_seed(query, turn)
    intent = classify_intent(query)

    # Identity
    if any(p in q_lower for p in IDENTITY_KEYWORDS):
        return (
            f"## 🤖 I'm {APP_NAME}\n\n"
            f"I run on **{ENGINE_NAME}** — my own reasoning engine, built from scratch by **{CREATOR}**.\n\n"
            f"I'm **not** GPT, Claude, Gemini, or any external service. No API keys, no cloud calls — just pure local reasoning.\n\n"
            f"**What I can do:**\n"
            f"- 📎 Deep-analyze any file you upload (PDF, DOCX, TXT, code, spreadsheets)\n"
            f"- 💬 Answer questions on almost any topic using my built-in knowledge + reasoning\n"
            f"- ✍️ Help with writing, brainstorming, explanations, summaries\n"
            f"- 🔍 Find specific info inside long documents\n\n"
            f"**Version:** {VERSION}\n\n"
            f"What would you like to dive into?"
        )

    # Greetings & social
    if intent["is_greeting"]:
        return pick(GREETINGS, seed)
    if intent["is_thanks"]:
        return pick(THANKS_REPLIES, seed)
    if intent["is_smalltalk"]:
        return pick(SMALLTALK_REPLIES, seed)

    # File-based answering (priority when files present)
    if file_texts:
        chunks = retrieve_best_chunks(query, file_texts, top_k=6)
        if chunks:
            return synthesize_from_files(query, chunks, file_names, intent, seed)
        # File present but no relevant content → fall through to general
        # but mention we checked files
        general = answer_from_general(query, intent, seed)
        return f"*I checked your uploaded files but couldn't find this topic there. Answering from general knowledge:*\n\n---\n\n{general}"

    # No files → general engine
    return answer_from_general(query, intent, seed)


def answer_from_general(query: str, intent: dict, seed: int) -> str:
    if intent["is_creative"]:
        return creative_response(query, seed)
    
    match = general_knowledge_match(query)
    if match:
        key, ans = match
        opener = pick(OPENERS_DEFINITION + OPENERS_EXPLAIN, seed)
        # Vary the structure
        variations = [
            f"{opener}\n\n**{key.title()}** — {ans}\n\n*Need more depth? Upload a file or ask a follow-up.*",
            f"{opener}\n\n{ans}\n\n💡 *That's the core of {key}. Ask me to go deeper on any part.*",
            f"Sure, here's what I know about **{key}**:\n\n{ans}\n\nWant me to compare it with something, give examples, or go deeper?",
        ]
        return pick(variations, seed)
    
    return reasoning_response(query, intent, seed)


# ════════════════════════════════════════════════════════════════
#  STREAMLIT UI
# ════════════════════════════════════════════════════════════════

def render():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@300;400;500&display=swap');
    @keyframes float{0%,100%{transform:translateY(0)}50%{transform:translateY(-7px)}}
    @keyframes slide-in{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:translateY(0)}}
    @keyframes blink{0%,80%,100%{opacity:0}40%{opacity:1}}
    @keyframes shimmer{0%{background-position:-200% center}100%{background-position:200% center}}
    .msg-user{animation:slide-in .28s ease;background:linear-gradient(135deg,rgba(123,97,255,.13),rgba(0,245,212,.07));border:1px solid rgba(123,97,255,.28);border-radius:16px 16px 4px 16px;padding:1rem 1.25rem;margin:.55rem 0;}
    .msg-ai{animation:slide-in .32s ease .06s both;background:rgba(13,17,23,.88);border:1px solid rgba(0,245,212,.18);border-radius:16px 16px 16px 4px;padding:1rem 1.25rem;margin:.55rem 0;}
    .msg-label{font-family:'Syne',sans-serif;font-size:.66rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase;margin-bottom:.4rem;}
    .thinking span{animation:blink 1.2s infinite;font-size:1.3rem;}
    .thinking span:nth-child(2){animation-delay:.22s}
    .thinking span:nth-child(3){animation-delay:.44s}
    .shimmer-bar{height:2px;border-radius:2px;background:linear-gradient(90deg,#00f5d4,#7b61ff,#ff6b6b,#00f5d4);background-size:200% auto;animation:shimmer 1.4s linear infinite;margin:.4rem 0 .8rem;}
    .autonomous-badge{display:inline-block;background:linear-gradient(90deg,rgba(0,245,212,.1),rgba(123,97,255,.1));border:1px solid rgba(0,245,212,.25);border-radius:100px;padding:.28rem .85rem;font-size:.7rem;color:#00f5d4;letter-spacing:.09em;font-family:'Syne',sans-serif;font-weight:700;}
    .file-pill{display:inline-block;background:rgba(0,245,212,.09);border:1px solid rgba(0,245,212,.22);border-radius:100px;padding:.14rem .55rem;font-size:.7rem;color:#00f5d4;margin:.15rem;}
    </style>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div style="text-align:center;padding:1.8rem 0 .9rem;">
      <div style="margin-bottom:.8rem;">
        <span class="autonomous-badge">⚡ {ENGINE_NAME} · 100% Autonomous · By {CREATOR}</span>
      </div>
      <h1 style="font-family:'Syne',sans-serif;font-size:clamp(1.8rem,4.5vw,3rem);font-weight:800;line-height:1.1;margin-bottom:.5rem;">
        <span style="background:linear-gradient(135deg,#e8eaf6,#fff);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Talk To</span>
        <span style="background:linear-gradient(135deg,#00f5d4,#7b61ff,#ff6b6b);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">Add AI</span>
      </h1>
      <p style="color:#6b7280;font-size:.95rem;max-width:480px;margin:0 auto;">
        Ask anything · Upload files for deep analysis · Truly independent engine
      </p>
    </div>
    """, unsafe_allow_html=True)

    # Session state
    if "messages" not in st.session_state: st.session_state.messages = []
    if "mode" not in st.session_state: st.session_state.mode = "💬 General Conversation"
    if "pending_message" not in st.session_state: st.session_state.pending_message = ""
    if "chat_input_key" not in st.session_state: st.session_state.chat_input_key = 0
    if "turn_counter" not in st.session_state: st.session_state.turn_counter = 0
    if "file_cache" not in st.session_state: st.session_state.file_cache = {}

    # Controls
    c1, c2, c3 = st.columns([3, 1, 1])
    with c1:
        mode = st.selectbox("Mode", list(DOMAIN_HINTS.keys()), label_visibility="collapsed")
        st.session_state.mode = mode
    with c2:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.session_state.turn_counter = 0
            st.rerun()
    with c3:
        if st.button("📤 Export", use_container_width=True) and st.session_state.messages:
            txt = "\n\n".join([f"{'YOU' if m['role']=='user' else 'ADD AI'}: {m['content']}" for m in st.session_state.messages])
            st.download_button("💾 Save", txt, "add_ai_chat.txt", "text/plain")

    # File uploader
    uploaded = st.file_uploader(
        "📎 Upload files (PDF, DOCX, TXT, CSV, code — up to 10)",
        accept_multiple_files=True,
        type=["pdf","docx","doc","txt","csv","xlsx","xls","py","js","ts","html","css","json","xml","md","cpp","c","java"],
        label_visibility="collapsed",
        key="file_uploader_main"
    )
    if uploaded and len(uploaded) > 10:
        uploaded = uploaded[:10]

    if uploaded:
        pills = "".join([f'<span class="file-pill">📄 {f.name}</span>' for f in uploaded])
        st.markdown(f"<div style='margin:.3rem 0 .6rem;'>{pills}</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:rgba(0,245,212,.05);border:1px solid rgba(0,245,212,.12);border-radius:10px;padding:.5rem .85rem;font-size:.78rem;color:#6b7280;margin-bottom:.5rem;">
          ✅ <strong style="color:#00f5d4;">{len(uploaded)} file(s) loaded</strong> — I'll deeply analyze them in real-time for every question you ask.
        </div>
        """, unsafe_allow_html=True)

    # Chat history
    if not st.session_state.messages:
        st.markdown("""
        <div style="text-align:center;padding:2rem 1rem 1.2rem;">
          <div style="font-size:3rem;animation:float 3s ease-in-out infinite;display:block;margin-bottom:.6rem;">🧠</div>
          <div style="font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:700;color:#e8eaf6;margin-bottom:.3rem;">Ask me anything</div>
          <div style="color:#6b7280;font-size:.83rem;">Upload files for deep analysis, or just chat</div>
        </div>
        """, unsafe_allow_html=True)
        examples = [
            ("👋", "Hi, who are you?"),
            ("📐", "Explain the Pythagoras theorem"),
            ("📝", "Summarize my uploaded document"),
            ("✍️", "Write me a short poem about coding"),
            ("💼", "Tips for being more productive"),
            ("🧪", "How does photosynthesis work?"),
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
                st.markdown(f"""<div class="msg-user"><div class="msg-label" style="color:#7b61ff;">You</div><div style="color:#e8eaf6;line-height:1.65;">{msg['content']}</div></div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""<div class="msg-ai"><div class="msg-label" style="color:#00f5d4;">⚡ {ENGINE_NAME}</div></div>""", unsafe_allow_html=True)
                st.markdown(msg["content"])

    # Input
    def _submit():
        val = st.session_state.get(f"ci_{st.session_state.chat_input_key}", "").strip()
        if val:
            st.session_state.pending_message = val
            st.session_state.chat_input_key += 1

    ci_col, btn_col = st.columns([6, 1])
    with ci_col:
        st.text_area(
            "Message",
            placeholder="Ask anything — about your files, life, science, code, anything...",
            height=90,
            label_visibility="collapsed",
            key=f"ci_{st.session_state.chat_input_key}",
        )
    with btn_col:
        st.markdown("<div style='height:24px;'></div>", unsafe_allow_html=True)
        if st.button("Send ➤", use_container_width=True, on_click=_submit):
            pass

    # Process pending message
    if st.session_state.pending_message:
        query = st.session_state.pending_message.strip()
        st.session_state.pending_message = ""
        st.session_state.messages.append({"role": "user", "content": query})
        st.session_state.turn_counter += 1

        with st.spinner(""):
            st.markdown(f"""
            <div class="msg-ai">
              <div class="msg-label" style="color:#00f5d4;">⚡ {ENGINE_NAME} — analyzing in real-time</div>
              <div class="thinking"><span>●</span><span>●</span><span>●</span></div>
            </div>
            <div class="shimmer-bar"></div>
            """, unsafe_allow_html=True)

            # REAL-TIME file extraction (every turn — fresh analysis)
            file_texts, file_names = [], []
            for f in (uploaded or []):
                try:
                    text = extract_text(f)
                    file_texts.append(text)
                    file_names.append(f.name)
                except Exception as e:
                    st.warning(f"Could not read {f.name}: {e}")

            response = add_ai_brain(query, file_texts, file_names,
                                    st.session_state.mode, st.session_state.turn_counter)
            st.session_state.messages.append({"role": "assistant", "content": response})

        st.rerun()

    # Sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"""
        <div style="padding:.85rem;background:rgba(0,245,212,.05);border-radius:12px;border:1px solid rgba(0,245,212,.12);font-size:.78rem;color:#6b7280;">
          <div style="color:#00f5d4;font-family:'Syne',sans-serif;font-weight:700;margin-bottom:.4rem;">⚡ {ENGINE_NAME}</div>
          ✅ Engine: {ENGINE_NAME}<br>
          ✅ No API keys<br>
          ✅ No external AI<br>
          ✅ Real-time file analysis<br>
          ✅ Variable, fresh responses<br><br>
          <div style="color:#7b61ff;font-weight:600;">Built by {CREATOR}</div>
          <div style="color:#6b7280;margin-top:.2rem;">Version {VERSION}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("### 📋 What I Do Best")
        st.markdown("""
        - 📎 **File Q&A** — I extract & analyze every word
        - 💬 **General chat** — any topic, any style
        - ✍️ **Creative** — poems, stories, jokes
        - 🧠 **Reasoning** — I think through problems
        - 🔄 **Fresh answers** — never the same reply twice
        """)


if __name__ == "__main__":
    render()
