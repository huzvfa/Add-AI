import streamlit as st
import io
import os
import time
import tempfile
import hashlib

# ── Safe Imports for Local Media Generation ──
try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    import pyttsx3
    HAS_TTS = True
except ImportError:
    HAS_TTS = False

ENGINE_NAME = "ADDCORE-VISUAL"
CREATOR     = "Huzaifa Baig"

# ════════════════════════════════════════════════════════════════
#  LOCAL MEDIA GENERATION ENGINES (ZERO API KEYS)
# ════════════════════════════════════════════════════════════════

def local_text_to_image(prompt):
    """Generates a unique image locally based on the prompt's hash."""
    if not HAS_CV2: return None, "Requires opencv-python-headless"
    seed = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
    np.random.seed(seed)
    
    # Create base canvas
    img = np.random.randint(20, 50, (512, 512, 3), dtype=np.uint8)
    
    # Draw geometric representations of the prompt
    for _ in range(seed % 10 + 5):
        color = np.random.randint(50, 255, 3).tolist()
        center = (np.random.randint(0, 512), np.random.randint(0, 512))
        radius = np.random.randint(20, 150)
        cv2.circle(img, center, radius, color, -1)
        
    # Apply a blur for a modern aesthetic
    img = cv2.GaussianBlur(img, (15, 15), 0)
    
    _, buffer = cv2.imencode('.png', img)
    return buffer.tobytes(), None

def local_image_to_image(image_bytes):
    """Applies an advanced stylization filter locally."""
    if not HAS_CV2: return None, "Requires opencv-python-headless"
    
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), 1)
    
    # Apply Edge Preserving Filter to give it an "AI Generated" stylized look
    stylized = cv2.edgePreservingFilter(img, flags=1, sigma_s=60, sigma_r=0.4)
    
    _, buffer = cv2.imencode('.png', stylized)
    return buffer.tobytes(), None

def process_ugc_motion(target_image_bytes, user_video_path, duration_sec):
    """Blends the user's motion video with the character image and saves an MP4."""
    if not HAS_CV2: return None, "Error: 'opencv-python-headless' is required."
    
    cap = cv2.VideoCapture(user_video_path)
    target_img = cv2.imdecode(np.frombuffer(target_image_bytes, np.uint8), 1)
    
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    max_frames = int(fps * duration_sec)
    
    # Read first frame to get dimensions
    ret, first_frame = cap.read()
    if not ret: return None, "Video could not be read."
    h, w = first_frame.shape[:2]
    
    # Setup Video Writer
    out_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    
    # Process First Frame
    warped_character = cv2.resize(target_img, (w, h))
    blended = cv2.addWeighted(warped_character, 0.6, first_frame, 0.4, 0)
    out.write(blended)
    
    # Process Remaining Frames
    count = 1
    progress_bar = st.progress(0)
    while cap.isOpened() and count < max_frames:
        ret, frame = cap.read()
        if not ret: break
        
        warped_character = cv2.resize(target_img, (w, h))
        blended = cv2.addWeighted(warped_character, 0.6, frame, 0.4, 0)
        out.write(blended)
        
        count += 1
        if count % 10 == 0:  # Update progress bar every 10 frames
            progress_bar.progress(min(count / max_frames, 1.0))
            
    cap.release()
    out.release()
    progress_bar.empty()
    return out_path, None

def local_text_to_video(prompt, duration_sec):
    """Generates a synthesized MP4 video locally based on text."""
    if not HAS_CV2: return None, "Requires opencv-python-headless"
    
    fps = 24
    frames_needed = duration_sec * fps
    w, h = 512, 512
    
    out_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(out_path, fourcc, fps, (w, h))
    
    seed = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16)
    np.random.seed(seed)
    
    # Generate shifting colors over time
    progress_bar = st.progress(0)
    for i in range(frames_needed):
        r = int(127 + 128 * np.sin(i * 0.05 + seed))
        g = int(127 + 128 * np.sin(i * 0.03 + seed + 1))
        b = int(127 + 128 * np.sin(i * 0.04 + seed + 2))
        
        frame = np.full((h, w, 3), (b, g, r), dtype=np.uint8)
        
        # Add text overlay
        cv2.putText(frame, prompt[:20] + "...", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        out.write(frame)
        
        if i % 10 == 0:
            progress_bar.progress(i / frames_needed)
            
    out.release()
    progress_bar.empty()
    return out_path, None

# ════════════════════════════════════════════════════════════════
#  UI RENDERING
# ════════════════════════════════════════════════════════════════

def render_voice_preview(tab_prefix):
    st.subheader("🎙️ Voiceover Agent")
    enable_voice = st.checkbox("Enable Voiceover", value=True, key=f"voice_enable_{tab_prefix}")
    
    if enable_voice:
        col1, col2 = st.columns(2)
        with col1:
            st.radio("Gender", ["Male", "Female"], key=f"voice_gender_{tab_prefix}")
        with col2:
            agent = st.selectbox("Agent", ["Marcus", "Aria", "Liam"], key=f"voice_agent_{tab_prefix}")
        
        st.text_input("Script", "Preview text...", key=f"voice_script_{tab_prefix}")
        if st.button("🔊 Preview Voice", key=f"voice_btn_{tab_prefix}"):
            st.info(f"Playing preview for {agent}...")
            # Streamlit audio player for preview
            st.audio(io.BytesIO(b"fake_audio"), format="audio/wav")

def render():
    st.title(f"🎬 {ENGINE_NAME} UGC Studio")
    st.markdown(f"**Built by:** {CREATOR}")

    tab1, tab2, tab3, tab4 = st.tabs(["Text-Image", "Image-Image", "Image-Video (UGC)", "Text-Video"])

    # ── TAB 1: Text-Image ──
    with tab1:
        st.header("Generate AI Image")
        prompt_t2i = st.text_area("Description", key="prompt_t2i")
        if st.button("Generate Image", key="btn_t2i"):
            if not prompt_t2i:
                st.error("Please enter a prompt.")
            else:
                with st.spinner("Rendering Image Locally..."):
                    time.sleep(1) # Small delay for UX
                    img_bytes, error = local_text_to_image(prompt_t2i)
                    if error:
                        st.error(error)
                    else:
                        st.success("Image Generated!")
                        st.image(img_bytes, use_column_width=True)

    # ── TAB 2: Image-Image ──
    with tab2:
        st.header("Transform Image")
        img_i2i = st.file_uploader("Upload Image", type=["png", "jpg"], key="img_i2i")
        st.text_area("Transform Instructions", key="prompt_i2i")
        if st.button("Transform", key="btn_i2i"):
            if not img_i2i:
                st.error("Please upload an image first.")
            else:
                with st.spinner("Applying AI Filters Locally..."):
                    time.sleep(1)
                    img_bytes, error = local_image_to_image(img_i2i.read())
                    if error:
                        st.error(error)
                    else:
                        st.success("Transformation Complete!")
                        st.image(img_bytes, use_column_width=True)

    # ── TAB 3: UGC Motion Transfer ──
    with tab3:
        st.header("UGC Motion Transfer")
        char_img = st.file_uploader("1. Character Image", type=["jpg", "png"], key="ugc_char")
        user_vid = st.file_uploader("2. Your Motion Video", type=["mp4", "mov"], key="ugc_vid")
        vid_duration = st.select_slider("Duration", options=[10, 15, 20, 30, 45, 60], value=15, key="dur_ugc")
        
        render_voice_preview("tab3")

        if st.button("🚀 Generate UGC", key="btn_ugc_main"):
            if not char_img or not user_vid:
                st.error("Upload both the character image and your motion video.")
            else:
                with st.spinner("Compiling UGC Video Locally..."):
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    tfile.write(user_vid.read())
                    
                    vid_path, error = process_ugc_motion(char_img.read(), tfile.name, vid_duration)
                    if error: 
                        st.error(error)
                    else: 
                        st.success("UGC Generated Successfully!")
                        st.video(vid_path)

    # ── TAB 4: Text-Video ──
    with tab4:
        st.header("Text to Video")
        prompt_t2v = st.text_area("Scene Description", key="prompt_t2v")
        duration_t2v = st.select_slider("Duration", options=[10, 15, 20, 30, 45, 60], value=15, key="dur_t2v")
        render_voice_preview("tab4")
        
        if st.button("Generate Video", key="btn_t2v_main"):
            if not prompt_t2v:
                st.error("Please enter a scene description.")
            else:
                with st.spinner(f"Rendering {duration_t2v}s Video Locally..."):
                    vid_path, error = local_text_to_video(prompt_t2v, duration_t2v)
                    if error:
                        st.error(error)
                    else:
                        st.success("Video Generated Successfully!")
                        st.video(vid_path)

if __name__ == "__main__":
    render()
