# 🧠 Add AI — Academic Super-Intelligence + UGC Creator Studio

> Your all-in-one AI platform: advanced academic assistant + viral UGC content creation

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://share.streamlit.io)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## ✨ Features

### 🧠 AI Agent — Academic Super-Intelligence
- **Real-time web access** — fetches current data, research papers, statistics
- **All academic subjects** — Math, Science, CS, Literature, History, Biology, Economics, and more
- **File upload analysis** — upload up to 10 files (PDF, images, code, docs) simultaneously
- **Step-by-step solutions** — complete working shown for every problem
- **Smart context** — subject-specific AI personas optimized per field
- **Chat export** — download conversation as text file
- **Streaming responses** — real-time answer generation

### 🎨 UGC Creator Studio
| Mode | Description |
|------|-------------|
| **Text → Image** | Generate UGC lifestyle images from text descriptions via FLUX |
| **Image → Image** | Transform your photos with AI style transfer |
| **Text → Video** | Create UGC videos from text + optional voiceover |
| **Image → Video** | Animate still images with AI + add voiceover |

**Voiceover Features:**
- 10 voice agents (5 Male, 5 Female)
- 6 tone styles: Natural, Enthusiastic, Professional, Dramatic, Calm, Persuasive
- AI script generation
- Preview before generating
- Powered by ElevenLabs Multilingual v2

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/add-ai.git
cd add-ai
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure API Keys

**Option A — Environment Variables (local):**
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key"
export REPLICATE_API_TOKEN="r8_your-token"
export ELEVENLABS_API_KEY="sk_your-key"
```

**Option B — .env file:**
```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit .streamlit/secrets.toml with your keys
```

**Option C — In-App:** Enter keys directly in the sidebar (session-only, not saved)

### 4. Run the App
```bash
streamlit run app.py
```

---

## ☁️ Deploy on Streamlit Cloud (Free)

1. **Fork this repo** to your GitHub account
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click **"New app"** → select your forked repo
4. Set **main file path** to `app.py`
5. In **Advanced settings → Secrets**, add:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-your-key-here"
   REPLICATE_API_TOKEN = "r8_your-token-here"
   ELEVENLABS_API_KEY = "sk_your-key-here"
   ```
6. Click **Deploy!** 🚀

---

## 🔑 API Keys — All Free Tiers Available

| Service | Purpose | Free Tier | Get Key |
|---------|---------|-----------|---------|
| **Anthropic** | AI Agent chat + script generation | $5 free credits | [console.anthropic.com](https://console.anthropic.com) |
| **Replicate** | Image & video generation | Free tier + pay-per-use | [replicate.com](https://replicate.com) |
| **ElevenLabs** | Voice synthesis | 10,000 chars/month free | [elevenlabs.io](https://elevenlabs.io) |

---

## 📁 Project Structure
```
add-ai/
├── app.py                    # Main entry point + global styling
├── pages/
│   ├── __init__.py
│   ├── ai_agent.py           # Academic AI chat agent
│   └── ugc_studio.py         # UGC content creation studio
├── .streamlit/
│   ├── config.toml           # Streamlit theme config
│   └── secrets.toml.example  # API keys template
├── requirements.txt
├── .gitignore
└── README.md
```

---

## 🎯 Supported File Types (AI Agent)

| Category | Formats |
|----------|---------|
| Documents | PDF, TXT, MD, DOCX, XLSX |
| Images | PNG, JPG, JPEG, GIF, WEBP |
| Code | PY, JS, TS, HTML, CSS, CPP, C, JAVA, RS, GO, RB |
| Data | CSV, JSON, XML |

---

## 🎓 Academic Subjects Supported

Mathematics · Physics · Chemistry · Biology · Computer Science · Literature · History · Economics · Geography · Psychology · Philosophy · Engineering · Statistics · Linguistics · Arts & more

---

## 🛡️ Privacy & Security
- API keys are never stored permanently — session-only when entered in-app
- Use Streamlit Secrets for production deployment
- No conversation data is stored between sessions

---

## 📄 License
MIT License — use freely for personal and commercial projects.

---

<div align="center">
  <strong>Built with ❤️ using Streamlit + Anthropic Claude + Replicate + ElevenLabs</strong>
</div>
