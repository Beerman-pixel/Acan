from platforms.youtube import YouTubePlatform
from platforms.twitch import TwitchPlatform
from platforms.kick import KickPlatform
from concurrent.futures import ThreadPoolExecutor
import time
import logging
import threading

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
        self.live_recordings = set()
        self.chat_tasks = set() # Tracking für Chat-Threads

    def _run_platform_logic(self, platform_instance):
        channel_id = f"{platform_instance.platform_name}_{platform_instance.channel}"
        
        if channel_id in self.active_tasks:
            return 
        
        self.active_tasks.add(channel_id)
        try:
            # 1. LIVE-RECORDING (Parallel)
            if self.config.platform(platform_instance.platform_name).get("record_live", True):
                if channel_id not in self.live_recordings:
                    logging.info(f"Starte Live-Recording Task für {channel_id}")
                    threading.Thread(
                        target=self._handle_live_recording, 
                        args=(platform_instance, channel_id), 
                        daemon=True
                    ).start()

            # 2. CHAT-RECORDING
            if self.config.platform(platform_instance.platform_name).get("chat", False):
                if channel_id not in self.chat_tasks:
                    chat_out = self.config.output_dir(platform_instance.platform_name) / platform_instance.channel
                    
                    if platform_instance.platform_name == "kick":
                        from utils.kick_chat import record_kick_chat
                        target_func = record_kick_chat
                        args = (platform_instance.channel, chat_out)
                    elif platform_instance.platform_name == "youtube":
                        from utils.youtube_chat import record_youtube_chat
                        target_func = record_youtube_chat
                        args = (platform_instance.channel, chat_out) # Hier ist channel die URL
                    
                    logging.info(f"Starte Chat-Recording für {channel_id}")
                    threading.Thread(
                        target=target_func,
                        args=args,
                        daemon=True
                    ).start()
                    self.chat_tasks.add(channel_id)

            # 3. VOD-DOWNLOAD (Jetzt ebenfalls im eigenen Thread!)
            # So blockiert das Live-Recording den Download nicht mehr.
            logging.info(f"Starte VOD-Check Thread für {channel_id}")
            threading.Thread(
                target=platform_instance.download,
                daemon=True
            ).start()
            
        except Exception as e:
            logging.error(f"Fehler bei {channel_id}: {e}")
        finally:
            self.active_tasks.remove(channel_id)

    def _handle_live_recording(self, platform_instance, channel_id):
        self.live_recordings.add(channel_id)
        try:
            process = platform_instance.record_live() 
            if process:
                process.wait() 
        finally:
            logging.info(f"Live-Recording für {channel_id} beendet.")
            self.live_recordings.discard(channel_id)

    def _handle_chat_recording(self, channel_id, channel_name, output_dir):
        self.chat_tasks.add(channel_id)
        try:
            from utils.kick_chat import record_kick_chat
            record_kick_chat(channel_name, output_dir)
        finally:
            logging.info(f"Chat-Recording für {channel_id} beendet.")
            self.chat_tasks.discard(channel_id)

    def run(self):
        logging.info("Acan Manager gestartet...")
        while True:
            for name, cls in PLATFORMS.items():
                if not self.config.platform_enabled(name):
                    continue

                channels = self.config.channels(name)
                for channel in channels:
                    platform = cls(self.config, channel)
                    self.executor.submit(self._run_platform_logic, platform)

            logging.info(f"Check abgeschlossen. Aktive Aufnahmen: {list(self.live_recordings)}")
            time.sleep(self.config.check_interval)