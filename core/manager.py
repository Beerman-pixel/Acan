import time
import logging
import threading
import datetime
from pathlib import Path

# Import der Utilities für den Ganymede-Workflow
from utils.metadata_handler import setup_ganymede_folder, save_stream_metadata
from core.post_processor import PostProcessor

class PlatformManager:
    def __init__(self, config, platforms):
        self.config = config
        self.platforms = platforms
        
        # Tracking für aktive Prozesse
        self.active_recordings = {}      # {channel_id: subprocess_handle}
        self.recording_details = {}       # {channel_id: {paths, url, etc.}}
        self.waiting_for_reconnect = {}   # {channel_id: timestamp_of_disconnect}
        self.chat_tasks = set()
        self.vod_tasks = set()
        
        # Initialisiere den Post-Processor für das Chat-Rendering
        self.post_processor = PostProcessor()
        self.running = True

    def run(self):
        logging.info("Acan Manager gestartet (Ganymede-Workflow & Reconnect-Logic aktiv)...")
        while self.running:
            try:
                for platform_instance in self.platforms:
                    self._run_platform_logic(platform_instance)
                
                self._check_finished_processes()
                
            except Exception as e:
                logging.error(f"Fehler im Manager-Loop: {e}")
            
            time.sleep(60)

    def _run_platform_logic(self, platform_instance):
        for channel in platform_instance.config.channels(platform_instance.platform_name):
            channel_id = f"{platform_instance.platform_name}_{channel}"
            
            # Prüfen, ob der Kanal bereits aufgenommen wird
            if channel_id in self.active_recordings:
                continue

            # Check ob der Stream online ist (Plattform-spezifisch)
            if platform_instance.is_online(channel):
                
                # RECONNECT FALL: Nutzen wir einen bestehenden Ordner?
                if channel_id in self.recording_details:
                    logging.info(f"Reconnect erkannt für {channel_id}. Setze Aufnahme fort...")
                    details = self.recording_details[channel_id]
                    proc = platform_instance.record_live(details['video'])
                else:
                    # NEUER STREAM FALL
                    title = platform_instance._get_stream_title(channel)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
                    
                    stream_folder = setup_ganymede_folder(
                        platform_instance.platform_name, 
                        channel, 
                        title, 
                        timestamp
                    )
                    
                    video_path = stream_folder / "stream-Video.mp4"
                    chat_path = stream_folder / "stream-live-chat.jsonl"
                    
                    self.recording_details[channel_id] = {
                        'video': video_path,
                        'chat': chat_path,
                        'folder': stream_folder,
                        'url': platform_instance._get_full_url(channel) if hasattr(platform_instance, '_get_full_url') else channel
                    }
                    
                    proc = platform_instance.record_live(video_path)
                    
                    # Metadaten asynchron laden
                    threading.Thread(
                        target=save_stream_metadata, 
                        args=(self.recording_details[channel_id]['url'], stream_folder), 
                        daemon=True
                    ).start()

                if proc:
                    self.active_recordings[channel_id] = proc
                    # Chat starten falls aktiviert
                    if self.config.platform(platform_instance.platform_name).get("chat", False):
                        if channel_id not in self.chat_tasks:
                            self._start_chat_task(platform_instance, channel, channel_id)

    def _start_chat_task(self, platform_instance, channel, channel_id):
        if channel_id in self.recording_details:
            chat_out_file = self.recording_details[channel_id]['chat']
            
            # Dynamischer Import der Chat-Module
            target_func = None
            if platform_instance.platform_name == "kick":
                from utils.kick_chat import record_kick_chat
                target_func = record_kick_chat
            
            if target_func:
                logging.info(f"Starte Chat-Recording für {channel_id}")
                threading.Thread(target=target_func, args=(channel, chat_out_file), daemon=True).start()
                self.chat_tasks.add(channel_id)

    def _check_finished_processes(self):
        now = time.time()
        
        # 1. Beendete Prozesse in die Warteschlange schieben
        for channel_id, proc in list(self.active_recordings.items()):
            if proc.poll() is not None:
                logging.info(f"Stream unterbrochen: {channel_id}. Warte auf Reconnect (5 Min)...")
                self.waiting_for_reconnect[channel_id] = now
                del self.active_recordings[channel_id]

        # 2. Prüfen, ob die 5 Minuten um sind
        for channel_id, start_wait_time in list(self.waiting_for_reconnect.items()):
            # Wenn der Prozess in _run_platform_logic wieder gestartet wurde
            if channel_id in self.active_recordings:
                del self.waiting_for_reconnect[channel_id]
                continue
                
            # Wenn 5 Minuten (300 Sek) abgelaufen sind -> Finalisieren
            if now - start_wait_time > 300:
                logging.info(f"Gnadenfrist abgelaufen für {channel_id}. Starte Post-Processing...")
                details = self.recording_details.get(channel_id)
                if details:
                    self.post_processor.add_job(details['video'], details['chat'])
                
                # Cleanup
                self.waiting_for_reconnect.pop(channel_id, None)
                self.recording_details.pop(channel_id, None)
                if channel_id in self.chat_tasks: self.chat_tasks.remove(channel_id)