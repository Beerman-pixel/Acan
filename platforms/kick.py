import subprocess
from .base import PlatformBase

class KickPlatform(PlatformBase):
    def process(self):
        for channel in self.config.channels("kick"):
            cmd = [
                "streamlink",
                f"https://kick.com/{channel}",
                self.config.quality,
                "-o", f"{self.config.output_dir}/kick/{channel}.mp4"
            ]
            subprocess.run(cmd)
