# CV-Based Jump Height Analyzer

## General Instructions

- Always think about what the simplest, least invasive way to complete a task is. Avoid scope creep. If implementing a feature, don't refactor unrelated code along the way.
- Before starting any non-trivial task, ask clarifying questions to understand the requirements fully. Don't make assumptions — interview the user about their intent.
- When given a task that involves multiple steps or architectural decisions, enter plan mode first. Write out the plan, get approval, then implement.
- Use the TodoWrite tool to track multi-step tasks. Mark items complete as you finish them, not in batches.
- After completing a task, summarize what was done concisely. Don't over-explain.
- Never modify files outside the scope of the current task. If you notice something that could be improved elsewhere, mention it but don't act on it unless asked.
- Prefer editing existing files to creating new ones. Only create new files when truly necessary.
- When making a change that touches multiple files, read all the relevant files first before making any edits.
- Do not push to remote repositories, deploy, or run destructive commands without explicit confirmation from the user.

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
