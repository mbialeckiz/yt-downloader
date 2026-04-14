#!/usr/bin/env python3.12
"""YouTube Downloader – web-based GUI (Flask + yt-dlp)."""

import json
import logging
import os
import queue
import re
import socket
import sys
import threading
import time
import uuid
import webbrowser
from pathlib import Path

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")

from flask import Flask, Response, jsonify, render_template, request, stream_with_context
import yt_dlp

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "app.log")
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))

DOWNLOAD_DIR = str(Path.home() / "Downloads")
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

PORT = 7979

_downloads: dict[str, dict] = {}
_lock = threading.Lock()

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/info", methods=["POST"])
def video_info():
    data = request.get_json(force=True)
    url = (data.get("url") or "").strip()
    if not url:
        return jsonify({"error": "Brak URL"}), 400
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
            info = ydl.extract_info(url, download=False)
        return jsonify({
            "title":     info.get("title", ""),
            "thumbnail": info.get("thumbnail", ""),
            "duration":  info.get("duration", 0),
            "uploader":  info.get("uploader", ""),
        })
    except Exception as exc:
        logging.error("info error: %s", exc)
        return jsonify({"error": _ANSI_RE.sub("", str(exc))}), 400


@app.route("/api/download", methods=["POST"])
def start_download():
    data = request.get_json(force=True)
    url  = (data.get("url") or "").strip()
    fmt  = data.get("format", "bestvideo+bestaudio/best")
    dest = data.get("dest", DOWNLOAD_DIR)

    if not url:
        return jsonify({"error": "Brak URL"}), 400

    download_id = str(uuid.uuid4())
    q: queue.Queue = queue.Queue()

    with _lock:
        _downloads[download_id] = {"queue": q, "status": "running"}

    threading.Thread(
        target=_do_download,
        args=(download_id, url, fmt, dest, q),
        daemon=True,
    ).start()

    return jsonify({"id": download_id})


@app.route("/api/progress/<download_id>")
def progress(download_id: str):
    with _lock:
        entry = _downloads.get(download_id)
    if entry is None:
        return jsonify({"error": "Nie znaleziono"}), 404
    q = entry["queue"]

    def generate():
        while True:
            try:
                event = q.get(timeout=30)
                yield f"data: {json.dumps(event)}\n\n"
                if event.get("type") in ("done", "error"):
                    break
            except queue.Empty:
                yield 'data: {"type":"ping"}\n\n'

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ---------------------------------------------------------------------------
# Download worker
# ---------------------------------------------------------------------------

def _do_download(download_id: str, url: str, fmt: str, dest: str, q: queue.Queue):
    is_audio = "bestaudio" in fmt and "bestvideo" not in fmt

    def hook(d):
        status = d.get("status", "")
        if status == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            speed = d.get("speed") or 0
            eta   = d.get("eta") or 0
            pct   = (downloaded / total * 100) if total else 0
            q.put({
                "type":     "progress",
                "pct":      round(pct, 1),
                "speed":    f"{speed / 1024:.1f} KB/s" if speed else "—",
                "eta":      f"{eta}s" if eta else "—",
                "filename": os.path.basename(d.get("filename", "")),
            })
        elif status == "finished":
            q.put({
                "type":     "finished_file",
                "filename": os.path.basename(d.get("filename", "")),
            })

    ydl_opts: dict = {
        "format":               fmt,
        "outtmpl":              os.path.join(dest, "%(title)s.%(ext)s"),
        "progress_hooks":       [hook],
        "quiet":                True,
        "merge_output_format":  "mp4",
    }
    if is_audio:
        ydl_opts["postprocessors"] = [{
            "key":              "FFmpegExtractAudio",
            "preferredcodec":   "mp3",
            "preferredquality": "192",
        }]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        q.put({"type": "done", "dest": dest})
        with _lock:
            _downloads[download_id]["status"] = "done"
    except Exception as exc:
        logging.error("download error: %s", exc)
        q.put({"type": "error", "message": _ANSI_RE.sub("", str(exc))})
        with _lock:
            _downloads[download_id]["status"] = "error"


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def _port_in_use(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=0.5):
            return True
    except OSError:
        return False


def _open_browser(port: int, delay: float = 1.2):
    time.sleep(delay)
    webbrowser.open(f"http://127.0.0.1:{port}")


if __name__ == "__main__":
    if _port_in_use(PORT):
        # Server already running – just open the browser
        webbrowser.open(f"http://127.0.0.1:{PORT}")
        sys.exit(0)

    threading.Thread(target=_open_browser, args=(PORT,), daemon=True).start()
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)
