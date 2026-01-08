import subprocess
from .base import PlatformBase

class TwitchPlatform(PlatformBase):
    def process(self):
        for channel in self.config.channels("twitch"):
            cmd = [
                "streamlink",
                f"twitch.tv/{channel}",
                self.config.quality,
                "-o", f"{self.config.output_dir}/twitch/{channel}.mp4"
            ]
            subprocess.run(cmd)
