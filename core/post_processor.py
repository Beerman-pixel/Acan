import threading
import queue
import logging
import subprocess

class PostProcessor:
    def __init__(self):
        self.queue = queue.Queue()
        self.worker = threading.Thread(target=self._run, daemon=True)
        self.worker.start()

    def add_job(self, video_path, json_path):
        self.queue.put((video_path, json_path))
        logging.info(f"[PostProcessor] Job eingereiht: {video_path.name}")

    def _run(self):
        while True:
            video_path, json_path = self.queue.get()
            try:
                self._render(video_path, json_path)
            except Exception as e:
                logging.error(f"[PostProcessor] Fehler beim Rendering: {e}")
            finally:
                self.queue.task_done()

    def _render(self, video_path, json_path):
        output_chat = video_path.parent / "stream-Chat.mp4"
        logging.info(f"[PostProcessor] Starte Rendering: {output_chat}")

        # Dies ist ein Platzhalter-Kommando. 
        # Es nutzt FFmpeg um den Chat visuell aufzubereiten.
        # Ein gängiges Tool dafür ist 'chat-downloader --visualize'
        cmd = [
            "chat-downloader",
            str(json_path),
            "--output", str(output_chat),
            # Hier kommen Parameter für Font, Farbe, Position rein
        ]
        
        # Hinweis: Da echtes MP4-Chat-Rendering komplex ist, 
        # nutzen viele User oft 'twitch-chat-render' (Node.js)
        subprocess.run(cmd, check=True)
        logging.info(f"[PostProcessor] Fertig: {output_chat}")