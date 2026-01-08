import subprocess
import logging
import os

def generate_ganymede_style_chat(video_path, json_path):
    """
    Erzeugt ein separates Chat-Video (stream-Chat.mp4) wie bei Ganymede.
    """
    output_chat_video = video_path.parent / f"{video_path.stem}-Chat.mp4"
    
    logging.info(f"[RENDER] Starte Ganymede-Style Rendering für {video_path.name}")

    # Beispielbefehl für einen Java- oder Node-basierten Renderer
    # Erfordert: twitch-chat-render (oder ähnliches Tool)
    cmd = [
        "tcr", 
        "-i", str(json_path),
        "-o", str(output_chat_video),
        "--width", "350",
        "--height", "1080",
        "--font", "Inter",
        "--font-size", "14",
        "--badge-distance", "4"
    ]

    try:
        # Dieser Prozess kann je nach CPU lange dauern
        subprocess.run(cmd, check=True)
        logging.info(f"[SUCCESS] Chat-Video erstellt: {output_chat_video}")
    except Exception as e:
        logging.error(f"[ERROR] Chat-Rendering fehlgeschlagen: {e}")
