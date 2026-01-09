import subprocess
import json
import logging
import threading
import queue
from pathlib import Path

class PostProcessor:
    def __init__(self):
        self.queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()

    def add_job(self, video_path, json_path):
        self.queue.put((video_path, json_path))
        logging.info(f"[Post-Processor] Job zur Warteschlange hinzugefügt: {video_path.name}")

    def _worker(self):
        while True:
            video_path, json_path = self.queue.get()
            try:
                self._render_chat(video_path, json_path)
            except Exception as e:
                logging.error(f"[Post-Processor] Fehler beim Rendern: {e}")
            finally:
                self.queue.task_done()

    def _render_chat(self, video_path, json_path):
        if not json_path.exists():
            logging.warning(f"Keine Chat-Datei gefunden für {video_path.name}")
            return

        output_chat_mp4 = video_path.parent / f"{video_path.stem}_chat.mp4"
        temp_text = video_path.parent / "temp_chat_lines.txt"

        # 1. JSONL zu Text formatieren (FFmpeg drawtext kompatibel)
        try:
            with open(json_path, 'r', encoding='utf-8') as f_in, open(temp_text, 'w', encoding='utf-8') as f_out:
                for line in f_in:
                    data = json.loads(line)
                    user = data.get('author', 'User')
                    msg = data.get('message', '').replace(":", " ").replace("'", "")
                    f_out.write(f"{user}: {msg}\n")
        except Exception as e:
            logging.error(f"Fehler bei Chat-Vorbereitung: {e}")
            return

        # 2. FFmpeg Rendering
        # Erstellt ein Video mit schwarzem Hintergrund und weißem Text
        cmd = [
            "ffmpeg", "-y",
            "-f", "lavfi", "-i", "color=c=black:s=400x1080:r=30",
            "-vf", f"drawtext=textfile='{temp_text}':fontcolor=white:fontsize=20:x=10:y=h-line_h-10",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-shortest",
            str(output_chat_mp4)
        ]

        logging.info(f"Starte FFmpeg Chat-Rendering: {output_chat_mp4.name}")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            logging.info(f"[SUCCESS] Chat-Video erstellt: {output_chat_mp4.name}")
            if temp_text.exists(): temp_text.unlink() # Aufräumen
        else:
            logging.error(f"[FFMPEG ERROR] {result.stderr}")