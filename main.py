import logging
import sys
from core.config import Config
from core.manager import PlatformManager

def main():
    # Logging hier EINMAL definieren
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

    logging.info("Acan Initialisierung...")

    try:
        config = Config()
        manager = PlatformManager(config)
        manager.run()
    except KeyboardInterrupt:
        logging.info("\nProgramm beendet durch Benutzer.")
        sys.exit(0)
    except Exception as e:
        logging.critical(f"Kritischer Systemfehler: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()