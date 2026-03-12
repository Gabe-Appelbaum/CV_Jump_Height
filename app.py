"""
CMJ Jump Height Analyzer — Streamlit Web App
=============================================
Run with:
    streamlit run app.py
"""

import base64
import tempfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from jump_analyzer import analyze_video, ensure_model

# ── One-time setup ────────────────────────────────────────────────────────────
ensure_model()

# ── Custom component ──────────────────────────────────────────────────────────
camera_recorder = components.declare_component(
    "camera_recorder",
    path=str(Path(__file__).parent / "camera_recorder"),
)

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="CMJ Jump Analyzer",
    page_icon="🏋️",
    layout="centered",
)

st.title("CMJ Jump Analyzer")
st.caption("Upload a side-view jump video — or record one directly from your camera.")


# ── Shared analysis helper ────────────────────────────────────────────────────
def run_analysis(input_path: str, output_path: str):
    with st.spinner("Analyzing jump… this usually takes 30–90 seconds."):
        try:
            result = analyze_video(input_path, output_path)
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

    if result["jump_height_in"] > 0:
        col1, col2 = st.columns(2)
        col1.metric("Jump Height", f"{result['jump_height_in']:.1f} in")
        col2.metric("Flight Time", f"{result['flight_time_s']:.3f} s")
        st.video(output_path)
        with open(output_path, "rb") as f:
            st.download_button(
                label="Download annotated video",
                data=f,
                file_name="jump_analyzed.mp4",
                mime="video/mp4",
            )
    else:
        st.warning(
            "No clear flight phase detected. "
            "Ensure feet are fully visible and the camera is still."
        )


# ── Tabs ──────────────────────────────────────────────────────────────────────
tab_upload, tab_record = st.tabs(["Upload video", "Record video"])

# ── Upload tab ────────────────────────────────────────────────────────────────
with tab_upload:
    uploaded = st.file_uploader(
        "Select video",
        type=["mp4", "mov", "avi", "mkv", "m4v"],
        label_visibility="collapsed",
    )

    if uploaded is not None:
        suffix = Path(uploaded.name).suffix or ".mp4"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
            tmp_in.write(uploaded.read())
            input_path = tmp_in.name
        output_path = input_path.replace(suffix, "_analyzed.mp4")
        run_analysis(input_path, output_path)

# ── Record tab ────────────────────────────────────────────────────────────────
with tab_record:
    st.info("Point your camera sideways so your full body (especially feet) is visible.")

    recording = camera_recorder(key="cam", height=420)

    # recording is None until the user stops; then it's {"data": base64, "mime": "..."}
    # Use session_state to avoid re-running analysis on every Streamlit rerun.
    if recording is not None:
        rec_key = recording["data"][:32]   # short fingerprint to detect new recordings
        if st.session_state.get("last_rec_key") != rec_key:
            st.session_state["last_rec_key"] = rec_key

            video_bytes = base64.b64decode(recording["data"])
            mime = recording.get("mime", "video/webm")
            suffix = ".mp4" if "mp4" in mime else ".webm"

            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_in:
                tmp_in.write(video_bytes)
                input_path = tmp_in.name
            output_path = input_path.replace(suffix, "_analyzed.mp4")
            run_analysis(input_path, output_path)
