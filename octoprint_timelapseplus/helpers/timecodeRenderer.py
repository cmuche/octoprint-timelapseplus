import math

from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont

from ..model.borderSnap import BorderSnap
from ..model.timecodeType import TimecodeType


class TimecodeRenderer:
    def __init__(self, baseFolder):
        self.__basefolder = baseFolder
        self.TEXT_PADDING = 0.1
        self.AA_FACTOR = 3

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
        elementMargin = int(imgH * (preset.TIMECODE_MARGIN / 100))
        element = self.createElement(imgW, imgH, preset, frameInfo)
        elementPosition = self.getElementPosition(imgW, imgH, element, elementMargin, preset.TIMECODE_SNAP)
        img.paste(element, elementPosition, element)

        return img

    def createElement(self, imgW, imgH, preset, frameInfo):
        type = preset.TIMECODE_TYPE

        elemH = math.ceil(imgH * (preset.TIMECODE_SIZE / 100)) * self.AA_FACTOR

        if type == TimecodeType.BAR:
            elemW = int(imgW / 2) * self.AA_FACTOR
            elem = self.createElementBar(elemW, elemH, frameInfo.getRatio())
        else:
            text = self.createText(type, frameInfo)
            elem = self.createElementText(text, elemH)

        finW, finH = elem.size
        elem = elem.resize((finW // self.AA_FACTOR, finH // self.AA_FACTOR), resample=Image.LANCZOS)
        return elem

    def createElementBar(self, width, height, ratio):
        borderW = int(height * 0.15)
        borderWH = int(borderW * 2)
        radius = math.floor(height / 2)
        img = Image.new("RGBA", (width, height))
        draw = ImageDraw.Draw(img, 'RGBA')
        draw.rounded_rectangle((1, 1, width, height), fill=(0, 0, 0, 127), radius=radius)

        innerW = int((width - borderWH) * ratio)
        if innerW > borderWH:
            draw.rounded_rectangle((borderWH + 1, borderWH + 1, innerW, height - borderWH), fill=(255, 255, 255, 220), radius=radius)

        draw.rounded_rectangle((1, 1, width, height), outline=(255, 255, 255, 220), width=borderW, radius=radius)
        return img

    def createText(self, type, frameInfo):
        pt = frameInfo.getElapsedSeconds()
        ptH = pt // 3600
        ptM = (pt % 3600) // 60
        ptS = pt % 60
        t = frameInfo.getDateTime()
        r = frameInfo.getRatio()

        if type == TimecodeType.PRINTTIME_HMS:
            return f"{ptH:02d}:{ptM:02d}:{ptS:02d}"
        if type == TimecodeType.PRINTTIME_HM:
            return f"{ptH:02d}:{ptM:02d}"
        if type == TimecodeType.PRINTTIME_HMS_LETTERS:
            return f"{ptH:02d}h {ptM:02d}m {ptS:02d}s"
        if type == TimecodeType.PRINTTIME_HM_LETTERS:
            return f"{ptH:02d}h {ptM:02d}m"

        if type == TimecodeType.PERCENT:
            return f"{round(r * 100)}%"

        if type == TimecodeType.TIME_HMS_12:
            return t.strftime("%I:%M:%S")
        if type == TimecodeType.TIME_HMS_24:
            return t.strftime("%H:%M:%S")
        if type == TimecodeType.TIME_HM_12:
            return t.strftime("%I:%M")
        if type == TimecodeType.TIME_HM_24:
            return t.strftime("%H:%M")

        return '?'

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
