from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


class TimecodeRenderer:
    def __init__(self, baseFolder):
        self.__basefolder = baseFolder
        self.TEXT_PADDING = 0.1

    def formatTime(self, seconds):
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def applyTimecode(self, img, frameInfo):
        size = 10
        imgW, imgH = img.size
        elementHeight = int(imgH * (size / 100))

        text = self.formatTime(frameInfo.getElapsedSeconds())
        imgText = self.createText(text, elementHeight)
        img.paste(imgText, (10, 10), imgText)
        return img

    def createText(self, text, size):
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
