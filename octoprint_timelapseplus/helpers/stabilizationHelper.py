from ..constants import Constants


class StabilizationHelper:

    def __init__(self, settings, stabilizationSettings):
        self.SNAPSHOT_COMMAND = settings.get(["snapshotCommand"])
        self.STAB = stabilizationSettings

    def getRetractionCommands(self, positionTracker, inverse):
        shouldDoRetract = self.STAB.RETRACT_AMOUNT > 0 or self.STAB.RETRACT_Z_HOP > 0
        if not shouldDoRetract:
            return []

        cmd = []

        if not positionTracker.RELATIVE_MODE:
            cmd.append('G91')
        if not positionTracker.RELATIVE_MODE_EXTRUDER:
            cmd.append('M83')

        if inverse:
            cmd.append('G1 E' + str(self.STAB.RETRACT_AMOUNT) + ' Z-' + str(self.STAB.RETRACT_Z_HOP) + ' F' + str(self.STAB.getFeedrateRetraction()))
        else:
            cmd.append('G1 E-' + str(self.STAB.RETRACT_AMOUNT) + ' Z' + str(self.STAB.RETRACT_Z_HOP) + ' F' + str(self.STAB.getFeedrateRetraction()))

        if not positionTracker.RELATIVE_MODE:
            cmd.append('G90')
        if not positionTracker.RELATIVE_MODE_EXTRUDER:
            cmd.append('M82')

        return cmd

    def getMoveCommands(self, positionTracker, x, y, z, f):
        cmd = []

        if positionTracker.RELATIVE_MODE:
            cmd.append('G90')

        cmd.append('G0 X' + str(x) + ' Y' + str(y) + ' Z' + str(z) + ' F' + str(f))

        if positionTracker.RELATIVE_MODE:
            cmd.append('G91')

        return cmd

    def stabilizeAndQueueSnapshotRaw(self, printer, positionTracker):
        if printer.set_job_on_hold(True):

            newZPos = self.STAB.PARK_Z
            if self.STAB.PARK_Z_RELATIVE:
                newZPos = positionTracker.POS_Z + self.STAB.PARK_Z

            cmd = []
            try:
                cmd += self.getRetractionCommands(positionTracker, False)
                cmd += self.getMoveCommands(positionTracker, self.STAB.PARK_X, self.STAB.PARK_Y, newZPos, self.STAB.getFeedrateMove())

                if self.STAB.WAIT_FOR_MOVEMENT:
                    cmd.append('M400')

                if self.STAB.WAIT_BEFORE > 0:
                    cmd.append('G4 P' + str(self.STAB.WAIT_BEFORE))

                cmd.append('@' + self.SNAPSHOT_COMMAND + '-' + Constants.SUFFIX_PRINT_UNSTABLE)

                if self.STAB.WAIT_AFTER > 0:
                    cmd.append('G4 P' + str(self.STAB.WAIT_AFTER))

                cmd += self.getMoveCommands(positionTracker, positionTracker.POS_X, positionTracker.POS_Y, positionTracker.POS_Z, self.STAB.getFeedrateMove())
                cmd += self.getRetractionCommands(positionTracker, True)

                printer.commands(cmd, force=True, tags={Constants.GCODE_TAG_STABILIZATION})
            finally:
                printer.set_job_on_hold(False)
