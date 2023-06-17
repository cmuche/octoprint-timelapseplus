from .stabilizationEaseFn import StabilizationEaseFn
from .stabilizationParkType import StabilizationParkType


class StabilizationSettings:
    def __init__(self, d=None):
        self.RETRACT_SPEED = 30
        self.RETRACT_AMOUNT = 1.2
        self.RETRACT_Z_HOP = 0.2
        self.MOVE_SPEED = 150

        self.PRINTER_X_MIN = 0
        self.PRINTER_X_MAX = 220
        self.PRINTER_Y_MIN = 0
        self.PRINTER_Y_MAX = 220
        self.PRINTER_Z_MAX = 250

        self.PRINTER_HOME_X = 0
        self.PRINTER_HOME_Y = 0
        self.PRINTER_HOME_Z = 0

        self.PARK_X_TYPE = StabilizationParkType.FIXED
        self.PARK_X = 0
        self.PARK_X_SWEEP_FN = StabilizationEaseFn.LINEAR
        self.PARK_X_SWEEP_CYCLES = 5
        self.PARK_X_SWEEP_FROM = 0
        self.PARK_X_SWEEP_TO = 200

        self.PARK_Y_TYPE = StabilizationParkType.FIXED
        self.PARK_Y = 0
        self.PARK_Y_SWEEP_FN = StabilizationEaseFn.LINEAR
        self.PARK_Y_SWEEP_CYCLES = 5
        self.PARK_Y_SWEEP_FROM = 0
        self.PARK_Y_SWEEP_TO = 200

        self.PARK_Z = 0
        self.PARK_Z_RELATIVE = True

        self.WAIT_FOR_MOVEMENT = True
        self.WAIT_BEFORE = 200
        self.WAIT_AFTER = 100

        self.OOZING_COMPENSATION = False
        self.OOZING_COMPENSATION_VALUE = 0.05

        self.INFILL_LOOKAHEAD = False

        self.GCODE_G90_G91_EXTRUDER_OVERWRITE = True

        if d is not None:
            self.setJSON(d)

    def getFeedrateMove(self):
        return self.MOVE_SPEED * 60

    def getFeedrateRetraction(self):
        return self.RETRACT_SPEED * 60

    def setJSON(self, d):
        if 'retractSpeed' in d: self.RETRACT_SPEED = float(d['retractSpeed'])
        if 'retractAmount' in d: self.RETRACT_AMOUNT = float(d['retractAmount'])
        if 'retractZHop' in d: self.RETRACT_Z_HOP = float(d['retractZHop'])
        if 'moveSpeed' in d: self.MOVE_SPEED = float(d['moveSpeed'])

        if 'parkXType' in d: self.PARK_X_TYPE = StabilizationParkType[d['parkXType']]
        if 'parkX' in d: self.PARK_X = float(d['parkX'])
        if 'parkXSweepFn' in d: self.PARK_X_SWEEP_FN = StabilizationEaseFn[d['parkXSweepFn']]
        if 'parkXSweepCycles' in d: self.PARK_X_SWEEP_CYCLES = int(d['parkXSweepCycles'])
        if 'parkXSweepFrom' in d: self.PARK_X_SWEEP_FROM = float(d['parkXSweepFrom'])
        if 'parkXSweepTo' in d: self.PARK_X_SWEEP_TO = float(d['parkXSweepTo'])

        if 'parkYType' in d: self.PARK_Y_TYPE = StabilizationParkType[d['parkYType']]
        if 'parkY' in d: self.PARK_Y = float(d['parkY'])
        if 'parkYSweepFn' in d: self.PARK_Y_SWEEP_FN = StabilizationEaseFn[d['parkYSweepFn']]
        if 'parkYSweepCycles' in d: self.PARK_Y_SWEEP_CYCLES = int(d['parkYSweepCycles'])
        if 'parkYSweepFrom' in d: self.PARK_Y_SWEEP_FROM = float(d['parkYSweepFrom'])
        if 'parkYSweepTo' in d: self.PARK_Y_SWEEP_TO = float(d['parkYSweepTo'])

        if 'parkZ' in d: self.PARK_Z = float(d['parkZ'])
        if 'parkZRelative' in d: self.PARK_Z_RELATIVE = d['parkZRelative']

        if 'waitForMovement' in d: self.WAIT_FOR_MOVEMENT = d['waitForMovement']
        if 'waitBefore' in d: self.WAIT_BEFORE = int(d['waitBefore'])
        if 'waitAfter' in d: self.WAIT_AFTER = int(d['waitAfter'])
        if 'oozingCompensation' in d: self.OOZING_COMPENSATION = d['oozingCompensation']
        if 'oozingCompensationValue' in d: self.OOZING_COMPENSATION_VALUE = float(d['oozingCompensationValue'])
        if 'infillLookahead' in d: self.INFILL_LOOKAHEAD = d['infillLookahead']

        if 'printerXMin' in d: self.PRINTER_X_MIN = float(d['printerXMin'])
        if 'printerXMax' in d: self.PRINTER_X_MAX = float(d['printerXMax'])
        if 'printerYMin' in d: self.PRINTER_Y_MIN = float(d['printerYMin'])
        if 'printerYMax' in d: self.PRINTER_Y_MAX = float(d['printerYMax'])
        if 'printerZMax' in d: self.PRINTER_Z_MAX = float(d['printerZMax'])

        if 'printerHomeX' in d: self.PRINTER_HOME_X = float(d['printerHomeX'])
        if 'printerHomeY' in d: self.PRINTER_HOME_Y = float(d['printerHomeY'])
        if 'printerHomeZ' in d: self.PRINTER_HOME_Z = float(d['printerHomeZ'])

        if 'gcodeG90G91ExtruderOverwrite' in d: self.GCODE_G90_G91_EXTRUDER_OVERWRITE = d['gcodeG90G91ExtruderOverwrite']

    def getJSON(self):
        return dict(
            retractSpeed=self.RETRACT_SPEED,
            retractAmount=self.RETRACT_AMOUNT,
            retractZHop=self.RETRACT_Z_HOP,
            moveSpeed=self.MOVE_SPEED,
            parkXType=self.PARK_X_TYPE.name,
            parkX=self.PARK_X,
            parkXSweepFn=self.PARK_X_SWEEP_FN.name,
            parkXSweepCycles=self.PARK_X_SWEEP_CYCLES,
            parkXSweepFrom=self.PARK_X_SWEEP_FROM,
            parkXSweepTo=self.PARK_X_SWEEP_TO,
            parkYType=self.PARK_Y_TYPE.name,
            parkY=self.PARK_Y,
            parkYSweepFn=self.PARK_Y_SWEEP_FN.name,
            parkYSweepCycles=self.PARK_Y_SWEEP_CYCLES,
            parkYSweepFrom=self.PARK_Y_SWEEP_FROM,
            parkYSweepTo=self.PARK_Y_SWEEP_TO,
            parkZ=self.PARK_Z,
            parkZRelative=self.PARK_Z_RELATIVE,
            waitForMovement=self.WAIT_FOR_MOVEMENT,
            waitBefore=self.WAIT_BEFORE,
            waitAfter=self.WAIT_AFTER,
            oozingCompensation=self.OOZING_COMPENSATION,
            oozingCompensationValue=self.OOZING_COMPENSATION_VALUE,
            infillLookahead=self.INFILL_LOOKAHEAD,
            gcodeG90G91ExtruderOverwrite=self.GCODE_G90_G91_EXTRUDER_OVERWRITE,
            printerXMin=self.PRINTER_X_MIN,
            printerXMax=self.PRINTER_X_MAX,
            printerYMin=self.PRINTER_Y_MIN,
            printerYMax=self.PRINTER_Y_MAX,
            printerZMax=self.PRINTER_Z_MAX,
            printerHomeX=self.PRINTER_HOME_X,
            printerHomeY=self.PRINTER_HOME_Y,
            printerHomeZ=self.PRINTER_HOME_Z
        )
