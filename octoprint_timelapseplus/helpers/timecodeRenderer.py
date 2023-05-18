from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from ..model.borderSnap import BorderSnap


class TimecodeRenderer:
    def __init__(self, baseFolder):
        self.__basefolder = baseFolder
        self.TEXT_PADDING = 0.1

    def formatTime(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def getElementPosition(self, imgW, imgH, element, margin, snap):
        elemW, elemH = element.size

        if snap == BorderSnap.TOP_LEFT:
            return (margin, margin)
        if snap == BorderSnap.TOP_CENTER:
            return (int(imgW / 2 - elemW / 2), margin)
        if snap == BorderSnap.TOP_RIGHT:
            return (imgW - elemW - margin, margin)
        if snap == BorderSnap.CENTER_RIGHT:
            return (imgW - elemW - margin, int(imgH / 2 - elemH / 2))
        if snap == BorderSnap.BOTTOM_RIGHT:
            return (imgW - elemW - margin, imgH - elemH - margin)
        if snap == BorderSnap.BOTTOM_CENTER:
            return (int(imgW / 2 - elemW / 2), imgH - elemH - margin)
        if snap == BorderSnap.BOTTOM_LEFT:
            return (margin, imgH - elemH - margin)
        if snap == BorderSnap.CENTER_LEFT:
            return (margin, int(imgH / 2 - elemH / 2))

        return (0, 0)

    def applyTimecode(self, img, preset, frameInfo):
        if not preset.TIMECODE:
            return img

        imgW, imgH = img.size
        elementHeight = int(imgH * (preset.TIMECODE_SIZE / 100))
        elementMargin = int(imgH * (preset.TIMECODE_MARGIN / 100))

        text = self.formatTime(frameInfo.getElapsedSeconds())
        tcElement = self.createElementText(text, elementHeight)

        elementPosition = self.getElementPosition(imgW, imgH, tcElement, elementMargin, preset.TIMECODE_SNAP)
        img.paste(tcElement, elementPosition, tcElement)

        return img

    def createElementText(self, text, size):
        fnt = ImageFont.truetype(self.__basefolder + '/static/assets/fonts/Inconsolata-Regular.ttf', size)
        padding = int(size * self.TEXT_PADDING)
        dummy = Image.new("RGBA", (1, 1))
        dummyDraw = ImageDraw.Draw(dummy, 'RGBA')
        textW, textH = dummyDraw.textsize(text, font=fnt)
        bbox = (0, 0, padding * 2 + textW, padding * 3 + textH)
        dummy.close()
        img = Image.new("RGBA", (bbox[2], bbox[3]))
        draw = ImageDraw.Draw(img, 'RGBA')
        draw.rectangle(bbox, fill=(0, 0, 0, 127))
        draw.text((padding, padding), text, font=fnt, fill=(255, 255, 255))
        return img
