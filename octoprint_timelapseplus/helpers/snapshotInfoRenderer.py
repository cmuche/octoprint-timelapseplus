from PIL import Image, ImageDraw


class SnapshotInfoRenderer:
    def __init__(self, settings):
        self.IMG_SCALE = 3
        self.IMG_SIZE = (200, 200)
        self.IMG_PADDING = 10
        self.LINE_WIDTH_FACTOR = 60
        self.LINE_WIDTH_MAX = 10
        self.COLOR_FADE_MIN = 200
        self.DOT_CURRENT_R = 30
        self.DOT_CURRENT_COLOR = (114, 137, 218)
        self.DOT_QUEUED_R = 30
        self.DOT_QUEUED_COLOR = (255, 0, 0)

    def getMinMaxPos(self, recording):
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

    def render(self, recording, currentPos, queuedPos):
        imgSize = (self.IMG_SIZE[0] * self.IMG_SCALE, self.IMG_SIZE[1] * self.IMG_SCALE)

        img = Image.new('RGBA', imgSize, (127, 127, 127, 255))
        draw = ImageDraw.Draw(img)

        minmax = self.getMinMaxPos(recording)

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
        draw.ellipse((curDotPos[0] - self.DOT_CURRENT_R, curDotPos[1] - self.DOT_CURRENT_R, curDotPos[0] + self.DOT_CURRENT_R, curDotPos[1] + self.DOT_CURRENT_R), fill=self.DOT_CURRENT_COLOR)

        if queuedPos is not None:
            queuedDotPos = self.mapImgPosition(queuedPos[0], queuedPos[1], queuedPos[2], minmax)
            draw.ellipse((queuedDotPos[0] - self.DOT_QUEUED_R, queuedDotPos[1] - self.DOT_QUEUED_R, queuedDotPos[0] + self.DOT_QUEUED_R, queuedDotPos[1] + self.DOT_QUEUED_R), fill=self.DOT_QUEUED_COLOR)

        imgOut = img.resize(self.IMG_SIZE)
        img.close()

        return imgOut
