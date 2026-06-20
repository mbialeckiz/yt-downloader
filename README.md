# YouTube Downloader

Prosty downloader wideo/audio z YouTube z webowym interfejsem (Flask + yt-dlp).

## Wymagania

- **Python 3.10+** (zalecany 3.12)
- **ffmpeg** – wymagany do łączenia strumieni wideo+audio oraz konwersji do MP3.
  Bez ffmpeg aplikacja nadal działa, ale pobiera gotowe pliki (np. `.mp4`/`.m4a`)
  zamiast najlepszej jakości scalonej i nie konwertuje audio do MP3.

### Instalacja ffmpeg

- **macOS:** `brew install ffmpeg`
- **Ubuntu/Debian:** `sudo apt install ffmpeg`
- **Windows:** pobierz z https://ffmpeg.org/download.html i dodaj do `PATH`

## Instalacja

```sh
# (zalecane) wirtualne środowisko
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
```

## Uruchomienie

```sh
./run.sh
```

lub bezpośrednio:

```sh
python3 app.py
```

Aplikacja wystartuje na **http://127.0.0.1:7979** i automatycznie otworzy
przeglądarkę. Pobrane pliki trafiają do katalogu `~/Downloads`.

## Rozwiązywanie problemów

- **`ModuleNotFoundError: No module named 'flask'` / `'yt_dlp'`** –
  zależności nie są zainstalowane. Uruchom `pip install -r requirements.txt`.
- **Łączenie wideo+audio / MP3 nie działa** – brak ffmpeg, patrz wyżej.
- **Port 7979 zajęty** – jeśli aplikacja już działa, ponowne uruchomienie
  tylko otworzy przeglądarkę.
- **Błędy pobierania / „Unable to download"** – zaktualizuj yt-dlp:
  `pip install -U yt-dlp` (YouTube często zmienia API).
