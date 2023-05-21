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
    COMBINING = 9
    CREATE_PALETTE = 10
    ENCODING = 11
    ADDING_TIMECODES = 12
    GENERATING_PPROLL = 13
    APPLYING_FADE = 14
