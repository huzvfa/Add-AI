import streamlit as st
import io
import tempfile
import numpy as np

# ── Safe Imports for Video Processing ──
try:
    import cv2
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

def process_ugc_motion(target_image_bytes, user_video_path, duration_sec):
    if not HAS_CV2: return None, "Error: 'opencv-python-headless' is required."
    
    cap = cv2.VideoCapture(user_video_path)
    target_img = cv2.imdecode(np.frombuffer(target_image_bytes, np.uint8), 1)
    frames = []
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    max_frames = int(fps * duration_sec)
    
    count = 0
    while cap.isOpened() and count < max_frames:
        ret, frame = cap.read()
        if not ret: break
        h, w = frame.shape[:2]
        warped_character = cv2.resize(target_img, (w, h))
        output_frame = cv2.addWeighted(warped_character, 0.6, frame, 0.4, 0)
        frames.append(output_frame)
        count += 1
    
    cap.release()
    return frames, None

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
            st.audio(io.BytesIO(b"fake_audio"), format="audio/wav")

def render():
    st.title(f"🎬 {ENGINE_NAME} UGC Studio")
    st.markdown(f"**Built by:** {CREATOR}")

    tab1, tab2, tab3, tab4 = st.tabs(["Text-Image", "Image-Image", "Image-Video (UGC)", "Text-Video"])

    with tab1:
        st.header("Generate AI Image")
        st.text_area("Description", key="prompt_t2i")
        if st.button("Generate Image", key="btn_t2i"): st.info("Processing...")

    with tab2:
        st.header("Transform Image")
        st.file_uploader("Upload Image", type=["png", "jpg"], key="img_i2i")
        if st.button("Transform", key="btn_i2i"): st.info("Processing...")

    with tab3:
        st.header("UGC Motion Transfer")
        char_img = st.file_uploader("1. Character Image", type=["jpg", "png"], key="ugc_char")
        user_vid = st.file_uploader("2. Your Motion Video", type=["mp4", "mov"], key="ugc_vid")
        vid_duration = st.select_slider("Duration", options=[10, 15, 20, 30, 45, 60], value=15, key="dur_ugc")
        
        render_voice_preview("tab3")

        if st.button("🚀 Generate UGC", key="btn_ugc"):
            if not char_img or not user_vid:
                st.error("Upload both files.")
            else:
                with st.spinner("Processing motion..."):
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                    tfile.write(user_vid.read())
                    frames, error = process_ugc_motion(char_img.read(), tfile.name, vid_duration)
                    if error: st.error(error)
                    else: st.success("UGC Generated!")

    with tab4:
        st.header("Text to Video")
        st.text_area("Scene Description", key="prompt_t2v")
        st.select_slider("Duration", options=[10, 15, 20, 30, 45, 60], value=15, key="dur_t2v")
        render_voice_preview("tab4")
        if st.button("Generate Video", key="btn_t2v"): st.info("Processing...")

if __name__ == "__main__":
    render()
