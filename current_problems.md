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

**Root cause:** Streamlit Cloud runs **Debian Trixie** with **Python 3.14**. In GLib 2.68+,
`libgthread-2.0.so.0` was merged into `libglib-2.0.so.0` and no longer exists as a separate
file. MediaPipe/cv2 wheels still link against the old soname.

**Key finding:** `libglib-2.0.so.0` DOES exist on the system. We just need to make
`libgthread-2.0.so.0` findable under that name before `import cv2` runs.

#### What was tried and why it failed

| Attempt | What it did | Why it failed |
|---------|-------------|---------------|
| `libglib2.0-0` in `packages.txt` | Tried apt install | Debian/Ubuntu source conflict — `libffi7` not installable on Trixie |
| `setup.sh` symlink | Symlinked libglib → libgthread | File was `100644` (not executable); Streamlit Cloud skipped it |
| Fix `setup.sh` executable + Python `sudo ln` fallback | Made setup.sh runnable; Python fallback with sudo | `sudo` silently fails during app execution (only works during build) |
| `Dockerfile` with Bullseye base image | Use Debian 11 where libgthread exists natively | Dockerfile support is paid/enterprise tier only — free tier ignores it (still used Python 3.14) |

---

## Current Fix (in app.py)

**Approach:** Create `/tmp/libgthread-2.0.so.0` as a symlink to `libglib-2.0.so.0`, then
prepend `/tmp` to `LD_LIBRARY_PATH` before `import cv2`.

- `/tmp` is always world-writable — no sudo needed
- `os.symlink()` creates the link without elevated permissions
- On Linux, `dlopen()` re-reads `LD_LIBRARY_PATH` from the live process environment, so
  setting it in `os.environ` before `import cv2` causes the dynamic linker to find the symlink

The fix block at the top of `app.py` includes print statements at each step so the logs
will show exactly what happened if it fails again.

**Expected log output on success:**
```
[libgthread-fix] Starting libgthread fix...
[libgthread-fix] libglib found at: /usr/lib/x86_64-linux-gnu/libglib-2.0.so.0
[libgthread-fix] libgthread in system dir exists: False
[libgthread-fix] Created symlink: /tmp/libgthread-2.0.so.0 -> /usr/lib/x86_64-linux-gnu/libglib-2.0.so.0
[libgthread-fix] LD_LIBRARY_PATH set to: /tmp:...
[libgthread-fix] Done. Proceeding to import cv2...
```
