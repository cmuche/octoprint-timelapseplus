import re

from ..constants import Constants


class PositionTracker:

    def __init__(self) -> None:
        self.POS_X = 0
        self.POS_Y = 0
        self.POS_Z = 0
        self.POS_E = 0
        self.FEEDRATE = 0
        self.RELATIVE_MODE = False
        self.RELATIVE_MODE_EXTRUDER = False

    def getMatchForProp(self, gcode, command, prop):
        if gcode is None or command is None:
            return None

        regex = '^' + gcode + ' .*' + prop + '([0-9\\.-]+).*'
        match = re.search(regex, command)
        if not match:
            return None
        val = match.group(1)

        try:
            val = val.strip()
            return self.parseFloat(val)
        except:
            return None

    def parseFloat(self, val):
        if val.startswith('-'):
            sign = -1
            val = val[1:]
        else:
            sign = 1

        if val.startswith('.'):
            val = '0' + val

        try:
            value = float(val)
            return sign * value
        except ValueError:
            return None

    def setPosition(self, x, y, z, e, f, override=False):
        if x is not None:
            if self.RELATIVE_MODE and not override:
                self.POS_X += x
            else:
                self.POS_X = x
        if y is not None:
            if self.RELATIVE_MODE and not override:
                self.POS_Y += y
            else:
                self.POS_Y = y
        if z is not None:
            if self.RELATIVE_MODE and not override:
                self.POS_Z += z
            else:
                self.POS_Z = z

        if e is not None:
            if self.RELATIVE_MODE_EXTRUDER and not override:
                self.POS_E += e
            else:
                self.POS_E = e

        if f is not None:
            self.FEEDRATE = f


    def consumeGcode(self, gcode, command, tags):
        if Constants.GCODE_TAG_STABILIZATION in tags:
            return

        propX = self.getMatchForProp(gcode, command, 'X')
        propY = self.getMatchForProp(gcode, command, 'Y')
        propZ = self.getMatchForProp(gcode, command, 'Z')
        propE = self.getMatchForProp(gcode, command, 'E')
        propF = self.getMatchForProp(gcode, command, 'F')

        if gcode == 'G0' or gcode == 'G1':
            # Linear Move https://marlinfw.org/docs/gcode/G000-G001.html
            self.setPosition(propX, propY, propZ, propE, propF)
        if gcode == 'G2' or gcode == 'G3':
            # Arc or Circle Move https://marlinfw.org/docs/gcode/G002-G003.html
            self.setPosition(propX, propY, propZ, propE, propF)
        elif gcode == 'M82':
            # E Absolute https://marlinfw.org/docs/gcode/M083.html
            self.RELATIVE_MODE_EXTRUDER = False
        elif gcode == 'M83':
            # E Relative https://marlinfw.org/docs/gcode/M083.html
            self.RELATIVE_MODE_EXTRUDER = True
        elif gcode == 'G90':
            # Absolute Positioning https://marlinfw.org/docs/gcode/G090.html
            # OVERWRITES EXTRUDER ON MARLIN
            self.RELATIVE_MODE = False

            if Constants.GCODE_G90_G91_EXTRUDER_OVERWRITE:
                self.RELATIVE_MODE_EXTRUDER = False
        elif gcode == 'G91':
            # Relative Positioning https://marlinfw.org/docs/gcode/G091.html
            # OVERWRITES EXTRUDER ON MARLIN
            self.RELATIVE_MODE = True

            if Constants.GCODE_G90_G91_EXTRUDER_OVERWRITE:
                self.RELATIVE_MODE_EXTRUDER = True
        elif gcode == 'G92':
            # Set Position https://marlinfw.org/docs/gcode/G092.html
            self.setPosition(propX, propY, propZ, propE, propF, True)
        else:
            return
