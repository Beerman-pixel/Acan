import subprocess
import logging
import datetime
import re
from .base import PlatformBase

class KickPlatform(PlatformBase):
    platform_name = "kick"

    def _get_clean_name(self):
        # Extrahiert den Namen aus der URL (z.B. https://kick.com/name -> name)
        return self.channel.split('/')[-1]

    def _get_stream_title(self, url):
        """Holt den aktuellen Titel des Kick-Streams via yt-dlp."""
        try:
            # Wir nutzen yt-dlp, um nur den Titel zu extrahieren
            cmd = [
                "yt-dlp", "--get-title", "--no-warnings", "--ignore-errors", url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            title = result.stdout.strip()
            # Entferne ungültige Dateinamen-Zeichen
            title = re.sub(r'[\\/*?:"<>|]', "", title)
            return title if title else "Live_Stream"
        except Exception:
            return "Live_Stream"

    def record_live(self):
        clean_name = self._get_clean_name()
        base_out = self.config.output_dir(self.platform_name) / clean_name
        base_out.mkdir(parents=True, exist_ok=True)
        
        url = self.channel
        
        # 1. Titel abfragen
        stream_title = self._get_stream_title(url)
        
        # 2. Zeitstempel mit Datum und Uhrzeit
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M")
        
        # 3. Format: Kanal_Datum_Uhrzeit_Titel
        filename = f"{clean_name}_{timestamp}_{time_str}_{stream_title}.mp4"
        output_file = base_out / filename


        quality = self.config.quality(self.platform_name)
        # Streamlink braucht 'best' statt 'bestvideo+bestaudio'
        if "+" in quality: quality = "best"

        cmd = [
            "streamlink",
            url,
            quality,
            "-o", str(output_file),
            "--loglevel", "info",
            "--retry-streams", "30"
        ]
        
        try:
            logging.info(f"[{self.platform_name}] Starte Aufnahme: {filename}")
            return subprocess.Popen(cmd)
        except Exception as e:
            logging.error(f"Fehler bei Kick Live ({clean_name}): {e}")
            return None


    def download(self):
        """Scannt nach VODs und Clips. Verhindert den Abbruch, wenn Kanal offline ist."""
        if not self.config.platform(self.platform_name).get("download_vods", True):
            return

        base_out = self.config.output_dir(self.platform_name) / self.channel
        base_out.mkdir(parents=True, exist_ok=True)
        archive_file = base_out / "archive.txt"

        logging.info(f"[{self.platform_name}] Starte VOD-Scan für {self.channel}...")
        
        cmd = [
            "yt-dlp",
            "--ignore-errors",
            "--no-warnings",
            "--download-archive", str(archive_file),
            "--cookies-from-browser", "chromium",
            "-o", str(base_out / "%(title)s.%(ext)s"),
            # WICHTIG: Wir deaktivieren den speziellen Kick-Extraktor für die URL-Erkennung,
            # damit er nicht versucht, den Live-Status zu prüfen.
            "--ies", "generic",
            # Wir fügen /videos hinzu
            f"https://kick.com/{self.channel}/videos"
        ]

        try:
            subprocess.run(cmd, check=False)
            
            # Falls oben nichts gefunden wurde (weil Kick die Links versteckt),
            # probieren wir einen zweiten Versuch direkt auf die Video-API,
            # falls du die Clips auch willst:
            logging.info(f"[{self.platform_name}] VOD-Scan für {self.channel} abgeschlossen.")
        except Exception as e:
            logging.error(f"yt-dlp Fehler bei {self.channel}: {e}")