import json
import logging
import re
from pathlib import Path
from chat_downloader import ChatDownloader

def record_youtube_chat(channel_url, output_dir):
    # Sauberer Name: Extrahiere @Name aus der URL
    clean_name = channel_url.split('@')[-1].split('/')[0]
    
    # WICHTIG: Den Pfad neu zusammenbauen, damit keine URL-Sonderzeichen drin sind
    # Wir nehmen den übergeordneten 'youtube' Ordner und hängen den sauberen Namen an
    final_dir = Path(output_dir).parent / clean_name
    final_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = final_dir / f"chat_yt_{clean_name}.jsonl"
    
    logging.info(f"[YT-CHAT] Starte Chat-Aufzeichnung für {clean_name}...")
    
    url = channel_url.rstrip("/") + "/live"

    try:
        downloader = ChatDownloader()
        chat = downloader.get_chat(url)

        with open(output_file, "a", encoding="utf-8") as f:
            for message in chat:
                f.write(json.dumps(message) + "\n")
                # Live-Anzeige im Terminal (optional)
                author = message.get('author', {}).get('name', 'Anonym')
                text = message.get('message', '')
                logging.info(f"[YT-CHAT] {author}: {text}")

    except Exception as e:
        logging.error(f"[YT-CHAT] Fehler bei {clean_name}: {e}")
