from abc import ABC, abstractmethod
import logging

class PlatformBase(ABC):
    def __init__(self, config, channel):
        self.config = config
        self.channel = channel

    def record_live(self):
        """Optional: Kann von Subklassen überschrieben werden."""
        logging.debug(f"Live-Recording für {self.channel} nicht implementiert.")
        pass

    def download(self):
        """Optional: Kann von Subklassen überschrieben werden."""
        logging.debug(f"VOD/Clip-Download für {self.channel} nicht implementiert.")
        pass