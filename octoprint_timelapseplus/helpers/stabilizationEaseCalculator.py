import math
import random

from ..model.stabilizationEaseFn import StabilizationEaseFn


class StabilizationEaseCalculator:
    @staticmethod
    def applyEaseFn(t, fn, cycles):
        val = 0
        if fn == StabilizationEaseFn.LINEAR:
            val = t
        if fn == StabilizationEaseFn.RANDOM:
            val = random.random()
        if fn == StabilizationEaseFn.INOUT:
            val = StabilizationEaseCalculator.easeFnInOut(t)
        if fn == StabilizationEaseFn.BOUNCE:
            val = StabilizationEaseCalculator.easeFnBounce(t)
        if fn == StabilizationEaseFn.CYCLIC_SINE:
            val = StabilizationEaseCalculator.easeFnCyclicSine(t, cycles)
        if fn == StabilizationEaseFn.CYCLIC_SINE_REDUCING:
            val = StabilizationEaseCalculator.easeFnCyclicSine(t, cycles)
            val = StabilizationEaseCalculator.reduceCyclicFn(t, val)
        if fn == StabilizationEaseFn.CYCLIC_LINEAR:
            val = StabilizationEaseCalculator.easeFnCyclicLinear(t, cycles)
        if fn == StabilizationEaseFn.CYCLIC_LINEAR_REDUCING:
            val = StabilizationEaseCalculator.easeFnCyclicLinear(t, cycles)
            val = StabilizationEaseCalculator.reduceCyclicFn(t, val)
        if fn == StabilizationEaseFn.CYCLIC_SAWTOOTH:
            val = StabilizationEaseCalculator.easeFnCyclicSawtooth(t, cycles)

        if val < 0:
            return 0
        if val > 1:
            return 1

        return val

    @staticmethod
    def easeFnBounce(t):
        if t < (1 / 2.75):
            return 7.5625 * t * t
        elif t < (2 / 2.75):
            t -= (1.5 / 2.75)
            return 7.5625 * t * t + 0.75
        elif t < (2.5 / 2.75):
            t -= (2.25 / 2.75)
            return 7.5625 * t * t + 0.9375
        else:
            t -= (2.625 / 2.75)
            return 7.5625 * t * t + 0.984375

    @staticmethod
    def easeFnInOut(t):
        return -(math.cos(math.pi * t) - 1) / 2

    @staticmethod
    def reduceCyclicFn(t, val):
        val -= 0.5
        val *= (1 - t)
        val += 0.5
        return val

    @staticmethod
    def easeFnCyclicSine(t, cycles):
        return 1 - (math.cos(t * 2 * math.pi * cycles) + 1) / 2

    @staticmethod
    def easeFnCyclicLinear(t, cycles):
        period = 1.0 / cycles
        normT = t % period
        tVal = 1 - 4 * abs(normT - 0.5 * period) / period
        return tVal / 2 + 0.5

    @staticmethod
    def easeFnCyclicSawtooth(t, cycles):
        periodLength = 1 / cycles
        period = math.floor(t / periodLength)
        tN = t - period * periodLength
        return tN * cycles
