class StabilizationSettings:
    def __init__(self, d=None):
        self.RETRACT_SPEED = 30
        self.RETRACT_AMOUNT = 1.2
        self.RETRACT_Z_HOP = 0.2
        self.MOVE_SPEED = 150
        self.PARK_X = 30
        self.PARK_Y = 125
        self.PARK_Z = 10
        self.PARK_Z_RELATIVE = True
        self.WAIT_FOR_MOVEMENT = True
        self.WAIT_BEFORE = 200
        self.WAIT_AFTER = 100

        if d is not None:
            self.setJSON(d)

    def setJSON(self, d):
        if 'retractSpeed' in d: self.RETRACT_SPEED = float(d['retractSpeed'])
        if 'retractAmount' in d: self.RETRACT_AMOUNT = float(d['retractAmount'])
        if 'retractZHop' in d: self.RETRACT_Z_HOP = float(d['retractZHop'])
        if 'moveSpeed' in d: self.MOVE_SPEED = float(d['moveSpeed'])
        if 'parkX' in d: self.PARK_X = float(d['parkX'])
        if 'parkY' in d: self.PARK_Y = float(d['parkY'])
        if 'parkZ' in d: self.PARK_Z = float(d['parkZ'])
        if 'parkZRelative' in d: self.PARK_Z_RELATIVE = d['parkZRelative']
        if 'waitForMovement' in d: self.WAIT_FOR_MOVEMENT = d['waitForMovement']
        if 'waitBefore' in d: self.WAIT_BEFORE = int(d['waitBefore'])
        if 'waitAfter' in d: self.WAIT_AFTER = int(d['waitAfter'])

    def getJSON(self):
        return dict(
            retractSpeed=self.RETRACT_SPEED,
            retractAmount=self.RETRACT_AMOUNT,
            retractZHop=self.RETRACT_Z_HOP,
            moveSpeed=self.MOVE_SPEED,
            parkX=self.PARK_X,
            parkY=self.PARK_Y,
            parkZ=self.PARK_Z,
            parkZRelative=self.PARK_Z_RELATIVE,
            waitForMovement=self.WAIT_FOR_MOVEMENT,
            waitBefore=self.WAIT_BEFORE,
            waitAfter=self.WAIT_AFTER,
        )
