from .base import PlatformBase
from pathlib import Path
import subprocess

class YouTubePlatform(PlatformBase):
    platform_name = "youtube"

    def record_live(self):
        base_out = self.config.output_dir(self.platform_name) / self.channel
        base_out.mkdir(parents=True, exist_ok=True)

        cmd = [
            "yt-dlp",
            "--ignore-errors",
            "--live-from-start",
            "--download-archive", str(base_out / "archive.txt"),
            "-f", self.config.quality(self.platform_name),
            "-o", str(base_out / "%(uploader)s/%(title)s.%(ext)s"),
            f"{self.channel}"
        ]
        subprocess.Popen(cmd)

    def download(self):
        base_out = self.config.output_dir(self.platform_name) / self.channel
        base_out.mkdir(parents=True, exist_ok=True)

        cmd = [
            "yt-dlp",
            "--ignore-errors",
            "--yes-playlist",
            "--download-archive", str(base_out / "archive.txt"),
            "-f", self.config.quality(self.platform_name),
            "-o", str(base_out / "%(uploader)s/%(title)s.%(ext)s"),
            f"{self.channel}"
        ]
        subprocess.run(cmd)
