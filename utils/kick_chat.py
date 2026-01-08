import json
import logging
from pathlib import Path
import websocket # Benötigt: pip install websocket-client

def record_kick_chat(channel_name, output_dir):
    """
    Minimalistischer Kick Chat Listener über Pusher.
    Speichert Nachrichten als JSONL (JSON Lines).
    """
    output_file = Path(output_dir) / f"chat_{channel_name}.jsonl"
    
    # Kick nutzt Pusher (ws-us2 Region)
    # Die App-ID für Kick ist eb1d35122262d40994
    socket_url = "wss://ws-us2.pusher.com/app/eb1d35122262d40994?protocol=7&client=js&version=7.6.0&flash=false"

    def on_open(ws):
        logging.info(f"Chat-Verbindung für {channel_name} wird hergestellt...")
        # Wir müssen dem Channel beitreten (Pusher Event)
        # Hinweis: Bei Kick ist der Chat-Channel oft 'chatrooms.<ID>.v2'
        # Für einen einfachen Test nutzen wir den Namen:
        subscribe_data = {
            "event": "pusher:subscribe",
            "data": {"auth": "", "channel": f"chatrooms.{channel_name}.v2"}
        }
        ws.send(json.dumps(subscribe_data))

    def on_message(ws, message):
        msg_data = json.loads(message)
        # Nur echte Chat-Nachrichten speichern
        if msg_data.get("event") == "App\\Events\\ChatMessageEvent":
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(message + "\n")

    ws = websocket.WebSocketApp(socket_url, on_open=on_open, on_message=on_message)
    ws.run_forever()
