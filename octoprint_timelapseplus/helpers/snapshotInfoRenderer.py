from PIL import Image, ImageDraw

from ..log import Log


class SnapshotInfoRenderer:
    def __init__(self, settings, printer):
        self.IMG_SCALE = 3
        self.IMG_SIZE = (200, 200)
        self.IMG_PADDING = 10
        self.LINE_WIDTH_FACTOR = 70
        self.LINE_WIDTH_MAX = 10
        self.LINE_PARKING_WIDTH = 5
        self.LINE_PARKING_COLOR = (253, 247, 195)
        self.COLOR_FADE_MIN = 180
        self.DOT_BORDER_RATIO = 0.25
        self.DOT_CURRENT_R = 25
        
        self.DOT_CURRENT_COLOR = (0, 223, 162)
        self.DOT_QUEUED_R = 25
        self.DOT_QUEUED_COLOR = (255, 0, 96)
        self.DOT_PARKING_R = 25
        self.DOT_PARKING_COLOR = (0, 121, 255)

        self.PRINTER_PROFILE_AVAILABLE = False
        self.PRINTER_PROFILE_WIDTH = None
        self.PRINTER_PROFILE_HEIGHT = None

        try:
            self.PRINTER_PROFILE_WIDTH = float(printer._printerProfileManager.default['volume']['width'])
            self.PRINTER_PROFILE_HEIGHT = float(printer._printerProfileManager.default['volume']['height'])
            self.PRINTER_PROFILE_AVAILABLE = True
        except Exception as err:
            Log.warning('Could not set Printer Profile Volume', err)

    def getMinMaxPos(self, recording, additionalPoints):
        minX = minY = minZ = float('inf')
        maxX = maxY = maxZ = float('-inf')

        for r in recording:
            posFrom, posTo = r[0], r[1]

            minX = min(minX, posFrom[0], posTo[0])
            maxX = max(maxX, posFrom[0], posTo[0])
            minY = min(minY, posFrom[1], posTo[1])
            maxY = max(maxY, posFrom[1], posTo[1])
            minZ = min(minZ, posFrom[2], posTo[2])
            maxZ = max(maxZ, posFrom[2], posTo[2])

        if self.PRINTER_PROFILE_AVAILABLE:
            additionalPoints.append((0, 0, 0))
            additionalPoints.append((self.PRINTER_PROFILE_WIDTH, self.PRINTER_PROFILE_HEIGHT, 0))

        for ap in additionalPoints:
            if ap is None:
                continue

            minX = min(minX, ap[0])
            maxX = max(maxX, ap[0])
            minY = min(minY, ap[1])
            maxY = max(maxY, ap[1])
            minZ = min(minZ, ap[2])
            maxZ = max(maxZ, ap[2])

        minX = minX if minX != float('inf') else 0
        minY = minY if minY != float('inf') else 0
        minZ = minZ if minZ != float('inf') else 0
        maxX = maxX if maxX != float('-inf') else 0
        maxY = maxY if maxY != float('-inf') else 0
        maxZ = maxZ if maxZ != float('-inf') else 0

        spanX = maxX - minX
        spanY = maxY - minY
        spanZ = maxZ - minZ

        #      0     1     2     3     4     5     6      7      8
        return minX, minY, minZ, maxX, maxY, maxZ, spanX, spanY, spanZ

    def mapImgPosition(self, x, y, z, minmax):
        pX = 0
        pY = 0
        pZ = 0

        spanImgX = (self.IMG_SIZE[0] - 2 * self.IMG_PADDING) * self.IMG_SCALE
        spanImgY = (self.IMG_SIZE[1] - 2 * self.IMG_PADDING) * self.IMG_SCALE
        spanPosX = minmax[6]
        spanPosY = minmax[7]

        if spanPosX > 0 and spanPosY > 0:
            scaleX = spanImgX / spanPosX
            scaleY = spanImgY / spanPosY
            scale = min(scaleX, scaleY)
            pX = (x - minmax[0]) * scale + (spanImgX - spanPosX * scale) / 2
            pY = (y - minmax[1]) * scale + (spanImgY - spanPosY * scale) / 2

        return int(pX) + self.IMG_PADDING * self.IMG_SCALE, (self.IMG_SIZE[1] * self.IMG_SCALE) - (int(pY) + self.IMG_PADDING * self.IMG_SCALE), pZ

    def drawPoint(self, draw, pos, size, color):
        sizeInner = int(size * (1 - self.DOT_BORDER_RATIO))
        colorInner = (color[0], color[1], color[2], 127)
        dotRect = (pos[0] - size, pos[1] - size, pos[0] + size, pos[1] + size)
        dotRectInner = (pos[0] - sizeInner, pos[1] - sizeInner, pos[0] + sizeInner, pos[1] + sizeInner)
        draw.ellipse(dotRect, fill=color)
        draw.ellipse(dotRectInner, fill=colorInner)

    def render(self, recording, currentPos, queuedPos, parkingPos):
        imgSize = (self.IMG_SIZE[0] * self.IMG_SCALE, self.IMG_SIZE[1] * self.IMG_SCALE)

        img = Image.new('RGBA', imgSize, (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        minmax = self.getMinMaxPos(recording, [currentPos, queuedPos, parkingPos])

        lineWidth = 1
        maxSpan = max(minmax[6], minmax[7])
        if maxSpan > 0:
            lineWidth = 1 / maxSpan * self.LINE_WIDTH_FACTOR * self.IMG_SCALE
        lineWidth = min(self.LINE_WIDTH_MAX * self.IMG_SCALE, lineWidth)
        lineWidth = max(1 * self.IMG_SCALE, lineWidth)

        for i, rec in enumerate(recording):
            posFrom = rec[0]
            posTo = rec[1]
            lFrom = self.mapImgPosition(posFrom[0], posFrom[1], 0, minmax)
            lTo = self.mapImgPosition(posTo[0], posTo[1], 0, minmax)

            r = i / len(recording)
            opacity = int(self.COLOR_FADE_MIN + (255 - self.COLOR_FADE_MIN) * r)
            draw.line((lFrom[0], lFrom[1], lTo[0], lTo[1]), fill=(255, 255, 255, opacity), width=int(lineWidth), joint='curve')

        curDotPos = self.mapImgPosition(currentPos[0], currentPos[1], currentPos[2], minmax)

        if parkingPos is not None:
            parkingDotPos = self.mapImgPosition(parkingPos[0], parkingPos[1], parkingPos[2], minmax)
            draw.line((curDotPos[0], curDotPos[1], parkingDotPos[0], parkingDotPos[1]), fill=self.LINE_PARKING_COLOR, width=self.LINE_PARKING_WIDTH)
            self.drawPoint(draw, parkingDotPos, self.DOT_PARKING_R, self.DOT_PARKING_COLOR)

        if queuedPos is not None:
            queuedDotPos = self.mapImgPosition(queuedPos[0], queuedPos[1], queuedPos[2], minmax)
            self.drawPoint(draw, queuedDotPos, self.DOT_QUEUED_R, self.DOT_QUEUED_COLOR)

        self.drawPoint(draw, curDotPos, self.DOT_CURRENT_R, self.DOT_CURRENT_COLOR)

        imgOut = img.resize(self.IMG_SIZE)
        img.close()

        return imgOut
