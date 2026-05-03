import streamlit as st
import google.generativeai as genai
import requests
import base64
import os
import time
import json
from io import BytesIO

# ... (VOICE_AGENTS and TONE_DESCRIPTIONS exactly as provided) ...

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

def enhance_prompt_with_claude(client, prompt, mode):
    """Refactored to use Gemini."""
    system = """You are a UGC (User Generated Content) creative director. Return ONLY the enhanced prompt, nothing else."""
    try:
        response = client.generate_content(f"{system}\n\nMode: {mode}\n\nOriginal prompt: {prompt}")
        return response.text.strip()
    except:
        return prompt

# ... (generate_image_replicate, generate_video_replicate, generate_tts_elevenlabs exactly as provided) ...

def generate_script_with_claude(client, description, tone, duration_sec=15):
    """Refactored to use Gemini."""
    prompt = f"Write a {duration_sec}-second UGC video script. Style: {tone}. Product: {description}. Return ONLY spoken text."
    try:
        response = client.generate_content(prompt)
        return response.text.strip()
    except:
        return f"Script generation failed."

# ... (render() function exactly as provided, just ensuring it calls get_gemini_client()) ...
def render():
    # ... All your HTML/CSS/Tabs logic stays here ...
    client = get_gemini_client()
    # ... rest of your code ...
