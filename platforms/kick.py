import subprocess
import logging
import requests
import re
from .base import PlatformBase

class KickPlatform(PlatformBase):
    def __init__(self, config):
        # Wir rufen die Basisklasse nur mit config auf
        super().__init__(config)
        self.platform_name = "kick"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }

    def is_online(self, channel_name):
        """Prüft über die Kick API, ob der Kanal live ist."""
        url = f"https://kick.com/api/v1/channels/{channel_name}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return data.get("livestream") is not None
            return False
        except Exception as e:
            logging.error(f"[Kick] Fehler beim Online-Check für {channel_name}: {e}")
            return False

    def _get_full_url(self, channel_name):
        """Gibt die vollständige URL für den Kanal zurück."""
        return f"https://kick.com/{channel_name}"

    def _get_stream_title(self, channel_name):
        """Holt den aktuellen Titel des Kick-Streams via API."""
        url = f"https://kick.com/api/v1/channels/{channel_name}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                title = data.get("livestream", {}).get("session_title", "Live_Stream")
                # Ungültige Zeichen entfernen
                return re.sub(r'[\\/*?:"<>|]', "", title)
        except Exception:
            pass
        return "Live_Stream"

    def record_live(self, video_path):
        """
        Startet die Aufnahme. 
        Der video_path wird vom Manager (Ganymede-Struktur) vorgegeben.
        """
        # Wir extrahieren den Kanalnamen aus dem Pfad oder nutzen die URL
        # Da der Manager video_path übergibt, nutzen wir diesen direkt
        url = self._get_full_url(video_path.parent.parent.name) # Holt Kanalname aus Ordnerstruktur
        
        quality = self.config.quality(self.platform_name)
        if "+" in quality: quality = "best"

        cmd = [
            "streamlink",
            url,
            quality,
            "-o", str(video_path),
            "--loglevel", "info",
            "--retry-streams", "30",
            "--retry-open", "30",
        ]
        
        try:
            logging.info(f"[{self.platform_name}] Starte Aufnahme in: {video_path.name}")
            return subprocess.Popen(cmd)
        except Exception as e:
            logging.error(f"Fehler bei Kick Live Start: {e}")
            return None

    def download(self, channel_name):
        """Scannt nach VODs und Clips für einen spezifischen Kanal."""
        if not self.config.platform(self.platform_name).get("download_vods", True):
            return

        # Pfad-Logik für VODs (simpel gehalten)
        output_root = self.config.platform(self.platform_name).get("output_dir", "~/Downloads/kick")
        base_out = self.config.path(output_root) / channel_name / "VODs"
        base_out.mkdir(parents=True, exist_ok=True)
        archive_file = base_out / "archive.txt"

        logging.info(f"[{self.platform_name}] Starte VOD-Scan für {channel_name}...")
        
        cmd = [
            "yt-dlp",
            "--ignore-errors",
            "--no-warnings",
            "--download-archive", str(archive_file),
            "-o", str(base_out / "%(upload_date)s_%(title)s.%(ext)s"),
            f"https://kick.com/{channel_name}/videos"
        ]

        try:
            subprocess.run(cmd, check=False)
            logging.info(f"[{self.platform_name}] VOD-Scan für {channel_name} abgeschlossen.")
        except Exception as e:
            logging.error(f"yt-dlp Fehler bei {channel_name}: {e}")