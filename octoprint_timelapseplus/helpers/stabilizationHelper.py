from ..constants import Constants


class StabilizationHelper:

    def __init__(self, settings, stabilizationSettings):
        self.SNAPSHOT_COMMAND = settings.get(["snapshotCommand"])
        self.STAB = stabilizationSettings

    def stabilizeAndQueueSnapshotRaw(self, printer, positionTracker):
        if printer.set_job_on_hold(True):

            shouldDoRetract = self.STAB.RETRACT_AMOUNT > 0 or self.STAB.RETRACT_Z_HOP > 0
            newZPos = self.STAB.PARK_Z
            if self.STAB.PARK_Z_RELATIVE:
                newZPos = positionTracker.POS_Z + self.STAB.PARK_Z

            cmd = []
            try:
                if shouldDoRetract:
                    cmd.append('G1 E-' + str(self.STAB.RETRACT_AMOUNT) + ' Z' + str(self.STAB.RETRACT_Z_HOP) + ' F' + str(self.STAB.RETRACT_SPEED * 60))

                cmd.append('G0 X' + str(self.STAB.PARK_X) + ' Y' + str(self.STAB.PARK_Y) + ' Z' + str(newZPos) + ' F' + str(self.STAB.MOVE_SPEED * 60))

                if self.STAB.WAIT_FOR_MOVEMENT:
                    cmd.append('M400')

                if self.STAB.WAIT_BEFORE > 0:
                    cmd.append('G4 P' + str(self.STAB.WAIT_BEFORE))

                cmd.append('@' + self.SNAPSHOT_COMMAND + '-' + Constants.SUFFIX_PRINT_UNSTABLE)

                if self.STAB.WAIT_AFTER > 0:
                    cmd.append('G4 P' + str(self.STAB.WAIT_AFTER))

                cmd.append('G0 X' + str(positionTracker.POS_X) + ' Y' + str(positionTracker.POS_Y) + ' Z' + str(positionTracker.POS_Z) + ' F' + str(self.STAB.MOVE_SPEED * 60))

                if shouldDoRetract:
                    cmd.append('G1 E' + str(self.STAB.RETRACT_AMOUNT) + ' Z-' + str(self.STAB.RETRACT_Z_HOP) + ' F' + str(self.STAB.RETRACT_SPEED * 60))

                printer.commands(cmd)
            finally:
                printer.set_job_on_hold(False)
