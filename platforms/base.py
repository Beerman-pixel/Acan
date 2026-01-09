from abc import ABC, abstractmethod
import logging

class PlatformBase:
    def __init__(self, config, channel=None): # channel=None macht es optional
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