import subprocess
import logging
from .base import PlatformBase

class YouTubePlatform(PlatformBase):
    def __init__(self, config):
        super().__init__(config)
        self.platform_name = "youtube"

    def is_online(self, channel_name):
        """Prüft via yt-dlp, ob ein Live-Stream läuft."""
        url = f"https://www.youtube.com/@{channel_name}/live"
        try:
            cmd = ["yt-dlp", "--get-id", "--is-live", url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return result.returncode == 0 and result.stdout.strip() != ""
        except Exception:
            return False

    def _get_full_url(self, channel_name):
        return f"https://www.youtube.com/@{channel_name}/live"

    def _get_stream_title(self, channel_name):
        return "YouTube Live Stream"

    def record_live(self, video_path):
        channel = video_path.parent.parent.name
        url = self._get_full_url(channel)
        
        cmd = [
            "streamlink", url, "best",
            "-o", str(video_path),
            "--retry-streams", "30"
        ]
        try:
            logging.info(f"[YouTube] Starte Aufnahme: {video_path.name}")
            return subprocess.Popen(cmd)
        except Exception as e:
            logging.error(f"[YouTube] Fehler: {e}")
            return None