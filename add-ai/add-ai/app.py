import streamlit as st

st.set_page_config(
    page_title="Add AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inject global CSS & animations
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

:root {
  --bg: #050810;
  --surface: #0d1117;
  --surface2: #161b27;
  --accent: #00f5d4;
  --accent2: #7b61ff;
  --accent3: #ff6b6b;
  --text: #e8eaf6;
  --muted: #6b7280;
  --glow: 0 0 40px rgba(0,245,212,0.15);
  --radius: 16px;
}

* { box-sizing: border-box; margin: 0; padding: 0; }

html, body, [data-testid="stAppViewContainer"] {
  background: var(--bg) !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif !important;
}

[data-testid="stSidebar"] {
  background: var(--surface) !important;
  border-right: 1px solid rgba(0,245,212,0.1) !important;
}

[data-testid="stSidebar"] * { color: var(--text) !important; }

.stButton > button {
  background: linear-gradient(135deg, var(--accent2), var(--accent)) !important;
  color: #000 !important;
  border: none !important;
  border-radius: 12px !important;
  font-family: 'Syne', sans-serif !important;
  font-weight: 700 !important;
  letter-spacing: 0.05em !important;
  padding: 0.6rem 1.5rem !important;
  transition: all 0.3s ease !important;
  cursor: pointer !important;
}
.stButton > button:hover {
  transform: translateY(-2px) !important;
  box-shadow: 0 8px 30px rgba(123,97,255,0.4) !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
  background: var(--surface2) !important;
  border: 1px solid rgba(0,245,212,0.2) !important;
  border-radius: 12px !important;
  color: var(--text) !important;
  font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(0,245,212,0.15) !important;
}

[data-testid="stFileUploader"] {
  background: var(--surface2) !important;
  border: 2px dashed rgba(0,245,212,0.3) !important;
  border-radius: 16px !important;
  transition: all 0.3s !important;
}
[data-testid="stFileUploader"]:hover {
  border-color: var(--accent) !important;
  box-shadow: var(--glow) !important;
}

h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

.stMarkdown a { color: var(--accent) !important; }

div[data-testid="stDecoration"] { display: none !important; }

[data-testid="stHeader"] {
  background: transparent !important;
}

.stSpinner > div { border-top-color: var(--accent) !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--accent2); border-radius: 3px; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface2) !important;
  border-radius: 12px !important;
  padding: 4px !important;
  gap: 4px !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--muted) !important;
  border-radius: 10px !important;
  font-family: 'Syne', sans-serif !important;
  font-weight: 600 !important;
  transition: all 0.2s !important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg, var(--accent2), var(--accent)) !important;
  color: #000 !important;
}

/* Selectbox */
.stSelectbox [data-baseweb="select"] > div {
  background: var(--surface2) !important;
  border-color: rgba(0,245,212,0.2) !important;
}
</style>

<script>
// Particle background animation
(function() {
  const canvas = document.createElement('canvas');
  canvas.id = 'particleCanvas';
  canvas.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;pointer-events:none;z-index:0;opacity:0.4;';
  document.body.prepend(canvas);
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  
  const particles = Array.from({length: 60}, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    r: Math.random() * 2 + 0.5,
    dx: (Math.random() - 0.5) * 0.4,
    dy: (Math.random() - 0.5) * 0.4,
    color: Math.random() > 0.5 ? '#00f5d4' : '#7b61ff'
  }));
  
  function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    particles.forEach(p => {
      p.x += p.dx; p.y += p.dy;
      if (p.x < 0 || p.x > canvas.width) p.dx *= -1;
      if (p.y < 0 || p.y > canvas.height) p.dy *= -1;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = p.color;
      ctx.shadowBlur = 10;
      ctx.shadowColor = p.color;
      ctx.fill();
    });
    requestAnimationFrame(animate);
  }
  animate();
  window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  });
})();
</script>
""", unsafe_allow_html=True)

# ── Sidebar Navigation ──────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1.5rem 0 1rem;">
      <div style="font-family:'Syne',sans-serif;font-size:2rem;font-weight:800;
                  background:linear-gradient(135deg,#00f5d4,#7b61ff);
                  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                  letter-spacing:-0.02em;">Add AI</div>
      <div style="font-size:0.75rem;color:#6b7280;letter-spacing:0.15em;
                  text-transform:uppercase;margin-top:0.25rem;">by your side, always</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["🧠 AI Agent", "🎨 UGC Creator Studio"],
        label_visibility="collapsed"
    )

    st.markdown("---")
    st.markdown("""
    <div style="padding:1rem;background:rgba(0,245,212,0.05);border-radius:12px;
                border:1px solid rgba(0,245,212,0.1);font-size:0.8rem;color:#6b7280;">
      <div style="color:#00f5d4;font-weight:600;margin-bottom:0.5rem;">⚡ Powered by</div>
      Claude 3 Sonnet • Gemini Flash<br>Groq Ultra-Fast • Replicate AI<br>ElevenLabs TTS
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style="margin-top:1rem;padding:0.75rem;background:rgba(123,97,255,0.08);
                border-radius:12px;border:1px solid rgba(123,97,255,0.15);
                font-size:0.75rem;color:#6b7280;text-align:center;">
      🌐 Real-time web access enabled<br>
      📁 Upload up to 10 files at once
    </div>
    """, unsafe_allow_html=True)

# ── Route Pages ──────────────────────────────────────────────────────────────
if "🧠 AI Agent" in page:
    from pages.ai_agent import render
    render()
else:
    from pages.ugc_studio import render
    render()
# ... (All your CSS and Particle JS exactly the same) ...

# ── Sidebar Navigation ──────────────────────────────────────────────────────
# ...
    st.markdown("""
    <div style="padding:1rem;background:rgba(0,245,212,0.05);border-radius:12px;
                border:1px solid rgba(0,245,212,0.1);font-size:0.8rem;color:#6b7280;">
      <div style="color:#00f5d4;font-weight:600;margin-bottom:0.5rem;">⚡ Powered by</div>
      Gemini Flash • Groq Ultra-Fast<br>Replicate AI • ElevenLabs TTS
    </div>
    """, unsafe_allow_html=True)
# ...
