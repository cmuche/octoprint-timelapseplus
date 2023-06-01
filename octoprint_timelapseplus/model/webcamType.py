from enum import Enum


class WebcamType(Enum):
    IMAGE_JPEG = 1
    STREAM_MJPEG = 2
    STREAM_MP4 = 3
    STREAM_HLS = 4
    SCRIPT = 5
    PLUGIN = 6
