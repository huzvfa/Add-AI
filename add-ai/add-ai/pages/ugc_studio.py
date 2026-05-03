import streamlit as st
import google.generativeai as genai
import requests
import base64
import os
import time
import json
from io import BytesIO

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
        return genai.GenerativeModel('gemini-1.5-flash')
    return None

def get_replicate_token():
    return os.environ.get("REPLICATE_API_TOKEN") or st.session_state.get("replicate_key", "")

def get_elevenlabs_key():
    return os.environ.get("ELEVENLABS_API_KEY") or st.session_state.get("elevenlabs_key", "")

def enhance_prompt_with_gemini(client, prompt, mode):
    """Use Gemini to enhance prompt."""
    system = "You are a UGC creative director. Transform basic prompts into highly detailed, cinematic generation prompts. Return ONLY the enhanced prompt."
    try:
        response = client.generate_content(f"{system}\n\nMode: {mode}\nOriginal prompt: {prompt}")
        return response.text.strip()
    except:
        return prompt

def generate_image_replicate(prompt, image_data=None):
    token = get_replicate_token()
    if not token: return None, "No token"
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    
    if image_data:
        payload = {
            "version": "ac732df83cea7fff18b8472768c88ad041fa750e7a4f6dab96d1c8b26dfd0a7e",
            "input": {"prompt": prompt, "image": f"data:image/png;base64,{image_data}", "prompt_strength": 0.75}
        }
    else:
        payload = {
            "version": "black-forest-labs/flux-schnell",
            "input": {"prompt": prompt, "aspect_ratio": "1:1"}
        }
    
    try:
        resp = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload)
        pred_id = resp.json()["id"]
        for _ in range(60):
            time.sleep(2)
            poll = requests.get(f"https://api.replicate.com/v1/predictions/{pred_id}", headers=headers)
            result = poll.json()
            if result["status"] == "succeeded":
                img_url = result["output"][0] if isinstance(result["output"], list) else result["output"]
                return requests.get(img_url).content, None
        return None, "Timeout"
    except Exception as e: return None, str(e)

def generate_video_replicate(prompt, image_data=None):
    token = get_replicate_token()
    if not token: return None, "No token"
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    
    if image_data:
        payload = {
            "version": "stability-ai/stable-video-diffusion:3f0457e4619daac51203dedb472816fd4af51f3149fa7a9e0b5ffcf1b8172438",
            "input": {"input_image": f"data:image/png;base64,{image_data}"}
        }
    else:
        payload = {
            "version": "9f747673945c62801b13b84701c783929c0ee784e4748ec062204894dda1a351",
            "input": {"prompt": prompt}
        }
    
    try:
        resp = requests.post("https://api.replicate.com/v1/predictions", headers=headers, json=payload)
        pred_id = resp.json()["id"]
        for _ in range(120):
            time.sleep(3)
            poll = requests.get(f"https://api.replicate.com/v1/predictions/{pred_id}", headers=headers)
            result = poll.json()
            if result["status"] == "succeeded":
                url = result["output"][0] if isinstance(result["output"], list) else result["output"]
                return requests.get(url).content, None
        return None, "Timeout"
    except Exception as e: return None, str(e)

def generate_tts_elevenlabs(script, voice_id, tone):
    api_key = get_elevenlabs_key()
    if not api_key: return None, "No key"
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    headers = {"xi-api-key": api_key, "Content-Type": "application/json"}
    payload = {"text": script, "model_id": "eleven_multilingual_v2"}
    try:
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code == 200: return resp.content, None
        return None, resp.text
    except Exception as e: return None, str(e)

def generate_script_with_gemini(client, description, tone, duration_sec=15):
    prompt = f"Write a {duration_sec}-second UGC video script. Style: {tone}. Product: {description}. Return ONLY spoken script."
    try:
        response = client.generate_content(prompt)
        return response.text.strip()
    except:
        return "Script failed."

# ── Main Render ───────────────────────────────────────────────────────────────

def render():
    st.markdown("""
    <style>
    @keyframes shimmer { 0% { background-position: -200% center; } 100% { background-position: 200% center; } }
    .studio-card {
      background: rgba(13,17,23,0.8);
      border: 1px solid rgba(0,245,212,0.15);
      border-radius: 20px;
      padding: 1.5rem;
      backdrop-filter: blur(20px);
    }
    .shimmer-text {
      background: linear-gradient(90deg, #00f5d4, #7b61ff, #ff6b6b, #00f5d4);
      background-size: 200% auto;
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      animation: shimmer 3s linear infinite;
    }
    </style>
    <div style="text-align:center;padding:2rem 0 1.5rem;">
      <h1 class="shimmer-text" style="font-family:'Syne',sans-serif;font-size:3rem;">Creator Studio</h1>
    </div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["🖼️ Text → Image", "🔄 Image → Image", "🎬 Text → Video", "📽️ Image → Video"])
    client = get_gemini_client()

    with tabs[0]:
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        t2i_prompt = st.text_area("Scene Description", key="t2i_prompt")
        if st.button("🎨 Generate Image", key="t2i_gen", use_container_width=True):
            if not t2i_prompt: st.warning("Enter prompt")
            else:
                with st.spinner("Generating..."):
                    final_p = enhance_prompt_with_gemini(client, t2i_prompt, "image") if client else t2i_prompt
                    img, err = generate_image_replicate(final_p)
                    if img: st.image(img)
                    else: st.error(err)
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[1]:
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        i2i_upload = st.file_uploader("Source Image", key="i2i_upload")
        i2i_prompt = st.text_area("Transformation", key="i2i_prompt")
        if st.button("🔄 Transform", key="i2i_gen", use_container_width=True):
            if i2i_upload:
                img_b64 = base64.b64encode(i2i_upload.read()).decode()
                img, err = generate_image_replicate(i2i_prompt, img_b64)
                if img: st.image(img)
                else: st.error(err)
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[2]:
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        t2v_prompt = st.text_area("Scene", key="t2v_prompt")
        t2v_script_area = st.text_area("Script", key="t2v_script")
        if st.button("🎬 Generate Video", key="t2v_gen", use_container_width=True):
            vid, err = generate_video_replicate(t2v_prompt)
            if vid: st.video(vid)
            else: st.error(err)
        st.markdown('</div>', unsafe_allow_html=True)

    with tabs[3]:
        st.markdown('<div class="studio-card">', unsafe_allow_html=True)
        i2v_upload = st.file_uploader("Image to animate", key="i2v_upload")
        if st.button("📽️ Animate", key="i2v_gen", use_container_width=True):
            if i2v_upload:
                img_b64 = base64.b64encode(i2v_upload.read()).decode()
                vid, err = generate_video_replicate("motion", img_b64)
                if vid: st.video(vid)
                else: st.error(err)
        st.markdown('</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 🔑 API Keys")
        st.text_input("Replicate Token", type="password", key="replicate_key")
        st.text_input("ElevenLabs Key", type="password", key="elevenlabs_key")
