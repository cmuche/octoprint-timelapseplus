import math

from .stabilizationEaseCalculator import StabilizationEaseCalculator
from ..log import Log
from ..constants import Constants
from ..model.stabilizationParkType import StabilizationParkType


class StabilizationHelper:

    def __init__(self, settings, stabilizationSettings):
        self.SNAPSHOT_COMMAND = settings.get(["snapshotCommand"])
        self.STAB = stabilizationSettings

    def floatVal(self, val):
        roundedNumber = round(float(val), 3)
        numberString = format(roundedNumber, ".3f")
        numberString = numberString.replace(',', '.')

        valInt, valDec = numberString.split('.')

        valDec = valDec.rstrip('0')
        if valDec == '':
            numberString = valInt
        else:
            numberString = valInt + '.' + valDec
        return numberString

    def calculateDistance(self, x1, y1, z1, x2, y2, z2):
        distance = math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2 + (z2 - z1) ** 2)
        return distance

    def calculateOozingCompensationAmount(self, positionTracker, x, y, z):
        distance = self.calculateDistance(positionTracker.POS_X, positionTracker.POS_Y, positionTracker.POS_Z, x, y, z)
        seconds = distance / self.STAB.MOVE_SPEED
        seconds *= 2
        seconds += self.STAB.WAIT_BEFORE / 1000
        seconds += self.STAB.WAIT_AFTER / 1000

        amount = seconds * self.STAB.OOZING_COMPENSATION_VALUE
        return amount

    def shouldDoRetract(self):
        return self.STAB.RETRACT_AMOUNT > 0 or self.STAB.RETRACT_Z_HOP > 0

    def getRetractionCommands(self, positionTracker, inverse, oozeOffset=0):
        if not self.shouldDoRetract():
            return []

        cmd = []
        cmd += self.getCommandsPositionRelative(positionTracker.RELATIVE_MODE, positionTracker.RELATIVE_MODE_EXTRUDER, True, True)

        if inverse:
            cmd.append('G1 E' + self.floatVal(self.STAB.RETRACT_AMOUNT) + ' F' + self.floatVal(self.STAB.getFeedrateRetraction()))
            cmd.append('G1 Z-' + self.floatVal(self.STAB.RETRACT_Z_HOP) + ' F' + self.floatVal(self.STAB.getFeedrateMove()))
        else:
            amount = self.STAB.RETRACT_AMOUNT + oozeOffset
            cmd.append('G1 Z' + self.floatVal(self.STAB.RETRACT_Z_HOP) + ' F' + self.floatVal(self.STAB.getFeedrateMove()))
            cmd.append('G1 E-' + self.floatVal(round(amount, 3)) + ' F' + self.floatVal(self.STAB.getFeedrateRetraction()))

        cmd += self.getCommandsPositionRelative(True, True, positionTracker.RELATIVE_MODE, positionTracker.RELATIVE_MODE_EXTRUDER)

        return cmd

    def getCommandsPositionRelative(self, fromValMove, fromValExt, toValMove, toValExt):
        cmd = []

        if toValMove != fromValMove:
            if toValMove:
                cmd.append('G91')
                if Constants.GCODE_G90_G91_EXTRUDER_OVERWRITE:
                    fromValExt = True
            else:
                cmd.append('G90')
                fromValExt = False

        if toValExt != fromValExt:
            if toValExt:
                cmd.append('M83')
                isRelE = True
            else:
                cmd.append('M82')
                isRelE = False

        return cmd

    def getMoveCommands(self, positionTracker, x, y, z, f):
        cmd = []

        cmd += self.getCommandsPositionRelative(positionTracker.RELATIVE_MODE, positionTracker.RELATIVE_MODE_EXTRUDER, False, positionTracker.RELATIVE_MODE_EXTRUDER)
        cmd.append('G0 X' + self.floatVal(x) + ' Y' + self.floatVal(y) + ' Z' + self.floatVal(z) + ' F' + self.floatVal(f))
        self.getCommandsPositionRelative(False, positionTracker.RELATIVE_MODE_EXTRUDER, positionTracker.RELATIVE_MODE, positionTracker.RELATIVE_MODE_EXTRUDER)

        return cmd

    def getXYParkPos(self, positionTracker, currentSnapshotProgress):
        posX = 0
        posY = 0

        if self.STAB.PARK_X_TYPE == StabilizationParkType.FIXED:
            posX = self.STAB.PARK_X
        elif self.STAB.PARK_X_TYPE == StabilizationParkType.RELATIVE:
            posX = positionTracker.POS_X + self.STAB.PARK_X
        elif self.STAB.PARK_X_TYPE == StabilizationParkType.SWEEP:
            rX = StabilizationEaseCalculator.applyEaseFn(currentSnapshotProgress, self.STAB.PARK_X_SWEEP_FN, self.STAB.PARK_X_SWEEP_CYCLES)
            sweepXDelta = self.STAB.PARK_X_SWEEP_TO - self.STAB.PARK_X_SWEEP_FROM
            posX = self.STAB.PARK_X_SWEEP_FROM + rX * sweepXDelta

        if self.STAB.PARK_Y_TYPE == StabilizationParkType.FIXED:
            posY = self.STAB.PARK_Y
        elif self.STAB.PARK_Y_TYPE == StabilizationParkType.RELATIVE:
            posY = positionTracker.POS_Y + self.STAB.PARK_Y
        elif self.STAB.PARK_Y_TYPE == StabilizationParkType.SWEEP:
            rY = StabilizationEaseCalculator.applyEaseFn(currentSnapshotProgress, self.STAB.PARK_Y_SWEEP_FN, self.STAB.PARK_Y_SWEEP_CYCLES)
            sweepYDelta = self.STAB.PARK_Y_SWEEP_TO - self.STAB.PARK_Y_SWEEP_FROM
            posY = self.STAB.PARK_Y_SWEEP_FROM + rY * sweepYDelta

        return posX, posY

    def validateParkingPosition(self, x, y, z):
        if x < self.STAB.PRINTER_X_MIN or x > self.STAB.PRINTER_X_MAX or \
                y < self.STAB.PRINTER_Y_MIN or y > self.STAB.PRINTER_Y_MAX or \
                z > self.STAB.PRINTER_Z_MAX:
            raise Exception('The Parking Position ' + '({:.2f},{:.2f},{:.2f})'.format(x, y, z) + ' is out of Limits!')

    def stabilizeAndQueueSnapshotRawCommands(self, positionTracker, currentSnapshotProgress):
        cmd = []

        newXPos, newYPos = self.getXYParkPos(positionTracker, currentSnapshotProgress)

        newZPos = self.STAB.PARK_Z
        if self.STAB.PARK_Z_RELATIVE:
            newZPos = positionTracker.POS_Z + self.STAB.PARK_Z

            if self.shouldDoRetract():
                newZPos += self.STAB.RETRACT_Z_HOP

        Log.debug('Parking Position calculated', {'x': newXPos, 'y': newYPos, 'z': newZPos})
        self.validateParkingPosition(newXPos, newYPos, newZPos)

        oozeOffset = 0
        if self.STAB.OOZING_COMPENSATION:
            oozeOffset = self.calculateOozingCompensationAmount(positionTracker, newXPos, newYPos, newZPos)

        cmd += self.getRetractionCommands(positionTracker, False, oozeOffset)
        cmd += self.getMoveCommands(positionTracker, newXPos, newYPos, newZPos, self.STAB.getFeedrateMove())

        if self.STAB.WAIT_FOR_MOVEMENT:
            cmd.append('M400')

        if self.STAB.WAIT_BEFORE > 0:
            cmd.append('G4 P' + str(self.STAB.WAIT_BEFORE))

        cmd.append('@' + self.SNAPSHOT_COMMAND + '-' + Constants.SUFFIX_PRINT_UNSTABLE)

        if self.STAB.WAIT_AFTER > 0:
            cmd.append('G4 P' + str(self.STAB.WAIT_AFTER))

        returnZPos = positionTracker.POS_Z
        if self.shouldDoRetract():
            returnZPos += self.STAB.RETRACT_Z_HOP

        cmd += self.getMoveCommands(positionTracker, positionTracker.POS_X, positionTracker.POS_Y, returnZPos, self.STAB.getFeedrateMove())
        cmd += self.getRetractionCommands(positionTracker, True)

        cmd.append('G0 F' + self.floatVal(positionTracker.FEEDRATE))

        return dict(cmd=cmd, parkPos=((newXPos, newYPos, newZPos)))

    def stabilizeAndQueueSnapshotRaw(self, printer, positionTracker, currentSnapshotProgress):
        if printer.set_job_on_hold(True):
            try:
                Log.debug('Generating Stabilization Commands', {'snapshotProgress': currentSnapshotProgress})

                cmdAndPos = self.stabilizeAndQueueSnapshotRawCommands(positionTracker, currentSnapshotProgress)
                cmd = cmdAndPos['cmd']

                Log.debug('Executing Stabilization Commands', cmd)
                printer.commands(cmd, force=True, tags={Constants.GCODE_TAG_STABILIZATION})
                # TODO Update PositionTracker with the created Commands

                return cmdAndPos['parkPos']
            finally:
                printer.set_job_on_hold(False)
