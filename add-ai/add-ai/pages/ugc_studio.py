import streamlit as st
import google.generativeai as genai
import requests
import base64
import os
import time
import json
import random
from urllib.parse import quote
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()

# ── Voice Agents ─────────────────────────────────────────────────────────────

VOICE_AGENTS = {
    "Male": {
        "Marcus (Deep & Authoritative)": "pNInz6obpgDQGcFmaJgB",
        "James (Warm & Professional)": "VR6AewLTigWG4xSOukaG",
        "Liam (Young & Energetic)": "TX3LPaxmHKxFdv7VOQHJ",
        "Ethan (Smooth & Confident)": "bVMeCyTHy58xNoL34h3p",
        "Noah (Casual & Friendly)": "ErXwobaYiN019PkySvjV",
    },
    "Female": {
        "Aria (Clear & Professional)": "EXAVITQu4vr4xnSDxMaL",
        "Sofia (Warm & Empathetic)": "21m00Tcm4TlvDq8ikWAM",
        "Luna (Energetic & Bright)": "AZnzlk1XvdvUeBnXmlld",
        "Emma (Calm & Reassuring)": "MF3mGyEYCl7XYWbV9V6O",
        "Zoe (Youthful & Vibrant)": "ThT5KcBeYPX3keUQqHPh",
    }
}

TONE_DESCRIPTIONS = {
    "Natural": "conversational, natural delivery",
    "Enthusiastic": "high energy, excited, enthusiastic",
    "Professional": "formal, polished, corporate",
    "Dramatic": "theatrical, cinematic, dramatic pauses",
    "Calm": "slow, calm, meditative",
    "Persuasive": "sales-oriented, compelling, urgent",
}

# ── Bulletproof Key Fetcher ───────────────────────────────────────────────────

def get_key(env_var_name, session_state_name):
    """Aggressively checks for keys across Sidebar, Streamlit Secrets, and .env"""
    if st.session_state.get(session_state_name):
        return st.session_state[session_state_name]
    try:
        if env_var_name in st.secrets:
            return st.secrets[env_var_name]
    except Exception:
        pass
    return os.environ.get(env_var_name, "")

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_gemini_client():
    key = get_key("GOOGLE_API_KEY", "google_key")
    if key:
        genai.configure(api_key=key)
        return genai.GenerativeModel(model_name='gemini-2.5-flash')
    return None

def get_elevenlabs_key():
    return get_key("ELEVENLABS_API_KEY", "elevenlabs_key")

def enhance_prompt_with_gemini(client, prompt, mode):
    system = """You are a UGC (User Generated Content) creative director. Transform basic prompts into highly detailed, cinematic generation prompts. Return ONLY the enhanced prompt, nothing else."""
    try:
        response = client.generate_content(f"{system}\n\nMode: {mode}\n\nOriginal prompt: {prompt}")
        return response.text.strip()
    except:
        return prompt

def generate_image_hf(prompt):
    """Uses Ungated HF Models with an 8-Second Hard Timeout to prevent loading freezes."""
    hf_token = get_key("HF_TOKEN", "hf_token")
    if not hf_token:
        return None, "🔑 Missing Hugging Face Token. Please add your free token in the sidebar or Streamlit Secrets."
    
    models_to_try = [
        "stabilityai/stable-diffusion-xl-base-1.0",
        "prompthero/openjourney"
    ]
    
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {"inputs": prompt}
    
    for model in models_to_try:
        API_URL = f"https://api-inference.huggingface.co/models/{model}"
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=8)
            if resp.status_code == 200 and 'image' in resp.headers.get('Content-Type', '').lower():
                return resp.content, None
            elif resp.status_code == 503:
                continue 
        except Exception:
            continue

    # BROWSER BYPASS: Offload to client browser if HF fails
    seed = random.randint(1, 100000)
    fallback_url = f"https://image.pollinations.ai/prompt/{quote(prompt)}?seed={seed}&width=1024&height=1024&nologo=true"
    return fallback_url, None

def generate_video_free(prompt):
    """Video Model Cascade: Tries 3 different free video servers. If one is down (404/503), it jumps to the next."""
    hf_token = get_key("HF_TOKEN", "hf_token")
    if not hf_token:
        return None, "🔑 Missing Hugging Face Token. Add it in settings to generate free videos."
        
    models_to_try = [
        "damo-vilab/text-to-video-ms-1.7b",
        "cerspense/zeroscope_v2_576w",
        "ByteDance/ModelScope-text-to-video-synthesis"
    ]
    
    headers = {"Authorization": f"Bearer {hf_token}"}
    payload = {"inputs": prompt}
    
    for model in models_to_try:
        API_URL = f"https://api-inference.huggingface.co/models/{model}"
        try:
            # Video takes longer, allowing 15 seconds per model before jumping
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=15)
            
            if resp.status_code == 200:
                return resp.content, None
            elif resp.status_code == 503 or resp.status_code == 404:
                continue # Model is overloaded or removed, instantly try the next one
        except Exception:
            continue # Timeout, instantly try the next one

    # If ALL 3 free models are down/overloaded, fail gracefully without crashing the app
    return None, "Server Alert: All 3 free video servers are currently at maximum global capacity. Video AI requires massive GPU power and free queues fill up fast. Please wait 60 seconds and try again."

def generate_tts_elevenlabs(script, voice_id, tone):
    api_key = get_elevenlabs_key()
    if not api_key:
        return None, "No ElevenLabs API key. (Note: ElevenLabs has a free tier of 10,000 chars/month, but requires an account)."
    
    tone_settings = {
        "Natural": {"stability": 0.5, "similarity_boost": 0.75, "style": 0.0},
        "Enthusiastic": {"stability": 0.3, "similarity_boost": 0.85, "style": 0.8},
        "Professional": {"stability": 0.75, "similarity_boost": 0.65, "style": 0.2},
        "Dramatic": {"stability": 0.35, "similarity_boost": 0.90, "style": 0.9},
        "Calm": {"stability": 0.85, "similarity_boost": 0.60, "style": 0.1},
        "Persuasive": {"stability": 0.4, "similarity_boost": 0.80, "style": 0.7},
    }
    settings = tone_settings.get(tone, tone_settings["Natural"])
    
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {
        "xi-api-key": api_key,
        "Content-Type": "application/json"
    }
    payload = {
        "text": script,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": settings["stability"],
            "similarity_boost": settings["similarity_boost"],
            "style": settings.get("style", 0.0),
            "use_speaker_boost": True
        }
    }
    
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        if resp.status_code == 200:
            return resp.content, None
        return None, f"ElevenLabs error: {resp.status_code} - {resp.text[:200]}"
    except Exception as e:
        return None, str(e)

def generate_script_with_gemini(client, description, tone, duration_sec=15):
    prompt = f"""Write a {duration_sec}-second UGC video script.
Style: {tone}
Product/Scene: {description}

Requirements:
- Sound natural and authentic, NOT like an ad
- Include action cues in [brackets] sparingly
- Hook in first 3 seconds
- Clear, conversational language
- End with soft CTA or memorable line
- Script should be speakable in ~{duration_sec} seconds ({duration_sec * 2} words max)

Return ONLY the spoken script text (no stage directions, no explanations)."""
    
    try:
        response = client.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Script generation failed: {e}"

# ── Main Render ───────────────────────────────────────────────────────────────

def render():
    st.markdown("""
    <style>
    @keyframes shimmer {
      0% { background-position: -200% center; }
      100% { background-position: 200% center; }
    }
    @keyframes pop-in {
      0% { transform: scale(0.9); opacity: 0; }
      100% { transform: scale(1); opacity: 1; }
    }
    @keyframes glow-pulse {
      0%, 100% { box-shadow: 0 0 20px rgba(0,245,212,0.2); }
      50% { box-shadow: 0 0 40px rgba(0,245,212,0.5), 0 0 80px rgba(123,97,255,0.3); }
    }
    .studio-card {
      animation: pop-in 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
      background: rgba(13,17,23,0.8);
      border: 1px solid rgba(0,245,212,0.15);
      border-radius: 20px;
      padding: 1.5rem;
      backdrop-filter: blur(20px);
      transition: all 0.3s ease;
    }
    .studio-card:hover {
      border-color: rgba(0,245,212,0.35);
      box-shadow: 0 8px 40px rgba(0,245,212,0.1);
      transform: translateY(-2px);
    }
    .mode-badge {
      display: inline-block;
      background: linear-gradient(135deg, rgba(0,245,212,0.15), rgba(123,97,255,0.15));
      border: 1px solid rgba(0,245,212,0.3);
      border-radius: 100px;
      padding: 0.4rem 1rem;
      font-family: 'Syne', sans-serif;
      font-size: 0.75rem;
      font-weight: 700;
      color: #00f5d4;
      letter-spacing: 0.1em;
      text-transform: uppercase;
    }
    .output-frame {
      animation: glow-pulse 3s ease-in-out infinite;
      border-radius: 16px;
      overflow: hidden;
      margin-top: 1rem;
    }
    .shimmer-text {
      background: linear-gradient(90deg, #00f5d4, #7b61ff, #ff6b6b, #00f5d4);
      background-size: 200% auto;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      animation: shimmer 3s linear infinite;
    }
    .progress-bar {
      height: 3px;
      border-radius: 3px;
      background: linear-gradient(90deg, #00f5d4, #7b61ff);
      animation: shimmer 1.5s linear infinite;
      background-size: 200% auto;
      margin: 1rem 0;
    }
    </style>
    
    <div style="text-align:center;padding:2rem 0 1.5rem;">
      <div style="display:inline-block;background:rgba(123,97,255,0.1);
                  border:1px solid rgba(123,97,255,0.25);border-radius:100px;
                  padding:0.3rem 1rem;font-size:0.75rem;color:#7b61ff;
                  letter-spacing:0.1em;text-transform:uppercase;margin-bottom:1rem;">
        🎬 UGC Level Content Creation
      </div>
      <h1 style="font-family:'Syne',sans-serif;font-size:clamp(1.8rem,4vw,3rem);
                 font-weight:800;line-height:1.1;margin-bottom:0.75rem;">
        <span class="shimmer-text">Creator Studio</span>
      </h1>
      <p style="color:#6b7280;font-size:1rem;max-width:500px;margin:0 auto;">
        Generate viral UGC content — images, videos & voiceovers — all AI-powered
      </p>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["🖼️ Text → Image", "🔄 Image → Image", "🎬 Text → Video", "📽️ Image → Video"])

    client = get_gemini_client()

    # ── Tab 1: Text to Image ──────────────────────────────────────────────────
    with tabs[0]:
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        st.markdown('<span class="mode-badge">✨ Text → Image (Free API)</span>', unsafe_allow_html=True)
        
        t2i_prompt = st.text_area(
            "Scene Description",
            placeholder="e.g. A confident young woman holding a sleek skincare bottle, golden hour lighting...",
            height=120,
            key="t2i_prompt",
            label_visibility="collapsed"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            t2i_enhance = st.toggle("✨ AI Enhance Prompt", value=True, key="t2i_enhance")
        with col2:
            t2i_style = st.selectbox("Style", 
                ["Lifestyle / Authentic", "Product Showcase", "Before/After", 
                 "Cinematic", "Social Media Native", "Minimalist"],
                key="t2i_style", label_visibility="collapsed")
        
        if st.button("🎨 Generate Image", key="t2i_gen", use_container_width=True):
            if not t2i_prompt.strip():
                st.warning("Please enter a description.")
            elif not get_key("HF_TOKEN", "hf_token"):
                st.error("🔑 Hugging Face Token Required. Add it in the Streamlit Secrets or sidebar settings.")
            else:
                with st.status("🎨 Creating your UGC image...", expanded=True) as status:
                    final_prompt = t2i_prompt.strip()
                    if t2i_enhance and client:
                        st.write("✨ Enhancing prompt with Gemini...")
                        final_prompt = enhance_prompt_with_gemini(client, 
                            f"[Style: {t2i_style}] {final_prompt}", "text-image")
                        st.write(f"📝 Enhanced: *{final_prompt[:100]}...*")
                    
                    st.write("🖼️ Connecting to Image Engines...")
                    st.markdown('<div class="progress-bar"></div>', unsafe_allow_html=True)
                    
                    img_data, err = generate_image_hf(final_prompt)
                    
                    if err:
                        status.update(label="❌ Generation failed", state="error")
                        st.error(err)
                    else:
                        status.update(label="✅ Image ready!", state="complete")
                        st.markdown('<div class="output-frame">', unsafe_allow_html=True)
                        
                        if isinstance(img_data, str) and img_data.startswith("http"):
                            st.markdown(f'<img src="{img_data}" style="width:100%; border-radius:16px; margin-bottom:1rem;">', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.info("💡 **Generated via Browser Bypass to avoid server overload.** Right-click the image and select 'Save Image As...' to download.")
                        else:
                            st.image(img_data, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.download_button("⬇️ Download Image", img_data, 
                                              "ugc_image.png", "image/png",
                                              use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Tab 2: Image to Image ─────────────────────────────────────────────────
    with tabs[1]:
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        st.markdown('<span class="mode-badge">🔄 Image → Image</span>', unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.8rem;color:#ff6b6b;'>Note: Free tier models generate a new image based entirely on your text description.</p>", unsafe_allow_html=True)
        
        i2i_upload = st.file_uploader("Upload source image", 
                                       type=["png","jpg","jpeg","webp"],
                                       key="i2i_upload",
                                       label_visibility="collapsed")
        
        if i2i_upload:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Original**")
                st.image(i2i_upload, use_container_width=True)
        
        i2i_prompt = st.text_area(
            "Transformation Description",
            placeholder="e.g. A completely new image of a golden hour lifestyle aesthetic, warm tones...",
            height=100,
            key="i2i_prompt",
            label_visibility="collapsed"
        )
        
        if st.button("🔄 Generate New Free Image", key="i2i_gen", use_container_width=True):
            if not i2i_prompt.strip():
                st.warning("Please enter a description.")
            elif not get_key("HF_TOKEN", "hf_token"):
                st.error("🔑 Hugging Face Token Required. Add it in the Streamlit Secrets or sidebar settings.")
            else:
                with st.status("🔄 Generating...", expanded=True) as status:
                    final_prompt = i2i_prompt.strip()
                    if client:
                        final_prompt = enhance_prompt_with_gemini(client, final_prompt, "text-image")
                    
                    img_data, err = generate_image_hf(final_prompt)
                    
                    if err:
                        status.update(label="❌ Failed", state="error")
                        st.error(err)
                    else:
                        status.update(label="✅ Generated!", state="complete")
                        st.markdown('<div class="output-frame">', unsafe_allow_html=True)
                        
                        if isinstance(img_data, str) and img_data.startswith("http"):
                            st.markdown(f'<img src="{img_data}" style="width:100%; border-radius:16px; margin-bottom:1rem;">', unsafe_allow_html=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.info("💡 Right-click the image and select 'Save Image As...' to download.")
                        else:
                            st.image(img_data, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                            st.download_button("⬇️ Download", img_data, "transformed.png", "image/png",
                                              use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Tab 3: Text to Video ──────────────────────────────────────────────────
    with tabs[2]:
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        st.markdown('<span class="mode-badge">🎬 Text → Video (Free API)</span>', unsafe_allow_html=True)
        
        t2v_prompt = st.text_area(
            "Scene Description",
            placeholder="e.g. A woman discovering an amazing skincare product...",
            height=100,
            key="t2v_prompt",
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### 🎙️ Voiceover Script")
        
        col1, col2 = st.columns(2)
        with col1:
            use_script = st.toggle("Add Voiceover", value=True, key="t2v_use_script")
        with col2:
            if use_script:
                auto_script = st.toggle("✨ AI Generate Script", value=True, key="t2v_auto_script")
        
        if use_script:
            script_duration = st.slider("Script Duration (seconds)", 10, 60, 15, 5, key="t2v_dur")
            
            if 'auto_script' in st.session_state and st.session_state.t2v_auto_script:
                if st.button("📝 Generate Script", key="gen_script"):
                    if client and t2v_prompt:
                        with st.spinner("Writing your script..."):
                            tone_for_script = st.session_state.get("t2v_tone", "Natural")
                            script = generate_script_with_gemini(client, t2v_prompt, 
                                                                 tone_for_script, script_duration)
                            st.session_state.generated_script = script
            
            t2v_script = st.text_area(
                "Voiceover Script",
                value=st.session_state.get("generated_script", ""),
                height=120,
                key="t2v_script"
            )
            
            st.markdown("### 🎭 Voice Agent (ElevenLabs - Free Tier Account Required)")
            v_col1, v_col2, v_col3 = st.columns(3)
            
            with v_col1:
                gender = st.selectbox("Gender", ["Male", "Female"], key="t2v_gender")
            with v_col2:
                voices = list(VOICE_AGENTS[gender].keys())
                selected_voice = st.selectbox("Voice", voices, key="t2v_voice")
            with v_col3:
                tone = st.selectbox("Tone", list(TONE_DESCRIPTIONS.keys()), key="t2v_tone")
        
        st.markdown("---")
        
        if st.button("🎬 Generate Video + Audio", key="t2v_gen", use_container_width=True):
            if not t2v_prompt.strip():
                st.warning("Please enter a scene description.")
            elif not get_key("HF_TOKEN", "hf_token"):
                st.error("🔑 Hugging Face Token Required. Add it in the Streamlit Secrets or sidebar settings.")
            else:
                with st.status("🎬 Processing Free Video Cascade...", expanded=True) as status:
                    final_prompt = t2v_prompt.strip()
                    if client:
                        st.write("✨ Enhancing prompt...")
                        final_prompt = enhance_prompt_with_gemini(client, final_prompt, "text-video")
                    
                    st.write("🎬 Generating video (Searching for open server slot)...")
                    video_data, v_err = generate_video_free(final_prompt)
                    
                    audio_data = None
                    a_err = None
                    if use_script and t2v_script.strip() and get_elevenlabs_key():
                        st.write("🎙️ Generating voiceover...")
                        voice_id = VOICE_AGENTS[gender][selected_voice]
                        audio_data, a_err = generate_tts_elevenlabs(t2v_script, voice_id, tone)
                    
                    if v_err:
                        status.update(label="❌ Cannot Generate Video", state="error")
                        st.error(v_err)
                    else:
                        status.update(label="✅ Content ready!", state="complete")
                        st.markdown('<div class="output-frame">', unsafe_allow_html=True)
                        st.video(video_data)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.download_button("⬇️ Download Video", video_data, 
                                          "ugc_video.mp4", "video/mp4",
                                          use_container_width=True)
                    
                    if audio_data:
                        st.markdown("**🎙️ Voiceover Audio:**")
                        st.audio(audio_data, format="audio/mp3")
                        st.download_button("⬇️ Download Audio", audio_data,
                                          "voiceover.mp3", "audio/mp3",
                                          use_container_width=True)
                    elif a_err:
                        st.error(a_err)
        
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Tab 4: Image to Video ─────────────────────────────────────────────────
    with tabs[3]:
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        st.markdown('<span class="mode-badge">📽️ Image → Video (Free Hack)</span>', unsafe_allow_html=True)
        st.markdown("<p style='font-size:0.8rem;color:#ff6b6b;'>Note: The free tier API generates a new video based on your text description, not strictly locked to the image structure.</p>", unsafe_allow_html=True)
        
        i2v_upload = st.file_uploader("Upload image to animate",
                                       type=["png","jpg","jpeg","webp"],
                                       key="i2v_upload",
                                       label_visibility="collapsed")
        
        if i2v_upload:
            st.image(i2v_upload, use_container_width=True)
        
        i2v_prompt = st.text_area(
            "Animation Direction",
            placeholder="e.g. Subtle camera zoom in, cinematic...",
            height=100,
            key="i2v_prompt",
            label_visibility="collapsed"
        )
        
        if st.button("📽️ Animate Image", key="i2v_gen", use_container_width=True):
            if not i2v_prompt.strip():
                st.warning("Please enter an animation description.")
            elif not get_key("HF_TOKEN", "hf_token"):
                st.error("🔑 Hugging Face Token Required.")
            else:
                with st.status("📽️ Animating your prompt via HF Cascade...", expanded=True) as status:
                    video_data, v_err = generate_video_free(i2v_prompt.strip())
                    
                    if v_err:
                        status.update(label="❌ Failed", state="error")
                        st.error(v_err)
                    else:
                        status.update(label="✅ Animated!", state="complete")
                        st.markdown('<div class="output-frame">', unsafe_allow_html=True)
                        st.video(video_data)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.download_button("⬇️ Download Video", video_data,
                                          "animated.mp4", "video/mp4",
                                          use_container_width=True)
                        
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔑 API Keys")
        
        with st.expander("Configure Additional APIs"):
            st.markdown("<small>Get a free token at huggingface.co</small>", unsafe_allow_html=True)
            hf_key = st.text_input("Hugging Face Token (Images/Video)", type="password",
                                    value=st.session_state.get("hf_token", ""),
                                    key="ugc_hf_key")
            if hf_key: st.session_state.hf_token = hf_key
            
            el_key = st.text_input("ElevenLabs (voiceovers)", type="password",
                                    value=st.session_state.get("elevenlabs_key", ""),
                                    key="ugc_el_key")
            if el_key: st.session_state.elevenlabs_key = el_key
