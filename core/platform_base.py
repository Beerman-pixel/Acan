class StreamingPlatformBase:
    platform_name = ""

    def __init__(self, config, channel):
        self.config = config
        self.channel = channel
        self.output = (
            config.output_dir(self.platform_name) / channel
        )

    def record_live(self):
        cmd = [
            "streamlink",
            f"{self.base_url}/{self.channel}",
            self.config.quality(self.platform_name),
            "-o", f"{self.output}/live.mp4"
        ]
