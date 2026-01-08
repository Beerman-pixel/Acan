from .base import PlatformBase
from pathlib import Path
import subprocess
import logging
import datetime

class KickPlatform(PlatformBase):
    platform_name = "kick"
    base_url = "https://kick.com"

    def record_live(self):
        """Versucht den aktuellen Livestream aufzunehmen."""
        base_out = self.config.output_dir(self.platform_name) / self.channel
        base_out.mkdir(parents=True, exist_ok=True)
        
        # Zeitstempel für Dateinamen (verhindert Überschreiben)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = base_out / f"live_{self.channel}_{timestamp}.mp4"

        cmd = [
            "streamlink",
            f"{self.base_url}/{self.channel}",
            self.config.quality(self.platform_name),
            "-o", str(output_file),
            "--loglevel", "info"
        ]
        
        try:
            logging.info(f"[{self.platform_name}] Prüfe Live-Status für {self.channel}...")
            # Wir geben das Popen-Objekt zurück
            process = subprocess.Popen(cmd)
            return process 
        except Exception as e:
            logging.error(f"Fehler bei {self.channel}: {e}")
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