import json
import logging
from pathlib import Path
from chat_downloader import ChatDownloader
from chat_downloader.exceptions import ChatDisabled, URLNotSupported, LoginRequired

def record_youtube_chat(channel_url, output_dir):
    # 1. Pfad-Fix (wie zuvor besprochen)
    clean_name = channel_url.split('@')[-1].split('/')[0]
    final_dir = Path(output_dir).parent / clean_name
    final_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = final_dir / f"chat_yt_{clean_name}.jsonl"
    
    url = channel_url.rstrip("/") + "/live"

    try:
        downloader = ChatDownloader()
        
        # Versuche den Chat zu initialisieren
        logging.info(f"[YT-CHAT] Prüfe Chat-Verfügbarkeit für {clean_name}...")
        chat = downloader.get_chat(url)

        with open(output_file, "a", encoding="utf-8") as f:
            for message in chat:
                f.write(json.dumps(message) + "\n")
                
                # Nur zur Info im Terminal
                author = message.get('author', {}).get('name', 'Anonym')
                text = message.get('message', '')
                logging.info(f"[YT-CHAT] {author}: {text}")

    except ChatDisabled:
        logging.warning(f"[YT-CHAT] Chat ist für den Stream von {clean_name} deaktiviert. Thread wird beendet.")
    except LoginRequired:
        logging.warning(f"[YT-CHAT] Chat für {clean_name} erfordert Login (Altersbeschränkung o.ä.). Überspringe...")
    except Exception as e:
        # Falls es ein anderer Fehler ist (z.B. Stream noch nicht gestartet)
        if "No chat groups found" in str(e):
            logging.info(f"[YT-CHAT] Aktuell kein aktiver Chat für {clean_name} gefunden.")
        else:
            logging.error(f"[YT-CHAT] Unerwarteter Fehler bei {clean_name}: {e}")