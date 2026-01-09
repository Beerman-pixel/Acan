import websocket
import json
import logging
import time

def record_kick_chat(channel_name, output_path):
    """
    Verbindet sich mit dem Kick-Pusher-System und speichert Chat-Events.
    Nutzt den US2-Cluster, um 'App Key not in cluster' Fehler zu vermeiden.
    """
    
    def on_message(ws, message):
        try:
            data = json.loads(message)
            
            # Pusher schickt Daten oft als String-kodiertes JSON innerhalb eines JSON
            if data.get('event') == 'App\\Events\\ChatMessageEvent':
                msg_data = json.loads(data['data'])
                
                # Wir bauen ein sauberes Format für unseren Post-Processor
                entry = {
                    "author": msg_data['sender']['username'],
                    "message": msg_data['content'],
                    "timestamp": time.time(), # Lokaler Zeitstempel für FFmpeg-Sync
                    "kick_timestamp": msg_data['created_at'],
                    "color": msg_data['sender'].get('identity', {}).get('color', '#FFFFFF')
                }
                
                with open(output_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry) + "\n")
                    f.flush() # Sofort schreiben, damit bei Absturz nichts verloren geht
                    
        except Exception as e:
            # Pings (pusher:pong) oder andere Events müssen nicht geloggt werden
            pass

    def on_open(ws):
        logging.info(f"[CHAT] Kick-Verbindung für {channel_name} wird authentifiziert...")
        
        # Abonniere den Chatroom-Kanal (v2 ist der aktuelle Standard)
        subscribe_msg = {
            "event": "pusher:subscribe",
            "data": {"channel": f"chatrooms