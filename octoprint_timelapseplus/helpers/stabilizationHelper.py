class StabilizationHelper:

    def stabilizeAndQueueSnapshotRaw(self, printer, positionTracker):
        if printer.set_job_on_hold(True):
            cmd = []
            try:
                spRetract = 30
                spMove = 150
                ppX = 30
                ppY = 125

                cmd.append('G1 G1 E-1.2 F' + str(spRetract * 60))
                cmd.append('G0 X' + str(ppX) + ' Y' + str(ppY) + ' F' + str(spMove * 60))
                cmd.append('M400')
                cmd.append('G4 P200')
                cmd.append('@SNAPSHOT-RAW')
                cmd.append('G4 P200')
                cmd.append('G0 X' + str(positionTracker.POS_X) + ' Y' + str(positionTracker.POS_Y) + ' F' + str(spMove * 60))
                cmd.append('G1 G1 E1.2 F' + str(spRetract * 60))

                printer.commands(cmd)
            finally:
                printer.set_job_on_hold(False)
