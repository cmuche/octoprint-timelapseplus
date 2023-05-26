class StabilizationHelper:

    def __init__(self, settings):
        self.RETRACT_SPEED = 30
        self.RETRACT_AMOUNT = 1.2
        self.MOVE_SPEED = 150
        self.PARK_X = 30
        self.PARK_Y = 125

    def stabilizeAndQueueSnapshotRaw(self, printer, positionTracker):
        if printer.set_job_on_hold(True):
            cmd = []
            try:
                cmd.append('G1 G1 E-' + str(self.RETRACT_AMOUNT) + ' F' + str(self.RETRACT_SPEED * 60))
                cmd.append('G0 X' + str(self.PARK_X) + ' Y' + str(self.PARK_Y) + ' F' + str(self.MOVE_SPEED * 60))
                cmd.append('M400')
                cmd.append('G4 P200')
                cmd.append('@SNAPSHOT-UNSTABLE')
                cmd.append('G4 P200')
                cmd.append('G0 X' + str(positionTracker.POS_X) + ' Y' + str(positionTracker.POS_Y) + ' F' + str(self.MOVE_SPEED * 60))
                cmd.append('G1 G1 E' + str(self.RETRACT_AMOUNT) + ' F' + str(self.RETRACT_SPEED * 60))

                printer.commands(cmd)
            finally:
                printer.set_job_on_hold(False)
