from app.core.config import Config
from app.core.manager import PlatformManager

def main():
    config = Config("config.yaml")
    manager = PlatformManager(config)
    manager.run()

if __name__ == "__main__":
    main()
