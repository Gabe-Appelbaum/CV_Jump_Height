# Current Problems & Fix Plan

## Problem History

### Original Issue: FPS inaccuracy from iOS VFR video
iPhone slow-motion clips use variable frame rate (VFR). The video metadata reports a nominal
FPS that doesn't reflect actual frame timing, causing jump height to be calculated incorrectly.

**Fix (merged, working):** Use `cap.get(cv2.CAP_PROP_POS_MSEC)` to get per-frame timestamps
from the video container. Flight time is computed as `timestamps[t1] - timestamps[t0]` instead
of `(t1 - t0) / fps`, bypassing nominal FPS entirely.

---

### Deployment Problem: `libgthread-2.0.so.0` not found on Streamlit Cloud

After deploying the FPS fix, the app fails at startup on Streamlit Cloud with:
```
ImportError: libgthread-2.0.so.0: cannot open shared object file: No such file or directory
```

**Root cause:** Streamlit Cloud runs **Debian Trixie**. In GLib 2.68+, `libgthread-2.0.so.0`
was merged into `libglib-2.0.so.0` and no longer exists as a separate file. MediaPipe's binary
wheels still link against the old soname.

#### What was tried and why it failed

| Attempt | What it did | Why it failed |
|---------|-------------|---------------|
| Add `libglib2.0-0` to `packages.txt` | Tried to install glib via apt | Debian Bullseye version conflicts with Trixie's `libffi8`/`libpcre3` |
| `setup.sh` symlink | Linked `libglib-2.0.so.0` → `libgthread-2.0.so.0` | File committed as `100644` (not executable); Streamlit Cloud silently skipped it |
| Fix `setup.sh` executable bit + Python `sudo ln` fallback | Made setup.sh runnable; fallback runs before `import cv2` | `sudo` fails silently during app execution (only works during build phase) |

---

## Current Fix Plan

**Use a `Dockerfile` with `python:3.11-slim-bullseye` (Debian 11).**

On Debian Bullseye, `libglib2.0-0` version 2.66 ships `libgthread-2.0.so.0` as a real file.
No symlinks, no runtime hacks — the library simply exists.

Streamlit Cloud uses a `Dockerfile` if one is present at the repo root, giving full
environment control.

**Changes:**
1. Add `Dockerfile` at the repo root — uses Bullseye base, installs `libgl1` + `libglib2.0-0`
2. Remove the `sudo ln` hack block from `app.py` (lines 8–17) — no longer needed

`packages.txt` and `setup.sh` are ignored when a Dockerfile is present; leave them as-is.
