from enum import Enum


class StabilizationEaseFn(Enum):
    LINEAR = 1
    INOUT = 2
    BOUNCE = 3
    RANDOM = 4
    CYCLIC_SINE = 5
    CYCLIC_SINE_REDUCING = 6
    CYCLIC_LINEAR = 7
    CYCLIC_LINEAR_REDUCING = 8
    CYCLIC_SAWTOOTH = 9
