import streamlit as st
import google.generativeai as genai
import requests
import base64
import os
import time
import json
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

# ── Helpers ───────────────────────────────────────────────────────────────────

def get_gemini_client():
    key = os.environ.get("GOOGLE_API_KEY") or st.session_state.get("google_key", "")
    if key:
        genai.configure(api_key=key)
        return genai.GenerativeModel(model_name='gemini-2.5-flash')
    return None

def get_replicate_token():
    return os.environ.get("REPLICATE_API_TOKEN") or st.session_state.get("replicate_key", "")

def get_elevenlabs_key():
    return os.environ.get("ELEVENLABS_API_KEY") or st.session_state.get("elevenlabs_key", "")

def enhance_prompt_with_gemini(client, prompt, mode):
    system = """You are a UGC (User Generated Content) creative director. Transform basic prompts into highly detailed, cinematic generation prompts. Return ONLY the enhanced prompt, nothing else."""
    try:
        response = client.generate_content(f"{system}\n\nMode: {mode}\n\nOriginal prompt: {prompt}")
        return response.text.strip()
    except:
        return prompt

def generate_image_replicate(prompt, image_data=None):
    token = get_replicate_token()
    if not token:
        return None, "No Replicate API token provided"
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    if image_data:
        payload = {
            "version": "ac732df83cea7fff18b8472768c88ad041fa750e7a4f6dab96d1c8b26dfd0a7e",
            "input": {
                "prompt": prompt,
                "image": f"data:image/png;base64,{image_data}",
                "prompt_strength": 0.75,
                "num_inference_steps": 30,
                "guidance_scale": 7.5
            }
        }
    else:
        payload = {
            "version": "black-forest-labs/flux-schnell",
            "input": {
                "prompt": prompt,
                "num_outputs": 1,
                "aspect_ratio": "1:1",
                "output_format": "webp",
                "output_quality": 90
            }
        }
    
    try:
        resp = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload, timeout=30)
        if resp.status_code != 201:
            return None, f"API Error: {resp.status_code} - {resp.text[:200]}"
        
        prediction = resp.json()
        pred_id = prediction["id"]
        
        for _ in range(60):
            time.sleep(2)
            poll = requests.get(f"https://api.replicate.com/v1/predictions/{pred_id}", headers=headers, timeout=10)
            result = poll.json()
            
            if result["status"] == "succeeded":
                output = result.get("output", [])
                if isinstance(output, list) and output:
                    img_url = output[0]
                elif isinstance(output, str):
                    img_url = output
                else:
                    return None, "No output URL in response"
                
                img_resp = requests.get(img_url, timeout=30)
                return img_resp.content, None
            elif result["status"] == "failed":
                return None, f"Generation failed: {result.get('error', 'Unknown error')}"
        
        return None, "Timeout: Generation took too long"
    except Exception as e:
        return None, str(e)

def generate_video_replicate(prompt, image_data=None):
    token = get_replicate_token()
    if not token:
        return None, "No Replicate API token"
    
    headers = {
        "Authorization": f"Token {token}",
        "Content-Type": "application/json"
    }
    
    if image_data:
        payload = {
            "version": "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438",
            "input": {
                "input_image": f"data:image/png;base64,{image_data}",
                "video_length": "25_frames_with_svd_xt",
                "sizing_strategy": "maintain_aspect_ratio",
                "frames_per_second": 6,
                "motion_bucket_id": 127,
                "cond_aug": 0.02,
                "decoding_t": 7,
            }
        }
    else:
        payload = {
            "version": "9f747673945c62801b13b84701c783929c0ee784e4748ec062204894dda1a351",
            "input": {
                "prompt": prompt,
                "num_frames": 24,
                "num_inference_steps": 50,
                "fps": 8,
                "width": 576,
                "height": 320
            }
        }
    
    try:
        resp = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload, timeout=30)
        if resp.status_code != 201:
            return None, f"API Error: {resp.status_code}"
        
        pred_id = resp.json()["id"]
        
        for _ in range(120):
            time.sleep(3)
            poll = requests.get(f"https://api.replicate.com/v1/predictions/{pred_id}", headers=headers, timeout=10)
            result = poll.json()
            
            if result["status"] == "succeeded":
                output = result.get("output", [])
                url = output[0] if isinstance(output, list) else output
                video_resp = requests.get(url, timeout=60)
                return video_resp.content, None
            elif result["status"] == "failed":
                return None, f"Failed: {result.get('error', 'Unknown')}"
        
        return None, "Timeout"
    except Exception as e:
        return None, str(e)

def generate_tts_elevenlabs(script, voice_id, tone, stability=0.5, similarity=0.75):
    api_key = get_elevenlabs_key()
    if not api_key:
        return None, "No ElevenLabs API key"
    
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
    }
    .voice-pill {
      background: rgba(123,97,255,0.1);
      border: 1px solid rgba(123,97,255,0.25);
      border-radius: 100px;
      padding: 0.3rem 0.8rem;
      font-size: 0.8rem;
      color: #7b61ff;
      cursor: pointer;
      transition: all 0.2s;
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

    with tabs[0]:
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        st.markdown('<span class="mode-badge">✨ Text → Image</span>', unsafe_allow_html=True)
        st.markdown("""
        <p style="color:#9ca3af;font-size:0.9rem;margin:0.75rem 0;">
        Describe your UGC scene and AI will craft a production-ready image.
        </p>
        """, unsafe_allow_html=True)
        
        t2i_prompt = st.text_area(
            "Scene Description",
            placeholder="e.g. A confident young woman holding a sleek skincare bottle, golden hour lighting, lifestyle aesthetic, soft bokeh background, authentic UGC feel...",
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
            elif not get_replicate_token():
                st.error("🔑 Add your Replicate API token in the sidebar to generate images.")
            else:
                with st.status("🎨 Creating your UGC image...", expanded=True) as status:
                    st.write("🧠 Analyzing your vision...")
                    
                    final_prompt = t2i_prompt.strip()
                    if t2i_enhance and client:
                        st.write("✨ Enhancing prompt with AI...")
                        final_prompt = enhance_prompt_with_gemini(client, 
                            f"[Style: {t2i_style}] {final_prompt}", "text-image")
                        st.write(f"📝 Enhanced: *{final_prompt[:100]}...*" if len(final_prompt) > 100 else f"📝 Enhanced: *{final_prompt}*")
                    
                    st.write("🖼️ Generating image...")
                    st.markdown('<div class="progress-bar"></div>', unsafe_allow_html=True)
                    
                    img_data, err = generate_image_replicate(final_prompt)
                    
                    if err:
                        status.update(label="❌ Generation failed", state="error")
                        st.error(f"Error: {err}")
                    else:
                        status.update(label="✅ Image ready!", state="complete")
                        st.markdown('<div class="output-frame">', unsafe_allow_html=True)
                        st.image(img_data, use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                        st.download_button("⬇️ Download Image", img_data, 
                                          "ugc_image.webp", "image/webp",
                                          use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        st.markdown('<span class="mode-badge">🔄 Image → Image</span>', unsafe_allow_html=True)
        
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
            placeholder="e.g. Transform to golden hour lifestyle aesthetic, warm tones, authentic UGC style, slight film grain...",
            height=100,
            key="i2i_prompt",
            label_visibility="collapsed"
        )
        
        i2i_strength = st.slider("Transformation Strength", 0.3, 0.95, 0.7, 0.05,
                                  help="Higher = more transformation, lower = closer to original")
        
        if st.button("🔄 Transform Image", key="i2i_gen", use_container_width=True):
            if not i2i_upload:
                st.warning("Please upload an image.")
            elif not i2i_prompt.strip():
                st.warning("Please enter a transformation description.")
            elif not get_replicate_token():
                st.error("🔑 Add your Replicate API token in the sidebar.")
            else:
                with st.status("🔄 Transforming your image...", expanded=True) as status:
                    img_b64 = base64.b64encode(i2i_upload.read()).decode()
                    
                    final_prompt = i2i_prompt.strip()
                    if client:
                        final_prompt = enhance_prompt_with_gemini(client, final_prompt, "image-image")
                    
                    img_data, err = generate_image_replicate(final_prompt, img_b64)
                    
                    if err:
                        status.update(label="❌ Failed", state="error")
                        st.error(f"Error: {err}")
                    else:
                        status.update(label="✅ Transformed!", state="complete")
                        with col2:
                            st.markdown("**Transformed**")
                            st.markdown('<div class="output-frame">', unsafe_allow_html=True)
                            st.image(img_data, use_container_width=True)
                            st.markdown('</div>', unsafe_allow_html=True)
                        st.download_button("⬇️ Download", img_data, "transformed.webp", "image/webp",
                                          use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        st.markdown('<span class="mode-badge">🎬 Text → Video</span>', unsafe_allow_html=True)
        
        t2v_prompt = st.text_area(
            "Scene Description",
            placeholder="e.g. A woman discovering an amazing skincare product, close-up reaction, holding product up, natural lighting, authentic and relatable...",
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
                placeholder="What the narrator or character says in the video...",
                height=120,
                key="t2v_script"
            )
            
            st.markdown("### 🎭 Voice Agent")
            v_col1, v_col2, v_col3 = st.columns(3)
            
            with v_col1:
                gender = st.selectbox("Gender", ["Male", "Female"], key="t2v_gender")
            with v_col2:
                voices = list(VOICE_AGENTS[gender].keys())
                selected_voice = st.selectbox("Voice", voices, key="t2v_voice")
            with v_col3:
                tone = st.selectbox("Tone", list(TONE_DESCRIPTIONS.keys()), key="t2v_tone")
            
            st.markdown(f"""
            <div style="background:rgba(123,97,255,0.08);border:1px solid rgba(123,97,255,0.2);
                        border-radius:12px;padding:0.75rem;font-size:0.8rem;color:#9ca3af;margin:0.5rem 0;">
              🎙️ <strong style="color:#7b61ff;">{selected_voice}</strong> · {TONE_DESCRIPTIONS.get(tone, '')}
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("▶️ Preview Voice", key="preview_voice"):
                preview_text = t2v_script[:100] if t2v_script else "This is a preview of your selected voice agent."
                if not get_elevenlabs_key():
                    st.error("🔑 Add ElevenLabs API key in sidebar for voice preview.")
                else:
                    with st.spinner("Generating voice preview..."):
                        voice_id = VOICE_AGENTS[gender][selected_voice]
                        audio, err = generate_tts_elevenlabs(preview_text, voice_id, tone)
                        if audio:
                            st.audio(audio, format="audio/mp3")
                        else:
                            st.error(f"Voice preview failed: {err}")
        
        st.markdown("---")
        
        if st.button("🎬 Generate Video + Audio", key="t2v_gen", use_container_width=True):
            if not t2v_prompt.strip():
                st.warning("Please enter a scene description.")
            elif not get_replicate_token():
                st.error("🔑 Add Replicate API token in sidebar.")
            else:
                with st.status("🎬 Creating your UGC video...", expanded=True) as status:
                    final_prompt = t2v_prompt.strip()
                    if client:
                        st.write("✨ Enhancing prompt...")
                        final_prompt = enhance_prompt_with_gemini(client, final_prompt, "text-video")
                    
                    st.write("🎬 Generating video (this takes 2-3 minutes)...")
                    video_data, v_err = generate_video_replicate(final_prompt)
                    
                    audio_data = None
                    if use_script and t2v_script.strip() and get_elevenlabs_key():
                        st.write("🎙️ Generating voiceover...")
                        voice_id = VOICE_AGENTS[gender][selected_voice]
                        audio_data, a_err = generate_tts_elevenlabs(t2v_script, voice_id, tone)
                    
                    if v_err and not video_data:
                        status.update(label="❌ Video generation failed", state="error")
                        st.error(f"Video error: {v_err}")
                    else:
                        status.update(label="✅ Content ready!", state="complete")
                        
                        if video_data:
                            st.video(video_data)
                            st.download_button("⬇️ Download Video", video_data, 
                                              "ugc_video.mp4", "video/mp4",
                                              use_container_width=True)
                        
                        if audio_data:
                            st.markdown("**🎙️ Voiceover Audio:**")
                            st.audio(audio_data, format="audio/mp3")
                            st.download_button("⬇️ Download Audio", audio_data,
                                              "voiceover.mp3", "audio/mp3",
                                              use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[3]:
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        st.markdown('<span class="mode-badge">📽️ Image → Video</span>', unsafe_allow_html=True)
        
        i2v_upload = st.file_uploader("Upload image to animate",
                                       type=["png","jpg","jpeg","webp"],
                                       key="i2v_upload",
                                       label_visibility="collapsed")
        
        if i2v_upload:
            st.image(i2v_upload, use_container_width=True)
        
        i2v_prompt = st.text_area(
            "Animation Direction",
            placeholder="e.g. Subtle camera zoom in, product rotates slowly, steam rising, hair blowing gently in breeze...",
            height=100,
            key="i2v_prompt",
            label_visibility="collapsed"
        )
        
        st.markdown("---")
        st.markdown("### 🎙️ Add Voiceover")
        
        i2v_use_voice = st.toggle("Add Voiceover Script", value=False, key="i2v_use_voice")
        
        if i2v_use_voice:
            i2v_script = st.text_area("Script", 
                                       placeholder="What should the narrator say?",
                                       height=80, key="i2v_script")
            
            v_col1, v_col2, v_col3 = st.columns(3)
            with v_col1:
                i2v_gender = st.selectbox("Gender", ["Male", "Female"], key="i2v_gender")
            with v_col2:
                i2v_voice = st.selectbox("Voice", list(VOICE_AGENTS[i2v_gender].keys()), key="i2v_voice")
            with v_col3:
                i2v_tone = st.selectbox("Tone", list(TONE_DESCRIPTIONS.keys()), key="i2v_tone")
        
        motion = st.select_slider("Motion Intensity", 
                                   ["Subtle", "Gentle", "Moderate", "Dynamic", "Intense"],
                                   value="Moderate", key="i2v_motion")
        
        if st.button("📽️ Animate Image", key="i2v_gen", use_container_width=True):
            if not i2v_upload:
                st.warning("Please upload an image to animate.")
            elif not get_replicate_token():
                st.error("🔑 Add Replicate API token in sidebar.")
            else:
                with st.status("📽️ Animating your image...", expanded=True) as status:
                    img_b64 = base64.b64encode(i2v_upload.read()).decode()
                    
                    prompt = i2v_prompt.strip() or f"{motion.lower()} motion, cinematic, smooth"
                    video_data, v_err = generate_video_replicate(prompt, img_b64)
                    
                    audio_data = None
                    if i2v_use_voice and i2v_script.strip() and get_elevenlabs_key():
                        st.write("🎙️ Generating voiceover...")
                        voice_id = VOICE_AGENTS[i2v_gender][i2v_voice]
                        audio_data, _ = generate_tts_elevenlabs(i2v_script, voice_id, i2v_tone)
                    
                    if v_err and not video_data:
                        status.update(label="❌ Failed", state="error")
                        st.error(f"Error: {v_err}")
                    else:
                        status.update(label="✅ Animated!", state="complete")
                        if video_data:
                            st.video(video_data)
                            st.download_button("⬇️ Download Video", video_data,
                                              "animated.mp4", "video/mp4",
                                              use_container_width=True)
                        if audio_data:
                            st.audio(audio_data, format="audio/mp3")
                            st.download_button("⬇️ Download Audio", audio_data,
                                              "voiceover.mp3", "audio/mp3",
                                              use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔑 API Keys")
        
        with st.expander("Configure Additional APIs"):
            rep_key = st.text_input("Replicate (images/videos)", type="password",
                                     value=st.session_state.get("replicate_key", ""),
                                     key="ugc_rep_key")
            if rep_key: st.session_state.replicate_key = rep_key
            
            el_key = st.text_input("ElevenLabs (voiceovers)", type="password",
                                    value=st.session_state.get("elevenlabs_key", ""),
                                    key="ugc_el_key")
            if el_key: st.session_state.elevenlabs_key = el_key
