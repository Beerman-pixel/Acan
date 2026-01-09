import subprocess
import logging
from .base import PlatformBase

class TwitchPlatform(PlatformBase):
    def __init__(self, config):
        super().__init__(config)
        self.platform_name = "twitch"

    def is_online(self, channel_name):
        """Prüft via Streamlink, ob der Kanal live ist."""
        url = self._get_full_url(channel_name)
        try:
            # --can-handle-url prüft nur, ob die URL valide ist
            # Wir nutzen --stream-url, um zu sehen, ob ein Stream existiert
            cmd = ["streamlink", "--stream-url", url, "best"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            return "master.m3u8" in result.stdout or "https://" in result.stdout
        except Exception:
            return False

    def _get_full_url(self, channel_name):
        return f"https://twitch.tv/{channel_name}"

    def _get_stream_title(self, channel_name):
        return "Twitch Live Stream"

    def record_live(self, video_path):
        channel = video_path.parent.parent.name
        url = self._get_full_url(channel)
        
        cmd = [
            "streamlink", url, "best",
            "-o", str(video_path),
            "--retry-streams", "30",
            "--retry-open", "30"
        ]

        try:
            logging.info(f"[Twitch] Starte Aufnahme: {video_path.name}")
            return subprocess.Popen(cmd)
        except Exception as e:
            logging.error(f"[Twitch] Fehler: {e}")
            return None