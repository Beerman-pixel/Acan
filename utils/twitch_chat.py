# In utils/twitch_chat.py
from chat_downloader import ChatDownloader

def record_twitch_chat(channel_url, output_dir):
    # ... (Name und Pfad Logik wie gehabt)
    if "twitch.tv" not in channel_url:
        channel_url = f"https://www.twitch.tv/{channel_url}"

    try:
        downloader = ChatDownloader()
        chat = downloader.get_chat(channel_url)
        # ... Rest des Codes
    except Exception as e:
        if "disabled" in str(e).lower():
            logging.warning(f"[TW-CHAT] Chat deaktiviert für {channel_url}")
        else:
            logging.error(f"[TW-CHAT] Fehler: {e}")