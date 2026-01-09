import os
import subprocess
import logging
from pathlib import Path

def setup_ganymede_folder(config_output_path, platform, channel_name, stream_title, timestamp):
    """Erstellt: [config_output_path] / [channel_name] / [timestamp_title]"""
    # Verhindert Dopplungen, falls der User ~/Downloads/kick in der Config hat
    root_path = Path(os.path.expanduser(config_output_path)).resolve()
    
    clean_title = "".join([c for c in stream_title if c.isalnum() or c in (' ', '_', '-')]).strip()
    clean_title = clean_title.replace(" ", "_")[:50]
    
    folder_name = f"{timestamp}_{clean_title}"
    
    # Hier lag der Fehler: platform wurde zusätzlich eingefügt
    # Wenn dein Pfad in der Config schon ".../kick" ist, lassen wir platform weg:
    target_dir = root_path / channel_name / folder_name
    
    target_dir.mkdir(parents=True, exist_ok=True)
    return target_dir, folder_name

def save_stream_metadata(url, folder_path, base_name):
    """Speichert Thumbnail und Info-JSON mit dem einheitlichen base_name."""
    logging.info(f"[METADATA] Lade Infos für {base_name}...")
    
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-info-json",
        "--write-thumbnail",
        "--convert-thumbnails", "jpg",
        "-o", f"{folder_path}/{base_name}",
        url
    ]
    
    try:
        subprocess.run(cmd, check=False, capture_output=True)
        # yt-dlp benennt thumbnails oft base_name.jpg oder base_name.webp
        # Wir korrigieren das ggf. auf base_name-Thumbnail.jpg falls gewünscht,
        # aber base_name.jpg ist für Ganymede/Plex meist am besten.
        logging.info(f"[METADATA] Erfolg für {base_name}")
    except Exception as e:
        logging.error(f"[METADATA] Fehler: {e}")