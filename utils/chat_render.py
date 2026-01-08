import subprocess
import logging
from pathlib import Path

def render_chat_to_video(video_path, jsonl_path):
    """
    Erzeugt ein Video des Chats, das über das Hauptvideo gelegt werden kann.
    """
    output_video = video_path.parent / f"{video_path.stem}_chat.mp4"
    
    logging.info(f"[RENDER] Starte Chat-Rendering für {video_path.name}...")
    
    # Beispiel-Befehl für einen Renderer
    # Hinweis: Die genauen Parameter hängen vom gewählten Tool ab
    cmd = [
        "twitch-chat-render",
        "-i", str(jsonl_path),
        "-o", str(output_video),
        "--width", "400",
        "--height", "1080",
        "--font-size", "18",
        "--theme", "dark"
    ]
    
    try:
        subprocess.run(cmd, check=True)
        logging.info(f"[RENDER] Chat-Video erstellt: {output_video}")
    except Exception as e:
        logging.error(f"[RENDER] Fehler beim Chat-Rendering: {e}")
