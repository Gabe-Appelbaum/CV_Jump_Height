"""
CMJ Jump Height Analyzer
========================
Analyzes countermovement jump (CMJ) videos to calculate jump height
using the flight-time method:  h = (g * t^2) / 8

Usage:
    python jump_analyzer.py                        # opens file-picker GUI
    python jump_analyzer.py input.mov              # analyze a specific file
    python jump_analyzer.py input.mov output.mp4   # specify output path
"""

import sys
import os
import urllib.request
import cv2
import numpy as np
from pathlib import Path

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python.vision import PoseLandmarker, PoseLandmarkerOptions
from mediapipe.tasks.python.vision.core.vision_task_running_mode import VisionTaskRunningMode


# ── Constants ────────────────────────────────────────────────────────────────
M_TO_IN   = 39.3701
MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/pose_landmarker/"
    "pose_landmarker_full/float16/latest/pose_landmarker_full.task"
)
MODEL_PATH = Path(__file__).parent / "pose_landmarker_full.task"

# Landmark indices in the 33-point MediaPipe pose skeleton
IDX_LEFT_HEEL  = 29
IDX_RIGHT_HEEL = 30
IDX_LEFT_FOOT  = 31
IDX_RIGHT_FOOT = 32
FOOT_INDICES   = [IDX_LEFT_HEEL, IDX_RIGHT_HEEL, IDX_LEFT_FOOT, IDX_RIGHT_FOOT]


# ── Model download ────────────────────────────────────────────────────────────

def ensure_model():
    """Download the pose landmarker model if not already present."""
    if MODEL_PATH.exists():
        return
    print(f"Downloading pose model (~8 MB) — one-time setup…")
    urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
    print(f"Model saved to {MODEL_PATH}")


# ── File picker ───────────────────────────────────────────────────────────────

def pick_file_gui():
    """Open a file-picker dialog and return the selected path (or None)."""
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        path = filedialog.askopenfilename(
            title="Select jump video",
            filetypes=[
                ("Video files", "*.mp4 *.mov *.avi *.mkv *.m4v *.MOV *.MP4 *.AVI"),
                ("All files", "*.*"),
            ],
        )
        root.destroy()
        return path or None
    except Exception as e:
        print(f"GUI file picker unavailable ({e}). Pass a path as an argument instead.")
        return None


# ── Pose helpers ──────────────────────────────────────────────────────────────

def get_foot_y(pose_landmarks):
    """
    Return mean normalised y-position of the four foot landmarks.
    In MediaPipe y increases downward → feet on ground = large y.
    Returns None if no foot landmark has sufficient visibility.
    """
    ys = []
    for idx in FOOT_INDICES:
        lm = pose_landmarks[idx]
        if lm.visibility > 0.3:
            ys.append(lm.y)
    return float(np.mean(ys)) if ys else None


def person_bbox(pose_landmarks, frame_w, frame_h, padding=20):
    """Return (x1, y1, x2, y2) bounding box over all visible landmarks."""
    xs, ys = [], []
    for lm in pose_landmarks:
        if lm.visibility > 0.3:
            xs.append(lm.x * frame_w)
            ys.append(lm.y * frame_h)
    if not xs:
        return None
    return (
        max(0,       int(min(xs)) - padding),
        max(0,       int(min(ys)) - padding),
        min(frame_w, int(max(xs)) + padding),
        min(frame_h, int(max(ys)) + padding),
    )


# ── Signal processing ─────────────────────────────────────────────────────────

def smooth_series(values, window=5):
    """Moving-average smoothing over a list that may contain None values."""
    half = window // 2
    out  = []
    for i in range(len(values)):
        neighbors = [
            values[j]
            for j in range(max(0, i - half), min(len(values), i + half + 1))
            if values[j] is not None
        ]
        out.append(float(np.mean(neighbors)) if neighbors else None)
    return out


def detect_jump(foot_ys, fps, ground_pct=85, threshold_frac=0.04, min_frames=4):
    """
    Find the primary jump (longest airborne segment) in the foot y time series.

    Returns (t0, t1, flight_time_s, jump_height_m, peak_frame) or None.
    """
    valid = [y for y in foot_ys if y is not None]
    if not valid:
        return None

    ground_y   = np.percentile(valid, ground_pct)
    airborne_y = ground_y - threshold_frac

    segments = []
    in_air, start = False, None

    for i, y in enumerate(foot_ys):
        if y is None:
            continue
        if not in_air and y < airborne_y:
            in_air, start = True, i
        elif in_air and y >= airborne_y:
            in_air = False
            if (i - start) >= min_frames:
                segments.append((start, i))
            start = None

    if in_air and start is not None and (len(foot_ys) - start) >= min_frames:
        segments.append((start, len(foot_ys) - 1))

    if not segments:
        return None

    t0, t1        = max(segments, key=lambda s: s[1] - s[0])
    flight_time   = (t1 - t0) / fps
    jump_height_m = 9.81 * flight_time**2 / 8.0
    peak_frame    = (t0 + t1) // 2

    return t0, t1, flight_time, jump_height_m, peak_frame


# ── Drawing helpers ───────────────────────────────────────────────────────────

def draw_text(img, text, pos, font_scale=1.0, thickness=2,
              color=(255, 255, 255), shadow=(0, 0, 0)):
    """Draw text with a drop shadow for readability on any background."""
    font = cv2.FONT_HERSHEY_SIMPLEX
    x, y = pos
    cv2.putText(img, text, (x + 2, y + 2), font, font_scale, shadow,
                thickness + 2, cv2.LINE_AA)
    cv2.putText(img, text, (x,     y    ), font, font_scale, color,
                thickness,     cv2.LINE_AA)


def draw_timeline_bar(img, frame_idx, total_frames, t0, t1, peak_frame,
                      frame_w, frame_h):
    """
    Bottom progress bar:
      dark background | blue = airborne | yellow dot = peak | white cursor = now
    """
    bar_h  = 14
    margin = 20
    bar_y  = frame_h - bar_h - 8
    bar_w  = frame_w - 2 * margin

    cv2.rectangle(img, (margin, bar_y),
                  (margin + bar_w, bar_y + bar_h), (50, 50, 50), -1)

    def to_x(f):
        return margin + int(f / total_frames * bar_w)

    # Airborne segment
    cv2.rectangle(img, (to_x(t0), bar_y), (to_x(t1), bar_y + bar_h),
                  (220, 80, 0), -1)

    # Peak marker
    xpk = to_x(peak_frame)
    cv2.circle(img, (xpk, bar_y + bar_h // 2), 6, (0, 230, 255), -1)
    cv2.circle(img, (xpk, bar_y + bar_h // 2), 6, (0, 0, 0), 1)
    draw_text(img, "PEAK", (xpk - 24, bar_y - 8),
              font_scale=0.65, thickness=1, color=(0, 230, 255))

    # Current-frame cursor
    xc = to_x(frame_idx)
    cv2.rectangle(img, (xc - 1, bar_y - 4),
                  (xc + 1, bar_y + bar_h + 4), (255, 255, 255), -1)


# ── Core analysis pipeline ────────────────────────────────────────────────────

def analyze_video(video_path: str, output_path: str | None = None) -> dict:
    """
    Full pipeline: pose extraction → flight detection → annotated video output.

    Returns a dict with: jump_height_in, flight_time_s, output_path, results_txt
    """
    video_path = str(video_path)
    stem   = Path(video_path).stem
    parent = Path(video_path).parent

    if output_path is None:
        output_path = str(parent / f"{stem}_analyzed.mp4")
    results_txt = str(parent / f"{stem}_results.txt")

    # ── Open video ────────────────────────────────────────────────────────────
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_path}")

    fps    = cap.get(cv2.CAP_PROP_FPS) or 30.0
    width  = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total  = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    print(f"\nVideo : {Path(video_path).name}")
    print(f"        {width}×{height}  |  {fps:.2f} fps  |  ~{total} frames")

    # ── Pass 1: extract pose landmarks per frame ──────────────────────────────
    raw_lm      = []   # list of pose_landmarks (list[NormalizedLandmark]) or None
    raw_foot_ys = []

    options = PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=str(MODEL_PATH)),
        running_mode=VisionTaskRunningMode.IMAGE,
        num_poses=1,
        min_pose_detection_confidence=0.5,
        min_pose_presence_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    print("\nPass 1/2  —  detecting pose…")
    with PoseLandmarker.create_from_options(options) as detector:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            rgb      = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            result   = detector.detect(mp_image)

            if result.pose_landmarks:
                lms = result.pose_landmarks[0]   # first (only) person
                raw_lm.append(lms)
                raw_foot_ys.append(get_foot_y(lms))
            else:
                raw_lm.append(None)
                raw_foot_ys.append(None)

    cap.release()
    n_frames = len(raw_foot_ys)

    # ── Flight detection ──────────────────────────────────────────────────────
    smoothed = smooth_series(raw_foot_ys, window=5)
    jump     = detect_jump(smoothed, fps)

    if jump:
        t0, t1, flight_time, jump_height_m, peak_frame = jump
        jump_height_in = jump_height_m * M_TO_IN
        print(f"\n  Flight time : {flight_time:.3f} s  (frames {t0}–{t1})")
        print(f"  Jump height : {jump_height_in:.1f} in")
    else:
        t0 = t1 = peak_frame = None
        flight_time = jump_height_m = jump_height_in = 0.0
        print("\n  WARNING: No clear flight phase detected.")
        print("  Tips: ensure feet are fully visible; camera should be still.")

    # ── Pass 2: write annotated video ─────────────────────────────────────────
    # Re-open the source video so we never hold all frames in RAM simultaneously.
    print("\nPass 2/2  —  writing annotated video…")
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out    = cv2.VideoWriter(output_path, fourcc, fps, (width, height))

    cap2 = cv2.VideoCapture(video_path)
    i = 0
    while cap2.isOpened():
        ret, frame = cap2.read()
        if not ret:
            break
        img     = frame.copy()
        lm_data = raw_lm[i] if i < len(raw_lm) else None

        # Phase + box colour
        if t0 is not None:
            at_peak = (i == peak_frame)
            if i < t0:
                phase, box_color = "Preparation",  (0, 215, 255)
            elif i <= t1:
                if at_peak:
                    phase, box_color = "PEAK HEIGHT", (0, 230, 255)
                else:
                    phase, box_color = "IN AIR",      (30, 100, 255)
            else:
                phase, box_color = "Landing",      (80, 200, 80)
        else:
            phase, box_color, at_peak = "No jump detected", (160, 160, 160), False

        # Bounding box
        if lm_data:
            bbox = person_bbox(lm_data, width, height)
            if bbox:
                x1, y1, x2, y2 = bbox
                thick = 4 if at_peak else 2
                cv2.rectangle(img, (x1, y1), (x2, y2), box_color, thick)
                if at_peak:
                    cv2.rectangle(img, (x1 + 3, y1 + 3),
                                  (x2 - 3, y2 - 3), (255, 255, 255), 1)
                draw_text(img, phase, (x1 + 6, y1 + 36),
                          font_scale=1.1, thickness=2, color=box_color)

        # HUD — top-left
        hx, hy = 20, 65
        if jump_height_in > 0:
            draw_text(img, f"Jump Height: {jump_height_in:.1f} in",
                      (hx, hy), font_scale=1.8, thickness=3)
            draw_text(img, f"Flight time: {flight_time:.3f} s",
                      (hx, hy + 55), font_scale=1.2, thickness=2,
                      color=(200, 200, 200))
        else:
            draw_text(img, "Jump Height: --",
                      (hx, hy), font_scale=1.6, thickness=3,
                      color=(160, 160, 160))

        # Timestamp — top-right
        ts = f"t = {i / fps:.2f}s"
        (tw, _), _ = cv2.getTextSize(ts, cv2.FONT_HERSHEY_SIMPLEX, 1.0, 2)
        draw_text(img, ts, (width - tw - 22, 55),
                  font_scale=1.0, thickness=2, color=(220, 220, 220))

        # Timeline bar
        if t0 is not None:
            draw_timeline_bar(img, i, n_frames, t0, t1, peak_frame,
                              width, height)

        out.write(img)

        done = i + 1
        if done % 30 == 0 or done == n_frames:
            print(f"  {done}/{n_frames} frames ({done/n_frames*100:.0f}%)", end="\r")

        i += 1

    cap2.release()
    out.release()
    print(f"\nAnnotated video -> {output_path}")

    # ── Write results .txt ─────────────────────────────────────────────────────
    with open(results_txt, "w") as f:
        f.write("CMJ Jump Height Analysis\n")
        f.write("=" * 40 + "\n")
        f.write(f"Video:        {Path(video_path).name}\n")
        if jump_height_in > 0:
            f.write(f"Jump height:  {jump_height_in:.1f} in\n")
            f.write(f"Flight time:  {flight_time:.3f} s\n")
            f.write(f"Takeoff:      frame {t0}  (t={t0/fps:.2f} s)\n")
            f.write(f"Landing:      frame {t1}  (t={t1/fps:.2f} s)\n")
            f.write(f"Peak frame:   frame {peak_frame}  (t={peak_frame/fps:.2f} s)\n")
        else:
            f.write("Jump height:  -- (no jump detected)\n")
        f.write(f"FPS:          {fps:.2f}\n")
        f.write(f"Resolution:   {width}x{height}\n")
        f.write(f"Total frames: {n_frames}\n")
        f.write(f"Output video: {Path(output_path).name}\n")

    print(f"Results txt   -> {results_txt}")

    return {
        "jump_height_in": jump_height_in,
        "flight_time_s":  flight_time,
        "output_path":    output_path,
        "results_txt":    results_txt,
    }


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if len(args) == 0:
        print("CMJ Jump Height Analyzer — opening file picker…")
        video_path = pick_file_gui()
        if not video_path:
            print("No file selected. Exiting.")
            sys.exit(0)
        output_path = None

    elif len(args) == 1:
        video_path  = args[0]
        output_path = None

    else:
        video_path  = args[0]
        output_path = args[1]

    if not os.path.isfile(video_path):
        print(f"ERROR: File not found: {video_path}")
        sys.exit(1)

    ensure_model()
    result = analyze_video(video_path, output_path)

    print()
    print("=" * 45)
    if result["jump_height_in"] > 0:
        print(f"  RESULT:  {result['jump_height_in']:.1f} inches")
        print(f"  Flight:  {result['flight_time_s']:.3f} s")
    else:
        print("  Could not determine jump height.")
        print("  Ensure feet are fully visible and camera is still.")
    print("=" * 45)

    try:
        os.startfile(result["output_path"])
    except Exception:
        print(f"Open manually: {result['output_path']}")


if __name__ == "__main__":
    main()
