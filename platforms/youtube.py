import subprocess
from .base import PlatformBase
from pathlib import Path

class YouTubePlatform(PlatformBase):
    platform_name = "youtube"

    def process_channel(self, channel_url: str):
        base_out = Path(self.config.output_dir) / "youtube"
        archive = base_out / "archive.txt"

        cmd = [
            "yt-dlp",
            "--ignore-errors",
            "--yes-playlist",
            "--download-archive", str(archive),
            "-f", self.config.data["youtube"].get("quality", self.config.quality),
            "-o", f"{base_out}/%(uploader)s/%(playlist_title,Videos)s/%(title)s.%(ext)s",
        ]

        yt_cfg = self.config.data["youtube"]

        if yt_cfg.get("record_live"):
            cmd += ["--live-from-start"]

        if not yt_cfg.get("shorts", True):
            cmd += ["--match-filter", "!is_short"]

        if yt_cfg.get("monitor_new"):
            cmd += ["--dateafter", "now-7days"]

        cmd.append(channel_url)

        subprocess.run(cmd)

    def process(self):
        for channel in self.config.channels("youtube"):
            self.process_channel(channel)

