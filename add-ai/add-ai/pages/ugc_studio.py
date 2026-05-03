import streamlit as st
import google.generativeai as genai
import requests
import base64
import os
import time
import json
from io import BytesIO

# ── Voice Agents (Provided by User) ──────────────────────────────────────────

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

# ── Helpers (Updated for Gemini 3) ───────────────────────────────────────────

def get_gemini_client():
    key = os.environ.get("GOOGLE_API_KEY") or st.session_state.get("google_key", "")
    if key:
        genai.configure(api_key=key)
        # FIXED LINE: Use Gemini 1.5 Flash
        return genai.GenerativeModel(model_name='gemini-1.5-flash')
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

# ... generate_image_replicate, generate_video_replicate, generate_tts_elevenlabs exactly as user provided ...

def generate_script_with_claude(client, description, tone, duration_sec=15):
    """Refactored to use Gemini."""
    prompt = f"Write a {duration_sec}-second UGC video script. Style: {tone}. Product: {description}. Return ONLY spoken text."
    try:
        response = client.generate_content(prompt)
        return response.text.strip()
    except:
        return f"Script generation failed."

# ── Main Render (Keep User HTML/CSS/Tabs) ──────────────────────────────────
# (Function logic continues as provided by user...)
