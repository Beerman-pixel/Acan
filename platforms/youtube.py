from .base import PlatformBase
import subprocess
import logging
import datetime
import re

class YouTubePlatform(PlatformBase):
    platform_name = "youtube"

    def _get_clean_name(self):
        name = self.channel.split('/')[-1]
        return name.replace('@', '')

    def _get_stream_title(self, url):
        """Holt den aktuellen Titel des Livestreams."""
        try:
            cmd = [
                "yt-dlp", "--get-title", "--no-warnings", "--ignore-errors", url
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            title = result.stdout.strip()
            # Zeichen entfernen, die in Dateinamen nicht erlaubt sind
            title = re.sub(r'[\\/*?:"<>|]', "", title)
            return title if title else "Unbekannter_Titel"
        except Exception:
            return "Live_Stream"

    def record_live(self):
        clean_name = self._get_clean_name()
        base_out = self.config.output_dir(self.platform_name) / clean_name
        base_out.mkdir(parents=True, exist_ok=True)
        
        url = self.channel.rstrip("/") + "/live"
        
        # 1. Titel abfragen
        stream_title = self._get_stream_title(url)
        
        # 2. Zeitstempel mit Datum UND Uhrzeit (StundeMinute)
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d")
        time_str = now.strftime("%H%M")
        
        # 3. Neues Format: Kanal_Datum_Uhrzeit_Titel
        filename = f"{clean_name}_{timestamp}_{time_str}_{stream_title}.mp4"
        output_file = base_out / filename


        quality = self.config.quality(self.platform_name)
        if "+" in quality: quality = "best"

        cmd = [
            "streamlink", url, quality,
            "-o", str(output_file),
            "--loglevel", "info",
            "--retry-streams", "30"
        ]
        
        try:
            logging.info(f"[{self.platform_name}] Aufnahme startet: {filename}")
            return subprocess.Popen(cmd)
        except Exception as e:
            logging.error(f"Fehler bei YouTube Live ({clean_name}): {e}")
            return None

    def download(self):
        """Lädt Videos, Shorts, vergangene Streams und Playlists herunter."""
        if not self.config.platform(self.platform_name).get("download_vods", True):
            return

        clean_name = self._get_clean_name()
        base_out = self.config.output_dir(self.platform_name) / clean_name
        base_out.mkdir(parents=True, exist_ok=True)
        archive_file = base_out / "archive.txt"

        # Liste der zu scannenden Endpunkte
        # /videos -> Normale Uploads
        # /shorts -> YouTube Shorts
        # /streams -> Vergangene (beendete) Livestreams
        # /playlists -> Alle öffentlichen Playlists des Kanals
        endpoints = ["videos", "shorts", "streams", "playlists"]
        
        for endpoint in endpoints:
            logging.info(f"[{self.platform_name}] Scanne {endpoint} für {clean_name}...")
            url = f"{self.channel.rstrip('/')}/{endpoint}"
            
            # Bei Playlists schauen wir tiefer (z.B. die letzten 20 Playlists),
            # bei Videos/Shorts reichen die neuesten 5 für den schnellen Check.
            limit = "20" if endpoint == "playlists" else "5"
            if not archive_file.exists(): limit = "100" # Erster Scan: Viel laden

            cmd = [
                "yt-dlp",
                "--ignore-errors",
                "--no-warnings",
                "--download-archive", str(archive_file),
                "--no-live-from-start",
                "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "-o", str(base_out / endpoint / "%(playlist_title)s" / "%(title)s.%(ext)s" if endpoint == "playlists" else base_out / endpoint / "%(title)s.%(ext)s"),
                "--playlist-end", limit,
                url
            ]
            
            try:
                subprocess.run(cmd, check=False)
            except Exception as e:
                logging.error(f"Fehler beim Scan von {endpoint}: {e}")

        logging.info(f"[{self.platform_name}] Vollständiger VOD-Scan für {clean_name} beendet.")