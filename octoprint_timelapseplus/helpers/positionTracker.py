import re


class PositionTracker:

    def __init__(self) -> None:
        self.POS_X = 0
        self.POS_Y = 0
        self.POS_Z = 0

    def getMatchForProp(self, gcode, command, prop):
        regex = '^' + gcode + ' .*' + prop + '([0-9\\.-]+).*'
        match = re.search(regex, command)
        if not match:
            return None
        val = match.group(1)

        try:
            return float(val)
        except:
            return None

    def consumeGcode(self, gcode, command):
        if gcode != 'G0' and gcode != 'G1':
            return

        propX = self.getMatchForProp(gcode, command, 'X')
        propY = self.getMatchForProp(gcode, command, 'Y')
        propZ = self.getMatchForProp(gcode, command, 'Z')

        if propX is not None:
            self.POS_X = propX
        if propY is not None:
            self.POS_Y = propY
        if propZ is not None:
            self.POS_Z = propZ
