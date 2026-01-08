import yaml
from pathlib import Path

class Config:
    def __init__(self, path="config.yaml"):
        self.path = Path(path)
        self.data = self._load()

    def _load(self):
        with open(self.path, "r") as f:
            return yaml.safe_load(f)

    # -------- Global --------

    @property
    def defaults(self):
        return self.data.get("defaults", {})

    @property
    def check_interval(self):
        return self.data.get("check_interval", 60)

    # -------- Platform helpers --------

    def platform(self, name: str) -> dict:
        return self.data.get(name, {})

    def platform_enabled(self, name: str) -> bool:
        return self.platform(name).get("enabled", False)

    def channels(self, name: str) -> list:
        return self.platform(name).get("channels", [])

    def output_dir(self, name: str) -> Path:
        return Path(
            self.platform(name).get(
                "output_dir",
                self.defaults.get("output_dir", "./downloads")
            )
        )

    def quality(self, name: str) -> str:
        return self.platform(name).get(
            "quality",
            self.defaults.get("quality", "best")
        )
