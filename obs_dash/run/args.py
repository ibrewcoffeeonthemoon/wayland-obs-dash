from dataclasses import dataclass


@dataclass
class Args:
    host: str
    port: int
    show_video: bool
    video_width: int
    video_height: int
    video_sampling_interval: float
    show_audio: bool
