from .base import PlatformBase
from pathlib import Path
import subprocess

class TwitchPlatform(PlatformBase):
    platform_name = "twitch"
    base_url = "https://twitch.tv"

    def record_live(self):
        base_out = self.config.output_dir(self.platform_name) / self.channel
        base_out.mkdir(parents=True, exist_ok=True)

        cmd = [
            "streamlink",
            f"{self.base_url}/{self.channel}",
            self.config.quality(self.platform_name),
            "-o", str(base_out / "live.mp4")
        ]
        subprocess.Popen(cmd)

    def download(self):
        base_out = self.config.output_dir(self.platform_name) / self.channel
        base_out.mkdir(parents=True, exist_ok=True)

        cmd = [
            "yt-dlp",
            f"https://twitch.tv/{self.channel}/videos",
            "-o", str(base_out / "vods/%(title)s.%(ext)s")
        ]
        subprocess.run(cmd)
