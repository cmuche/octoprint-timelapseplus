from ..constants import Constants


class StabilizationHelper:

    def __init__(self, settings):
        self.SNAPSHOT_COMMAND = settings.get(["snapshotCommand"])
        self.RETRACT_SPEED = 30
        self.RETRACT_AMOUNT = 1.2
        self.RETRACT_ZHOP = 0.2
        self.MOVE_SPEED = 150
        self.PARK_X = 30
        self.PARK_Y = 125
        self.PARK_Z = 2
        self.PARK_Z_RELATIVE = True
        self.WAIT_FOR_MOVEMENT = True
        self.WAIT_BEFORE = 200
        self.WAIT_AFTER = 100

    def stabilizeAndQueueSnapshotRaw(self, printer, positionTracker):
        if printer.set_job_on_hold(True):

            shouldDoRetract = self.RETRACT_AMOUNT > 0 or self.RETRACT_ZHOP > 0
            newZPos = self.PARK_Z
            if self.PARK_Z_RELATIVE:
                newZPos = positionTracker.POS_Z + self.PARK_Z

            cmd = []
            try:
                if shouldDoRetract:
                    cmd.append('G1 E-' + str(self.RETRACT_AMOUNT) + ' Z' + str(self.RETRACT_ZHOP) + ' F' + str(self.RETRACT_SPEED * 60))

                cmd.append('G0 X' + str(self.PARK_X) + ' Y' + str(self.PARK_Y) + ' Z' + str(newZPos) + ' F' + str(self.MOVE_SPEED * 60))

                if self.WAIT_FOR_MOVEMENT:
                    cmd.append('M400')

                if self.WAIT_BEFORE > 0:
                    cmd.append('G4 P' + int(self.WAIT_BEFORE))

                cmd.append('@' + self.SNAPSHOT_COMMAND + '-' + Constants.SUFFIX_PRINT_UNSTABLE)

                if self.WAIT_AFTER > 0:
                    cmd.append('G4 P' + int(self.WAIT_AFTER))

                cmd.append('G0 X' + str(positionTracker.POS_X) + ' Y' + str(positionTracker.POS_Y) + ' Z' + str(positionTracker.POS_Z) + ' F' + str(self.MOVE_SPEED * 60))

                if shouldDoRetract:
                    cmd.append('G1 E' + str(self.RETRACT_AMOUNT) + ' Z-' + str(self.RETRACT_ZHOP) + ' F' + str(self.RETRACT_SPEED * 60))

                printer.commands(cmd)
            finally:
                printer.set_job_on_hold(False)
