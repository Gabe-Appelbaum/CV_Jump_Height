# CV-Based Jump Height Analyzer

## Goal
Analyze iPhone video of a countermovement jump (CMJ) filmed from a **side view** and output:
- Jump height in **inches** (via the flight-time physics method)
- An annotated video with bounding box, jump height overlay, timeline bar, and peak highlight
- A plain-text results file (.txt) saved alongside the annotated video

## How to Run

```bash
# Install dependencies (first time only)
install.bat          # double-click or run in terminal

# Run the analyzer
python jump_analyzer.py                     # opens a file picker
python jump_analyzer.py input.mov           # analyze a specific file
python jump_analyzer.py input.mov out.mp4   # specify output path
```

## Physics Formula

**Flight-time method:**  h = (g × t²) / 8

- `g` = 9.81 m/s²  (gravitational acceleration)
- `t` = total airborne time in seconds (takeoff → landing)
- Result converted: meters → inches (× 39.3701)

This method requires **no camera calibration** — only accurate frame rate and clear foot visibility.

## Algorithm Overview

1. **Pass 1 — Pose extraction**: MediaPipe Pose tracks 4 foot landmarks per frame
   (LEFT_HEEL, RIGHT_HEEL, LEFT_FOOT_INDEX, RIGHT_FOOT_INDEX)
2. **Flight detection**: Smoothed foot y-positions are compared to a ground baseline;
   contiguous frames where feet are elevated above threshold = flight segment
3. **Peak frame**: Midpoint of flight segment (symmetric parabolic arc assumption)
4. **Pass 2 — Video annotation**: Bounding box (yellow at peak), HUD text, timeline bar
5. **Output**: Annotated .mp4 + results .txt + auto-open in video player

## File Structure

```
cv based jump height/
├── CLAUDE.md            ← this file
├── jump_analyzer.py     ← main script
├── requirements.txt     ← pip dependencies
└── install.bat          ← Windows install helper
```

## Dependencies

- `mediapipe` — pose detection
- `opencv-python` — video I/O and drawing
- `numpy` — numerical operations
- `tkinter` — file picker GUI (bundled with Python)

## Known Limitations

- Requires full body (especially feet) visible in every frame during flight
- Camera should be still (no panning/zooming)
- Optimized for side-view footage
- If athlete bends knees significantly before heels touch on landing, height may be slightly
  overestimated (flight-time method assumes symmetric jump)
- iPhone slow-motion VFR clips: FPS is read from video metadata; may be inaccurate for
  variable-frame-rate MOV files
