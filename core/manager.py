import time
import logging
import threading
import datetime
from pathlib import Path

# Import der neuen Utilities für den Ganymede-Workflow
from utils.metadata_handler import setup_ganymede_folder, save_stream_metadata
from core.post_processor import PostProcessor

class PlatformManager:
    def __init__(self, config, platforms):
        self.config = config
        self.platforms = platforms  # Liste der Platform-Instanzen (YouTube, Twitch, Kick)
        
        # Tracking für aktive Prozesse
        self.active_recordings = {}  # {channel_id: subprocess_handle}
        self.recording_details = {}   # {channel_id: {'video': path, 'chat': path}}
        self.chat_tasks = set()
        self.vod_tasks = set()
        
        # Initialisiere den Post-Processor für das Chat-Rendering
        self.post_processor = PostProcessor()
        
        self.running = True

    def run(self):
        logging.info("Acan Manager gestartet (Ganymede-Workflow aktiv)...")
        while self.running:
            try:
                for platform_instance in self.platforms:
                    self._run_platform_logic(platform_instance)
                
                self._check_finished_processes()
                
            except Exception as e:
                logging.error(f"Fehler im Manager-Loop: {e}")
            
            time.sleep(60)  # Check alle 60 Sekunden

    def _run_platform_logic(self, platform_instance):
        for channel in platform_instance.config.channels(platform_instance.platform_name):
            channel_id = f"{platform_instance.platform_name}_{channel}"
            
            # 1. LIVE-RECORDING & METADATA
            if channel_id not in self.active_recordings:
                # Hole Titel und bereite Ganymede-Struktur vor
                url = platform_instance._get_full_url() if hasattr(platform_instance, '_get_full_url') else channel
                title = platform_instance._get_stream_title(url)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
                
                # Erstelle den spezifischen Stream-Ordner
                stream_folder = setup_ganymede_folder(
                    platform_instance.platform_name, 
                    platform_instance._get_clean_name(), 
                    title, 
                    timestamp
                )
                
                # Starte Aufnahme
                video_path = stream_folder / "stream-Video.mp4"
                chat_path = stream_folder / "stream-live-chat.jsonl"
                
                proc = platform_instance.record_live(video_path)
                
                if proc:
                    self.active_recordings[channel_id] = proc
                    self.recording_details[channel_id] = {
                        'video': video_path,
                        'chat': chat_path,
                        'url': url
                    }
                    
                    # Sofort Metadaten & Thumbnail sichern (Ganymede-Style)
                    threading.Thread(
                        target=save_stream_metadata, 
                        args=(url, stream_folder), 
                        daemon=True
                    ).start()

            # 2. CHAT-RECORDING
            if self.config.platform(platform_instance.platform_name).get("chat", False):
                if channel_id not in self.chat_tasks:
                    self._start_chat_task(platform_instance, channel, channel_id)

            # 3. VOD/CLIP DOWNLOADS (Läuft parallel im Hintergrund)
            if channel_id not in self.vod_tasks:
                threading.Thread(target=platform_instance.download, daemon=True).start()
                self.vod_tasks.add(channel_id)

    def _start