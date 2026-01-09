import time
import logging
import threading
import datetime
from pathlib import Path

from utils.metadata_handler import setup_ganymede_folder, save_stream_metadata
from core.post_processor import PostProcessor

class PlatformManager:
    def __init__(self, config, platforms):
        self.config = config
        self.platforms = platforms
        
        self.active_recordings = {}      # {channel_id: subprocess_handle}
        self.recording_details = {}       # {channel_id: {folder, base_name, video, chat, url, platform}}
        self.waiting_for_reconnect = {}   # {channel_id: timestamp}
        self.post_processor = PostProcessor()
        self.running = True

    def run(self):
        logging.info("Acan Manager aktiv. Überwachung der Kanäle läuft...")
        while self.running:
            try:
                for platform in self.platforms:
                    self._process_platform(platform)
                self._check_finished_processes()
            except Exception as e:
                logging.error(f"Fehler im Manager-Loop: {e}")
            time.sleep(60)

    def _process_platform(self, platform):
        # Kanäle aus der Config für diese Plattform holen
        channels = self.config.channels(platform.platform_name)
        if not channels:
            return

        for channel in channels:
            if not channel: continue
            channel_id = f"{platform.platform_name}_{channel}"
            
            # 1. Prüfen, ob bereits eine Aufnahme für diesen Kanal läuft
            if channel_id in self.active_recordings:
                if self.active_recordings[channel_id].poll() is not None:
                    logging.info(f"Stream-Prozess beendet: {channel_id}")
                    self.active_recordings.pop(channel_id)
                    self.waiting_for_reconnect[channel_id] = time.time()
                continue

            # 2. Online-Check
            if platform.is_online(channel):
                proc = None
                
                # Falls wir auf einen Reconnect gewartet haben (Gnadenfrist)
                if channel_id in self.recording_details:
                    logging.info(f"Reconnect erkannt: {channel_id}. Setze Aufnahme fort.")
                    details = self.recording_details[channel_id]
                    proc = platform.record_live(details['video'])
                    self.waiting_for_reconnect.pop(channel_id, None)
                else:
                    # Neuer Stream: Ordnerstruktur und Metadaten initialisieren
                    title = platform._get_stream_title(channel)
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
                    output_root = self.config.platform(platform.platform_name).get("output_dir", "~/Downloads")
                    
                    stream_folder, base_name = setup_ganymede_folder(
                        output_root, platform.platform_name, channel, title, timestamp
                    )
                    
                    details = {
                        'folder': stream_folder,
                        'base_name': base_name,
                        'video': stream_folder / f"{base_name}.mp4",
                        'chat_json': stream_folder / f"{base_name}_chat.jsonl",
                        'url': platform._get_full_url(channel) if hasattr(platform, '_get_full_url') else channel,
                        'platform': platform.platform_name
                    }
                    self.recording_details[channel_id] = details
                    proc = platform.record_live(details['video'])
                    
                    # Metadaten (Thumbnail/JSON) im Hintergrund laden
                    threading.Thread(
                        target=save_stream_metadata, 
                        args=(details['url'], stream_folder, base_name), 
                        daemon=True
                    ).start()

                # 3. Wenn Aufnahme erfolgreich gestartet wurde -> Chat starten
                if proc:
                    self.active_recordings[channel_id] = proc
                    
                    # Chat-Recording Logik
                    if self.config.platform(platform.platform_name).get("chat", True):
                        self._start_chat_recorder(platform.platform_name, channel, details)

    def _start_chat_recorder(self, platform_name, channel, details):
        """Wählt den passenden Chat-Recorder basierend auf der Plattform."""
        target_func = None
        args = ()

        try:
            if platform_name == "kick":
                from utils.kick_chat import record_kick_chat
                target_func = record_kick_chat
                args = (channel, details['chat_json'])
            
            elif platform_name == "twitch":
                from utils.twitch_chat import record_twitch_chat
                target_func = record_twitch_chat
                args = (channel, details['chat_json'])
            
            elif platform_name == "youtube":
                from utils.youtube_chat import record_youtube_chat
                target_func = record_youtube_chat
                args = (details['url'], details['chat_json'])

            if target_func:
                t = threading.Thread(target=target_func, args=args, daemon=True)
                t.start()
                logging.info(f"[CHAT] {platform_name.upper()}-Recorder für {channel} gestartet.")
        except ImportError as e:
            logging.error(f"[CHAT] Fehler beim Import des Recorders für {platform_name}: {e}")
        except Exception as e:
            logging.error(f"[CHAT] Unerwarteter Fehler beim Chat-Start: {e}")

    def _check_finished_processes(self):
        """Prüft, ob die 5-Minuten-Gnadenfrist für beendete Streams abgelaufen ist."""
        now = time.time()
        grace_period = 300 # 5 Minuten
        finished_channels = []

        for channel_id, start_time in list(self.waiting_for_reconnect.items()):
            if now - start_time > grace_period:
                logging.info(f"Cleanup: {channel_id} final beendet. Post-Processing beginnt.")
                details = self.recording_details.get(channel_id)
                
                if details:
                    # Job an den Post-Processor (FFmpeg Chat Render) übergeben
                    self.post_processor.add_job(
                        details['video'], 
                        details['chat_json'], 
                        details['folder']
                    )
                
                self.recording_details.pop(channel_id, None)
                finished_channels.append(channel_id)

        for cid in finished_channels:
            self.waiting_for_reconnect.pop(cid, None)