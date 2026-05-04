import streamlit as st
import io
import os
import base64
import time
import hashlib
import tempfile
from pathlib import Path

# ── Optional local model imports (graceful fallbacks) ────────────────────────
try:
    import torch
    HAS_TORCH = True
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
except ImportError:
    HAS_TORCH = False
    DEVICE = "cpu"

try:
    from diffusers import StableDiffusionPipeline, StableDiffusionImg2ImgPipeline
    HAS_DIFFUSERS = True
except ImportError:
    HAS_DIFFUSERS = False

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

try:
    import cv2
    import numpy as np
    HAS_CV = True
except ImportError:
    HAS_CV = False

try:
    import mediapipe as mp
    HAS_MEDIAPIPE = True
except ImportError:
    HAS_MEDIAPIPE = False

# ════════════════════════════════════════════════════════════════
#  ENGINE IDENTITY
# ════════════════════════════════════════════════════════════════

ENGINE_NAME = "ADDCORE-VISUAL"
CREATOR     = "Huzaifa Baig"

# ════════════════════════════════════════════════════════════════
#  VOICE AGENTS — local TTS, no APIs
# ════════════════════════════════════════════════════════════════

VOICE_AGENTS = {
    "Male": {
        "Marcus (Deep & Authoritative)": {"rate": 150, "pitch": 0.85, "voice_idx": 0},
        "James (Warm & Professional)":   {"rate": 165, "pitch": 0.95, "voice_idx": 0},
        "Liam (Young & Energetic)":      {"rate": 185, "pitch": 1.05, "voice_idx": 0},
        "Ethan (Smooth & Confident)":    {"rate": 160, "pitch": 0.90, "voice_idx": 0},
        "Noah (Casual & Friendly)":      {"rate": 170, "pitch": 1.00, "voice_idx": 0},
    },
    "Female": {
        "Aria (Clear & Professional)":  {"rate": 170, "pitch": 1.10, "voice_idx": 1},
        "Sofia (Warm & Empathetic)":    {"rate": 160, "pitch": 1.05, "voice_idx": 1},
        "Luna (Energetic & Bright)":    {"rate": 190, "pitch": 1.15, "voice_idx": 1},
        "Emma (Calm & Reassuring)":     {"rate": 150, "pitch": 1.00, "voice_idx": 1},
        "Zoe (Youthful & Vibrant)":     {"rate": 195, "pitch": 1.20, "voice_idx": 1},
    }
}

TONE_DESCRIPTIONS = {
    "Natural":      "conversational, natural delivery",
    "Enthusiastic": "high energy, excited",
    "Professional": "formal, polished, corporate",
    "Dramatic":     "theatrical, cinematic",
    "Calm":         "slow, calm, meditative",
    "Persuasive":   "sales-oriented, compelling",
}

TONE_RATE_MOD = {
    "Natural": 1.0, "Enthusiastic": 1.15, "Professional": 0.95,
    "Dramatic": 0.85, "Calm": 0.80, "Persuasive": 1.05,
}

# ════════════════════════════════════════════════════════════════
#  AUTONOMOUS PROMPT ENHANCEMENT
# ════════════════════════════════════════════════════════════════

_STYLE_MODIFIERS = {
    "Lifestyle / Authentic": "golden hour lighting, authentic lifestyle, warm tones, soft bokeh",
    "Product Showcase":      "clean product shot, studio lighting, sharp focus, neutral background",
    "Before/After":          "split composition, transformation theme, dramatic reveal",
    "Cinematic":             "cinematic wide shot, dramatic lighting, film grain, 4K",
    "Social Media Native":   "vertical format, bright colors, trendy aesthetic, UGC native",
    "Minimalist":            "minimalist composition, negative space, clean lines, elegant",
}

_MOTION_WORDS = {
    "Subtle":   "very subtle gentle motion",
    "Gentle":   "smooth gentle camera drift",
    "Moderate": "moderate camera movement, steady pan",
    "Dynamic":  "dynamic camera movement, energetic motion",
    "Intense":  "intense fast motion, high energy",
}

def enhance_prompt(prompt: str, mode: str, style: str = "", motion: str = "") -> str:
    base = prompt.strip().rstrip(".")
    if mode == "text-image":
        mod = _STYLE_MODIFIERS.get(style, "authentic UGC style")
        return f"{base}, {mod}, high resolution, professional photography"[:480]
    elif mode == "image-image":
        mod = _STYLE_MODIFIERS.get(style, "UGC lifestyle")
        return f"{base}, {mod}, seamless transfer, professional"[:480]
    elif mode == "text-video":
        return f"{base}, smooth cinematic motion, authentic UGC, natural lighting"[:480]
    elif mode == "image-video":
        m = _MOTION_WORDS.get(motion, "smooth natural motion")
        return f"{base}, {m}, realistic, smooth interpolation"[:480]
    return f"{base}, high quality, detailed"[:480]


# ════════════════════════════════════════════════════════════════
#  LOCAL IMAGE GENERATION (Stable Diffusion — runs on YOUR machine)
# ════════════════════════════════════════════════════════════════

@st.cache_resource(show_spinner=False)
def load_sd_pipeline():
    """Load Stable Diffusion locally (one-time ~4GB download, then cached)."""
    if not HAS_DIFFUSERS:
        return None, "Install: pip install diffusers transformers torch accelerate"
    try:
        dtype = torch.float16 if DEVICE == "cuda" else torch.float32
        pipe = StableDiffusionPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=dtype,
            safety_checker=None,
        )
        pipe = pipe.to(DEVICE)
        if DEVICE == "cuda":
            pipe.enable_attention_slicing()
        return pipe, None
    except Exception as e:
        return None, f"Model load failed: {e}"

@st.cache_resource(show_spinner=False)
def load_sd_img2img():
    if not HAS_DIFFUSERS:
        return None, "diffusers not installed"
    try:
        dtype = torch.float16 if DEVICE == "cuda" else torch.float32
        pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            torch_dtype=dtype,
            safety_checker=None,
        )
        pipe = pipe.to(DEVICE)
        return pipe, None
    except Exception as e:
        return None, str(e)

def generate_image_local(prompt: str, progress_callback=None):
    """Generate image entirely locally — no APIs."""
    pipe, err = load_sd_pipeline()
    if err: return None, err
    try:
        steps = 25 if DEVICE == "cuda" else 15
        result = pipe(prompt, num_inference_steps=steps, guidance_scale=7.5, height=512, width=512)
        img = result.images[0]
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), None
    except Exception as e:
        return None, str(e)

def generate_img2img_local(prompt: str, init_image_bytes: bytes, strength: float = 0.7):
    pipe, err = load_sd_img2img()
    if err: return None, err
    try:
        init = Image.open(io.BytesIO(init_image_bytes)).convert("RGB").resize((512, 512))
        steps = 25 if DEVICE == "cuda" else 15
        result = pipe(prompt=prompt, image=init, strength=strength,
                      guidance_scale=7.5, num_inference_steps=steps)
        img = result.images[0]
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue(), None
    except Exception as e:
        return None, str(e)


# ════════════════════════════════════════════════════════════════
#  LOCAL TTS (pyttsx3 — works fully offline)
# ════════════════════════════════════════════════════════════════

def generate_tts_local(text: str, voice_settings: dict, tone: str):
    """Generate voiceover entirely offline using pyttsx3."""
    if not HAS_TTS:
        return None, "Install: pip install pyttsx3"
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            out_path = tmp.name
        engine = pyttsx3.init()
        rate = int(voice_settings["rate"] * TONE_RATE_MOD.get(tone, 1.0))
        engine.setProperty('rate', rate)
        engine.setProperty('volume', 1.0)
        voices = engine.getProperty('voices')
        if voices and voice_settings["voice_idx"] < len(voices):
            engine.setProperty('voice', voices[voice_settings["voice_idx"]].id)
        engine.save_to_file(text, out_path)
        engine.runAndWait()
        with open(out_path, "rb") as f:
            audio = f.read()
        try: os.remove(out_path)
        except: pass
        return audio, None
    except Exception as e:
        return None, str(e)


# ════════════════════════════════════════════════════════════════
#  LOCAL SCRIPT GENERATION (template-based, no AI API)
# ════════════════════════════════════════════════════════════════

SCRIPT_TEMPLATES = {
    "Natural": [
        "Okay so I just tried {topic} and honestly? I had no idea it would be this good. {detail} If you've been on the fence, this is your sign.",
        "Real talk — {topic}. I was skeptical at first, but {detail}. Now I'm telling everyone.",
    ],
    "Enthusiastic": [
        "STOP scrolling! You NEED to see {topic}! {detail} I am OBSESSED. Run, don't walk!",
        "Guys! {topic} just changed EVERYTHING for me! {detail} You have to try this!",
    ],
    "Professional": [
        "Today we're examining {topic}. {detail} Let's break down why this matters.",
        "Introducing {topic} — a thoughtful approach to elevated everyday living. {detail}",
    ],
    "Dramatic": [
        "They said it couldn't be done. Then came {topic}. {detail} Everything changed.",
        "In a world full of options... {topic} stands apart. {detail} This is the moment.",
    ],
    "Calm": [
        "Take a breath. Let me tell you about {topic}. {detail} It's that simple.",
        "Sometimes the best things are the quietest. {topic}. {detail}",
    ],
    "Persuasive": [
        "Here's the truth about {topic}: {detail} If you're not using this yet, you're behind. Start today.",
        "Why settle? {topic} is the upgrade you've been waiting for. {detail} Don't wait.",
    ],
}

def generate_script_local(description: str, tone: str, duration_sec: int) -> str:
    import random
    templates = SCRIPT_TEMPLATES.get(tone, SCRIPT_TEMPLATES["Natural"])
    seed = int(hashlib.md5(f"{description}{tone}{duration_sec}".encode()).hexdigest()[:8], 16)
    random.seed(seed)
    template = random.choice(templates)
    parts = description.split('.')
    topic = parts[0].strip()[:80] if parts else description[:80]
    detail = parts[1].strip()[:120] if len(parts) > 1 else "It really lives up to the hype."
    script = template.format(topic=topic, detail=detail)
    target_words = duration_sec * 2  # ~2 words/sec
    words = script.split()
    if len(words) > target_words:
        script = " ".join(words[:target_words])
    return script


# ════════════════════════════════════════════════════════════════
#  MOTION TRANSFER (UGC core — character does YOUR moves)
# ════════════════════════════════════════════════════════════════

def extract_pose_keypoints(video_bytes: bytes):
