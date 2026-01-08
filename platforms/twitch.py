import subprocess
import logging
import datetime
import re
from .base import PlatformBase

class TwitchPlatform(PlatformBase):
    platform_name = "twitch"

    def _get_full_url(self):
        # Falls nur der Name angegeben wurde, bauen wir die URL
        if "twitch.tv" not in self.channel:
            return f"https://www.twitch.tv/{self.channel}"
        return self.channel

    def _get_clean_name(self):
        return self.channel.rstrip("/").split('/')[-1]

    def _get_stream_title(self, url):
        try:
            # yt-dlp braucht die volle URL
            cmd = ["yt-dlp", "--get-title", "--no-warnings", url]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            title = result.stdout.strip()
            return re.sub(r'[\\/*?:"<>|]', "", title) if title else "Live_Stream"
        except Exception:
            return "Live_Stream"

    def record_live(self):
        clean_name = self._get_clean_name()
        full_url = self._get_full_url()
        base_out = self.config.output_dir(self.platform_name) / clean_name
        base_out.mkdir(parents=True, exist_ok=True)
        
        stream_title = self._get_stream_title(full_url)
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y%m%d_%H%M")
        
        filename = f"{clean_name}_{timestamp}_{stream_title}.mp4"
        output_file = base_out / filename

        quality = self.config.quality(self.platform_name)
        if "+" in quality: quality = "best"

        cmd = [
            "streamlink", full_url, quality,
            "-o", str(output_file),
            "--twitch-disable-ads",
            "--retry-streams", "30"
        ]
        
        try:
            logging.info(f"[{self.platform_name}] Starte Aufnahme: {filename}")
            return subprocess.Popen(cmd)
        except Exception as e:
            logging.error(f"Fehler bei Twitch Live ({clean_name}): {e}")
            return None

    def download(self):
        if not self.config.platform(self.platform_name).get("download_vods", True):
            return

        clean_name = self._get_clean_name()
        full_url = self._get_full_url()
        base_out = self.config.output_dir(self.platform_name) / clean_name
        archive_file = base_out / "archive.txt"

        for ep in ["videos", "clips"]:
            logging.info(f"[{self.platform_name}] Scanne {ep} für {clean_name}...")
            url = f"{full_url}/{ep}" # Korrekte URL-Zusammensetzung

            cmd = [
                "yt-dlp",
                "--download-archive", str(archive_file),
                "-f", "bestvideo+bestaudio/best",
                "-o", str(base_out / ep / "%(title)s.%(ext)s"),
                "--playlist-end", "5",
                url
            ]
            subprocess.run(cmd, check=False)