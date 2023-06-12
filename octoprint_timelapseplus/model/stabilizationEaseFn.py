from enum import Enum


class StabilizationEaseFn(Enum):
    LINEAR = 1
    INOUT = 2
    BOUNCE = 3
    RANDOM = 4
    CYCLIC_SINE = 5
