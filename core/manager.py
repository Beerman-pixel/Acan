from platforms.youtube import YouTubePlatform
from platforms.twitch import TwitchPlatform
from platforms.kick import KickPlatform
from concurrent.futures import ThreadPoolExecutor
import time
import logging

PLATFORMS = {
    "youtube": YouTubePlatform,
    "twitch": TwitchPlatform,
    "kick": KickPlatform,
}

class PlatformManager:
    def __init__(self, config):
        self.config = config
        self.executor = ThreadPoolExecutor(max_workers=10)
        self.active_tasks = set()

    def _run_platform_logic(self, platform_instance):
        """Wird im Thread ausgeführt: Prüft erst Live, dann VODs."""
        channel_id = f"{platform_instance.platform_name}_{platform_instance.channel}"
        
        if channel_id in self.active_tasks:
            return 
        
        self.active_tasks.add(channel_id)
        try:
            # 1. Live Recording (Streamlink läuft im Hintergrund weiter)
            if self.config.platform(platform_instance.platform_name).get("record_live", True):
                platform_instance.record_live()

            # 2. VOD/Clip Download (Blockiert diesen Thread, bis yt-dlp fertig ist)
            platform_instance.download()
            
        except Exception as e:
            logging.error(f"Fehler bei {channel_id}: {e}")
        finally:
            self.active_tasks.remove(channel_id)

    def run(self):
        logging.info("Acan Manager gestartet...")
        while True:
            for name, cls in PLATFORMS.items():
                if not self.config.platform_enabled(name):
                    continue

                channels = self.config.channels(name)
                for channel in channels:
                    # Plattform-Instanz erstellen
                    platform = cls(self.config, channel)
                    # Task an den Pool übergeben
                    self.executor.submit(self._run_platform_logic, platform)

            logging.info(f"Check abgeschlossen. Warte {self.config.check_interval}s...")
            time.sleep(self.config.check_interval)