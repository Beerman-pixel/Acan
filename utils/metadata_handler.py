import subprocess
import json
import logging
from pathlib import Path

def setup_ganymede_folder(platform, channel_name, stream_title, timestamp):
    """Erstellt den isolierten Ordner für den Stream."""
    folder_name = f"{timestamp}_{stream_title}"
    # Bereinige Ordnername von Sonderzeichen
    folder_name = "".join([c for c in folder_name if c.isalnum() or c in (' ', '_', '-')]).rstrip()
    folder_name = folder_name.replace(" ", "_")
    
    base_path = Path(f"Downloads/{platform}/{channel_name}/{folder_name}")
    base_path.mkdir(parents=True, exist_ok=True)
    return base_path

def save_stream_metadata(url, folder_path):
    """Speichert Thumbnail und stream-info.json via yt-dlp."""
    logging.info(f"[METADATA] Erfasse Stream-Infos in {folder_path}")
    
    cmd = [
        "yt-dlp",
        "--skip-download",
        "--write-info-json",
        "--write-thumbnail",
        "--convert-thumbnails", "jpg",
        "-o", f"{folder_path}/stream",
        url
    ]
    
    try:
        subprocess.run(cmd, check=False, capture_output=True)
        # Umbenennen der info.json zu Ganymede-Standard (optional)
        info_file = folder_path / "stream.info.json"
        if info_file.exists():
            info_file.rename(folder_path / "stream-info.json")
    except Exception as e:
        logging.error(f"[METADATA] Fehler beim Speichern: {e}")
