import logging
from core.config import Config
from core.manager import PlatformManager
from platforms.kick import KickPlatform
from platforms.twitch import TwitchPlatform
from platforms.youtube import YouTubePlatform

def main():
    logging.basicConfig(
        level=logging.INFO, 
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logging.info("Acan Initialisierung...")

    try:
        config = Config("config.yaml")
        
        # Plattformen initialisieren
        # Wir übergeben jeder Plattform die config
        platforms = [
            KickPlatform(config),
            TwitchPlatform(config),
            YouTubePlatform(config)
        ]

        # WICHTIG: Hier fehlte das 'platforms' Argument!
        manager = PlatformManager(config, platforms)
        manager.run()

    except Exception as e:
        logging.critical(f"Kritischer Systemfehler: {e}", exc_info=True)

if __name__ == "__main__":
    main()