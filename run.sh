#!/usr/bin/env bash
# Launcher for YouTube Downloader
APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$APP_DIR"
exec python3.12 app.py
