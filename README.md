# CMJ Jump Height Analyzer

Analyze iPhone video of a **countermovement jump (CMJ)** and automatically calculate jump height — no force plate, no calibration object required.

---

## How It Works

The tool uses **MediaPipe Pose** to track the athlete's feet in every frame of the video. When the feet lift off the ground, it records the takeoff frame; when they return, it records the landing frame. Jump height is then calculated from the airborne flight time using a standard physics formula:

```
h = (g × t²) / 8
```

where `g = 9.81 m/s²` and `t` = total time in the air (seconds).

No camera calibration or reference objects are needed — only a clear side-view video with the athlete's full body visible.

---

## Features

- Automatic flight-phase detection (takeoff → peak → landing)
- Jump height output in inches
- Annotated output video with:
  - Bounding box around the athlete (turns yellow at peak height)
  - Jump height and flight time displayed on every frame
  - Phase labels: *Preparation*, *IN AIR*, *Landing*
  - Timeline bar at the bottom showing the airborne segment and peak marker
- Plain-text results file saved alongside the output video
- File picker GUI — no command-line arguments needed
- Auto-opens the annotated video when processing is complete

---

## Requirements

- **Python 3.10+** (tested on Python 3.12.1)
- **pip** (comes with Python)
- An iPhone video filmed from a **side view** with the athlete's full body visible throughout the jump

---

## Installation

### Step 1 — Install Python (if not already installed)
Download from [python.org](https://www.python.org/downloads/). Make sure to check **"Add Python to PATH"** during installation.

### Step 2 — Install dependencies

**Option A — Double-click (Windows)**
Double-click `install.bat` in the project folder.

**Option B — Terminal**
```bash
pip install -r requirements.txt
```

### Step 3 — Download the pose model (automatic)
The first time you run the script, it will automatically download a small pose detection model file (~8 MB) called `pose_landmarker_full.task`. This only happens once.

---

## How to Use

### Option 1 — File picker (easiest)

Double-click `jump_analyzer.py`, or run in a terminal with no arguments:

```bash
python jump_analyzer.py
```

A file picker window will open. Select your jump video (`.mov`, `.mp4`, `.avi`, etc.) and click **Open**. Processing begins automatically.

### Option 2 — Drag a file path into the terminal

```bash
python jump_analyzer.py "C:\path\to\your\jump_video.mov"
```

### Option 3 — Specify both input and output paths

```bash
python jump_analyzer.py "input.mov" "output_annotated.mp4"
```

---

## Output

After processing, two files are saved in the **same folder as your input video**:

| File | Description |
|---|---|
| `<video>_analyzed.mp4` | Annotated video with bounding box, HUD, and timeline bar |
| `<video>_results.txt` | Plain-text summary of jump height, flight time, and frame data |

**Example results file:**
```
CMJ Jump Height Analysis
========================================
Video:        jump_test.mov
Jump height:  18.3 in
Flight time:  0.612 s
Takeoff:      frame 88  (t=1.47 s)
Landing:      frame 125  (t=2.08 s)
Peak frame:   frame 106  (t=1.77 s)
FPS:          60.00
Resolution:   1920x1080
Total frames: 210
Output video: jump_test_analyzed.mp4
```

The annotated video also auto-opens in your default video player when processing finishes.

---

## Filming Tips (for best accuracy)

| Do | Avoid |
|---|---|
| Film from the **side** (camera perpendicular to the jump) | Filming from the front or back |
| Keep the **full body visible** from head to toe | Cutting off the feet at any point |
| Use a **stationary camera** (tripod or leaning against something) | Panning or zooming during the jump |
| Film at **60 fps** if possible (iPhone: Settings → Camera → Record Video) | Slow-motion mode (variable frame rate can cause inaccuracies) |
| Ensure **good lighting** so the body is clearly visible | Dark backgrounds or backlit subjects |

---

## Known Limitations

- **Flight-time method assumption**: the formula assumes the athlete takes off and lands at the same height with the same foot position. If the athlete bends their knees significantly before their heels touch down, height may be slightly overestimated.
- **Feet must be visible**: if the feet leave the frame at any point during the flight phase, detection will fail.
- **One jump per video**: the tool selects the longest detected flight segment. For best results, trim the video to contain only one jump.
- **Slow-motion video**: iPhone slow-mo clips use a variable frame rate (VFR). The tool reads FPS from the video metadata, which may not match the actual playback speed — use regular video mode for most accurate results.

---

## Project Structure

```
cv based jump height/
├── jump_analyzer.py          # Main script
├── requirements.txt          # Python dependencies
├── install.bat               # Windows one-click installer
├── CLAUDE.md                 # Developer notes
├── pose_landmarker_full.task # Pose model (auto-downloaded on first run)
└── README.md                 # This file
```

---

## Dependencies

| Package | Version | Purpose |
|---|---|---|
| `mediapipe` | ≥ 0.10.0 | Pose landmark detection |
| `opencv-python` | ≥ 4.8.0 | Video reading and annotation |
| `numpy` | ≥ 1.24.0 | Numerical operations |

---

## License

This project is for personal use.
