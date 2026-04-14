#!/usr/bin/env python3.12
"""YouTube Downloader - prosta aplikacja GUI do pobierania wideo z YouTube."""

import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import yt_dlp


FORMATS = [
    ("Najlepsza jakość (wideo + audio)", "bestvideo+bestaudio/best"),
    ("1080p MP4", "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]"),
    ("720p MP4",  "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]"),
    ("480p MP4",  "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]"),
    ("360p MP4",  "bestvideo[height<=360][ext=mp4]+bestaudio[ext=m4a]/best[height<=360]"),
    ("Tylko audio (MP3)", "bestaudio/best"),
]

DEFAULT_DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("YouTube Downloader")
        self.resizable(False, False)
        self._download_dir = tk.StringVar(value=DEFAULT_DOWNLOAD_DIR)
        self._url = tk.StringVar()
        self._format_index = tk.IntVar(value=0)
        self._status = tk.StringVar(value="Gotowy.")
        self._downloading = False
        self._build_ui()

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------

    def _build_ui(self):
        PAD = 12
        self.configure(bg="#1e1e2e", padx=PAD * 2, pady=PAD)

        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel",      background="#1e1e2e", foreground="#cdd6f4", font=("Segoe UI", 10))
        style.configure("TEntry",      fieldbackground="#313244", foreground="#cdd6f4",
                        insertcolor="#cdd6f4", bordercolor="#45475a", lightcolor="#45475a",
                        darkcolor="#45475a")
        style.configure("TCombobox",   fieldbackground="#313244", foreground="#cdd6f4",
                        background="#313244", arrowcolor="#cdd6f4",
                        selectbackground="#45475a", selectforeground="#cdd6f4")
        style.map("TCombobox",         fieldbackground=[("readonly", "#313244")],
                  foreground=[("readonly", "#cdd6f4")])
        style.configure("TButton",     background="#89b4fa", foreground="#1e1e2e",
                        font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("TButton",           background=[("active", "#74c7ec"), ("disabled", "#45475a")],
                  foreground=[("disabled", "#6c7086")])
        style.configure("TProgressbar", troughcolor="#313244", background="#89b4fa", thickness=8)
        style.configure("Browse.TButton", background="#585b70", foreground="#cdd6f4",
                        font=("Segoe UI", 9))
        style.map("Browse.TButton",    background=[("active", "#6c7086")])

        # ---- URL ----
        ttk.Label(self, text="URL wideo:").grid(row=0, column=0, sticky="w", pady=(PAD, 2))
        url_frame = tk.Frame(self, bg="#1e1e2e")
        url_frame.grid(row=1, column=0, sticky="ew", pady=(0, PAD))
        self._url_entry = ttk.Entry(url_frame, textvariable=self._url, width=58)
        self._url_entry.pack(side="left", fill="x", expand=True)
        ttk.Button(url_frame, text="Wklej", style="Browse.TButton",
                   command=self._paste_url).pack(side="left", padx=(6, 0))

        # ---- Format ----
        ttk.Label(self, text="Format / jakość:").grid(row=2, column=0, sticky="w", pady=(0, 2))
        labels = [label for label, _ in FORMATS]
        self._format_combo = ttk.Combobox(self, values=labels, state="readonly", width=64)
        self._format_combo.current(0)
        self._format_combo.grid(row=3, column=0, sticky="ew", pady=(0, PAD))

        # ---- Destination ----
        ttk.Label(self, text="Folder docelowy:").grid(row=4, column=0, sticky="w", pady=(0, 2))
        dir_frame = tk.Frame(self, bg="#1e1e2e")
        dir_frame.grid(row=5, column=0, sticky="ew", pady=(0, PAD))
        ttk.Entry(dir_frame, textvariable=self._download_dir, width=50,
                  state="readonly").pack(side="left", fill="x", expand=True)
        ttk.Button(dir_frame, text="Zmień...", style="Browse.TButton",
                   command=self._choose_dir).pack(side="left", padx=(6, 0))

        # ---- Separator ----
        ttk.Separator(self, orient="horizontal").grid(row=6, column=0, sticky="ew",
                                                       pady=(0, PAD))

        # ---- Download button ----
        self._dl_btn = ttk.Button(self, text="Pobierz", command=self._start_download)
        self._dl_btn.grid(row=7, column=0, sticky="ew", ipady=6, pady=(0, PAD))

        # ---- Progress ----
        self._progress = ttk.Progressbar(self, mode="determinate", maximum=100)
        self._progress.grid(row=8, column=0, sticky="ew", pady=(0, 6))

        # ---- Status label ----
        ttk.Label(self, textvariable=self._status, wraplength=520,
                  font=("Segoe UI", 9)).grid(row=9, column=0, sticky="w")

        # ---- Log box ----
        ttk.Label(self, text="Logi:").grid(row=10, column=0, sticky="w", pady=(PAD, 2))
        log_frame = tk.Frame(self, bg="#313244")
        log_frame.grid(row=11, column=0, sticky="nsew", pady=(0, PAD))
        self._log = tk.Text(log_frame, height=8, width=68, bg="#313244", fg="#a6e3a1",
                            font=("Courier New", 9), relief="flat", state="disabled",
                            wrap="word")
        scrollbar = ttk.Scrollbar(log_frame, command=self._log.yview)
        self._log.configure(yscrollcommand=scrollbar.set)
        self._log.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.columnconfigure(0, weight=1)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _paste_url(self):
        try:
            text = self.clipboard_get()
            self._url.set(text.strip())
        except tk.TclError:
            pass

    def _choose_dir(self):
        path = filedialog.askdirectory(initialdir=self._download_dir.get(),
                                       title="Wybierz folder docelowy")
        if path:
            self._download_dir.set(path)

    def _log_write(self, text: str):
        self._log.configure(state="normal")
        self._log.insert("end", text + "\n")
        self._log.see("end")
        self._log.configure(state="disabled")

    def _set_status(self, text: str):
        self._status.set(text)

    def _set_progress(self, value: float):
        self._progress["value"] = max(0, min(100, value))

    # ------------------------------------------------------------------
    # Download logic
    # ------------------------------------------------------------------

    def _start_download(self):
        url = self._url.get().strip()
        if not url:
            messagebox.showwarning("Brak URL", "Wpisz lub wklej link do wideo YouTube.")
            return
        if self._downloading:
            return

        dest = self._download_dir.get()
        os.makedirs(dest, exist_ok=True)

        fmt_label = self._format_combo.get()
        fmt_value = next(v for l, v in FORMATS if l == fmt_label)

        self._downloading = True
        self._dl_btn.configure(state="disabled")
        self._set_progress(0)
        self._set_status("Pobieranie...")
        self._log_write(f"--- Rozpoczynam pobieranie ---")
        self._log_write(f"URL:    {url}")
        self._log_write(f"Format: {fmt_label}")
        self._log_write(f"Cel:    {dest}")

        thread = threading.Thread(target=self._download,
                                  args=(url, fmt_value, dest),
                                  daemon=True)
        thread.start()

    def _download(self, url: str, fmt: str, dest: str):
        is_audio_only = "bestaudio" in fmt and "bestvideo" not in fmt

        ydl_opts = {
            "format": fmt,
            "outtmpl": os.path.join(dest, "%(title)s.%(ext)s"),
            "progress_hooks": [self._progress_hook],
            "logger": _YtdlLogger(self._log_write),
            "quiet": True,
            "no_warnings": False,
            "merge_output_format": "mp4",
        }

        if is_audio_only:
            ydl_opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            self.after(0, self._on_success)
        except Exception as exc:
            self.after(0, self._on_error, str(exc))

    def _progress_hook(self, d: dict):
        status = d.get("status", "")
        if status == "downloading":
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            speed = d.get("speed") or 0
            eta = d.get("eta") or 0

            pct = (downloaded / total * 100) if total else 0
            speed_str = f"{speed / 1024:.1f} KB/s" if speed else "—"
            eta_str = f"{eta}s" if eta else "—"
            filename = os.path.basename(d.get("filename", ""))

            self.after(0, self._set_progress, pct)
            self.after(0, self._set_status,
                       f"{filename}  |  {pct:.1f}%  |  {speed_str}  |  ETA: {eta_str}")

        elif status == "finished":
            self.after(0, self._set_progress, 100)
            self.after(0, self._log_write,
                       f"Pobrano: {os.path.basename(d.get('filename', ''))}")

    def _on_success(self):
        self._downloading = False
        self._dl_btn.configure(state="normal")
        self._set_status("Pobieranie zakonczone!")
        self._log_write("--- Sukces! Plik zapisany w: " + self._download_dir.get() + " ---\n")

    def _on_error(self, msg: str):
        self._downloading = False
        self._dl_btn.configure(state="normal")
        self._set_progress(0)
        self._set_status("Blad pobierania.")
        self._log_write(f"BLAD: {msg}\n")
        messagebox.showerror("Blad", msg)


class _YtdlLogger:
    """Przekierowuje logi yt-dlp do okna tekstowego aplikacji."""

    def __init__(self, write_fn):
        self._write = write_fn

    def debug(self, msg):
        if msg.startswith("[debug]"):
            return
        self._write(msg)

    def info(self, msg):
        self._write(msg)

    def warning(self, msg):
        self._write(f"[!] {msg}")

    def error(self, msg):
        self._write(f"[ERR] {msg}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
