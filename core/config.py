import yaml
import os
from pathlib import Path

class Config:
    def __init__(self, path="config.yaml"):
        self.path = Path(path)
        self.data = self._load()

    def _load(self):
        with open(self.path, "r") as f:
            content = yaml.safe_load(f)
            return content if content else {}

    def _resolve_path(self, path_str: str) -> Path:
        if not path_str:
            return Path("./downloads")
        # .expanduser() ersetzt das "~", .replace() ersetzt dein "$home"
        p = str(path_str).replace("$home", str(Path.home())).replace("$HOME", str(Path.home()))
        return Path(p).expanduser().resolve()

    @property
    def check_interval(self):
        return self.data.get("check_interval", 60)

    def platform(self, name: str) -> dict:
        # Da youtube/kick/twitch direkt auf oberster Ebene stehen:
        return self.data.get(name, {})

    def platform_enabled(self, name: str) -> bool:
        return self.platform(name).get("enabled", False)

    def channels(self, name: str) -> list:
        return self.platform(name).get("channels", [])

    def output_dir(self, name: str) -> Path:
        # Sucht output_dir in der Plattform, sonst in defaults, sonst ./downloads
        raw_path = self.platform(name).get(
            "output_dir", 
            self.data.get("defaults", {}).get("output_dir", "./downloads")
        )
        resolved = self._resolve_path(raw_path)
        resolved.mkdir(parents=True, exist_ok=True)
        return resolved

    def quality(self, name: str) -> str:
        return self.platform(name).get("quality", "best")