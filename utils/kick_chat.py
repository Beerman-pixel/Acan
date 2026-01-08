import websocket
import json
import logging
import requests
from pathlib import Path

def record_kick_chat(channel_name, output_dir):
    output_file = Path(output_dir) / f"chat_{channel_name}.jsonl"
    
    # 1. Interne Chatroom-ID von Kick holen
    try:
        # Wir fragen die API nach dem Channel
        response = requests.get(f"https://kick.com/api/v1/channels/{channel_name}")
        data = response.json()
        # Das ist die magische Nummer, die wir zum Abonnieren brauchen
        chatroom_id = data['chatroom']['id']
        logging.info(f"[CHAT] ID für {channel_name} gefunden: {chatroom_id}")
    except Exception as e:
        logging.error(f"[CHAT] Konnte Chatroom-ID für {channel_name} nicht holen: {e}")
        return

    # 2. Verbindung mit dem Standard-Pusher-Endpoint
    socket_url = "wss://ws-us2.pusher.com/app/eb1d35122262d40994?protocol=7&client=js&version=7.6.0&flash=false"

    def on_open(ws):
        # WICHTIG: Wir nutzen jetzt die chatroom_id statt des Namens
        subscribe_data = {
            "event": "pusher:subscribe",
            "data": {"auth": "", "channel": f"chatrooms.{chatroom_id}.v2"}
        }
        ws.send(json.dumps(subscribe_data))
        logging.info(f"[CHAT] Abonnement für ID {chatroom_id} gesendet.")

    def on_message(ws, message):
        if "ChatMessageEvent" in message:
            with open(output_file, "a", encoding="utf-8") as f:
                f.write(message + "\n")

    def on_error(ws, error):
        logging.error(f"[CHAT] WebSocket Fehler: {error}")

    ws = websocket.WebSocketApp(
        socket_url,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error
    )
    ws.run_forever()