from app.platforms.youtube import YouTubePlatform
from app.platforms.twitch import TwitchPlatform
from app.platforms.kick import KickPlatform

PLATFORMS = {
    "youtube": YouTubePlatform,
    "twitch": TwitchPlatform,
    "kick": KickPlatform,
}

class PlatformManager:
    def __init__(self, config):
        self.config = config

    def run(self):
        for name, platform_cls in PLATFORMS.items():
            if self.config.platform_enabled(name):
                platform = platform_cls(self.config)
                platform.process()
