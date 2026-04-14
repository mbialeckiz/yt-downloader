#!/usr/bin/env sh
# Launcher for YouTube Downloader
APP_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$APP_DIR"

# Find python with yt-dlp available
for py in python3.12 python3.11 python3 python; do
  if command -v "$py" >/dev/null 2>&1; then
    if "$py" -c "import yt_dlp, flask" 2>/dev/null; then
      exec "$py" app.py
    fi
  fi
done

echo "Blad: nie znaleziono Pythona z zainstalowanymi yt-dlp i flask."
echo "Uruchom: pip install yt-dlp flask"
exit 1
