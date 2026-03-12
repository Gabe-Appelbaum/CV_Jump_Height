# Current Problems

No active problems. App is deploying with the libgthread fix in place.

## Resolved: libgthread-2.0.so.0 ImportError on Streamlit Cloud

**Fix:** `packages.txt` installs `libglib2.0-0t64` (Debian Trixie's package name for libglib).
`app.py` then creates `/tmp/libgthread-2.0.so.0` symlink + sets `LD_LIBRARY_PATH` before
`import cv2`. See CLAUDE.md → "Streamlit Cloud Deployment Notes" for full history.
