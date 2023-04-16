from enum import Enum


class RenderJobState(Enum):
    WAITING = 1
    EXTRACTING = 2
    RENDERING = 3
    FINISHED = 4
    FAILED = 5
    ENHANCING = 6
    BLURRING = 7
    RESIZING = 8