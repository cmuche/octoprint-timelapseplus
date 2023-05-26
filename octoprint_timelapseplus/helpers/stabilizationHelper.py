class StabilizationHelper:

    def __init__(self, settings):
        self.RETRACT_SPEED = 30
        self.RETRACT_AMOUNT = 1.2
        self.MOVE_SPEED = 150
        self.PARK_X = 30
        self.PARK_Y = 125
        self.WAIT_FOR_MOVEMENT = True
        self.WAIT_BEFORE = 200
        self.WAIT_AFTER = 100

    def stabilizeAndQueueSnapshotRaw(self, printer, positionTracker):
        if printer.set_job_on_hold(True):
            cmd = []
            try:
                if self.RETRACT_AMOUNT > 0:
                    cmd.append('G1 G1 E-' + str(self.RETRACT_AMOUNT) + ' F' + str(self.RETRACT_SPEED * 60))

                cmd.append('G0 X' + str(self.PARK_X) + ' Y' + str(self.PARK_Y) + ' F' + str(self.MOVE_SPEED * 60))

                if self.WAIT_FOR_MOVEMENT:
                    cmd.append('M400')

                if self.WAIT_BEFORE > 0:
                    cmd.append('G4 P' + int(self.WAIT_BEFORE))

                # todo snapshot command from settings
                cmd.append('@SNAPSHOT-UNSTABLE')

                if self.WAIT_AFTER > 0:
                    cmd.append('G4 P' + int(self.WAIT_AFTER))

                cmd.append('G0 X' + str(positionTracker.POS_X) + ' Y' + str(positionTracker.POS_Y) + ' F' + str(self.MOVE_SPEED * 60))

                if self.RETRACT_AMOUNT > 0:
                    cmd.append('G1 G1 E' + str(self.RETRACT_AMOUNT) + ' F' + str(self.RETRACT_SPEED * 60))

                printer.commands(cmd)
            finally:
                printer.set_job_on_hold(False)
