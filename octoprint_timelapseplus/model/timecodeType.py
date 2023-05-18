from enum import Enum


class TimecodeType(Enum):
    PRINTTIME_HMS = 1
    PRINTTIME_HM = 2
    PRINTTIME_HMS_LETTERS = 3
    PRINTTIME_HM_LETTERS = 4
    TIME_HMS_12 = 5
    TIME_HMS_24 = 6
    TIME_HM_12 = 7
    TIME_HM_24 = 8
    PERCENT = 9,
    BAR = 10,
    CLOCK = 11,
    CLOCK_NOSECONDS = 12
