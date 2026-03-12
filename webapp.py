"""
CMJ Jump Height Analyzer — Web App
===================================
Flask web server that wraps analyze_video() for phone/browser access.

Usage:
    python webapp.py                  # starts on http://localhost:5000
    PORT=8080 python webapp.py        # custom port (Replit sets PORT automatically)

For public phone access:
    Local PC:  run `ngrok http 5000` in a second terminal
    Replit:    just click Run — Replit provides a public URL automatically
"""

import os
import uuid
import tempfile
from pathlib import Path

from flask import Flask, request, render_template, send_file

from jump_analyzer import analyze_video, ensure_model

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024   # 500 MB upload limit

WORK_DIR = Path(tempfile.gettempdir()) / "cmj_web"
WORK_DIR.mkdir(exist_ok=True)


@app.route("/")
def index():
    return render_template("index.html", result=None, error=None, token=None)


@app.route("/analyze", methods=["POST"])
def analyze():
    f = request.files.get("video")
    if not f or not f.filename:
        return render_template("index.html", result=None,
                               error="No file selected.", token=None)

    token       = uuid.uuid4().hex[:10]
    suffix      = Path(f.filename).suffix or ".mp4"
    upload_path = WORK_DIR / f"{token}_input{suffix}"
    output_path = WORK_DIR / f"{token}_analyzed.mp4"

    f.save(upload_path)
    try:
        result = analyze_video(str(upload_path), str(output_path))
    except Exception as e:
        return render_template("index.html", result=None,
                               error=str(e), token=None)
    finally:
        upload_path.unlink(missing_ok=True)   # discard the original upload

    return render_template("index.html", result=result, error=None, token=token)


@app.route("/file/<token>")
def download(token):
    # Sanitise token — only hex chars allowed
    if not token.isalnum() or len(token) > 20:
        return "Invalid token.", 400
    path = WORK_DIR / f"{token}_analyzed.mp4"
    if not path.exists():
        return "File not found or already expired.", 404
    return send_file(path, as_attachment=True,
                     download_name="jump_analyzed.mp4")


if __name__ == "__main__":
    ensure_model()
    port = int(os.environ.get("PORT", 5000))
    print(f"\n  CMJ Web App running on http://localhost:{port}")
    print("  For phone access, run:  ngrok http " + str(port))
    print("  Press Ctrl+C to stop.\n")
    app.run(host="0.0.0.0", port=port, debug=False)
