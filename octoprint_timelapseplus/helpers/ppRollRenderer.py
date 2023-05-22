import math

from PIL import Image, ImageFilter
from PIL import ImageDraw
from PIL import ImageFont

from .colorHelper import ColorHelper
from ..model.ppRollEaseFn import PPRollEaseFn
from ..model.ppRollPhase import PPRollPhase
from ..model.ppRollType import PPRollType


class PPRollRenderer:
    @staticmethod
    def renderFrame(ratio, frames, preset, phase, metadata, baseFolder):
        type = preset.PPROLL_TYPE

        if phase == PPRollPhase.PRE:
            ratio = PPRollRenderer.applyEaseFn(preset.PPROLL_EASE_FN, 1 - ratio)
        else:
            ratio = PPRollRenderer.applyEaseFn(preset.PPROLL_EASE_FN, ratio)

        img = None

        if type == PPRollType.STILL:
            img = PPRollRenderer.getStillFrame(frames, phase)
        elif type == PPRollType.STILL_FINAL:
            img = PPRollRenderer.getStillFrame(frames, PPRollPhase.POST)
        elif type == PPRollType.LAPSE:
            reverse = (phase == PPRollPhase.POST)
            img = PPRollRenderer.getLapseFrame(frames, ratio, reverse)

        if preset.PPROLL_BLUR:
            blurRadius = ratio * preset.PPROLL_BLUR_RADIUS
            img = img.filter(ImageFilter.GaussianBlur(blurRadius))

        if preset.PPROLL_ZOOM:
            zoomFactor = 1 + ratio * (preset.PPROLL_ZOOM_FACTOR - 1)
            img = PPRollRenderer.zoomImage(img, zoomFactor)

        if preset.PPROLL_TEXT and phase == PPRollPhase.PRE:
            if metadata is None:
                raise Exception('The Frame Collection doesn\'t contain any Metadata. Pre/Post Roll Text can\'t be added.')
            printName = metadata['baseName']

            imgText = Image.new('RGBA', img.size)
            fnt = ImageFont.truetype(baseFolder + '/static/assets/fonts/Inconsolata-Bold.ttf', 100)
            draw = ImageDraw.Draw(imgText, 'RGBA')
            col = ColorHelper.hexToRgba(preset.PPROLL_TEXT_FOREGROUND, max(0, ratio - 0.2))
            draw.text((10, 10), printName, font=fnt, fill=col, anchor='la')
            img.paste(imgText, (0, 0), imgText)
            imgText.close()

        return img

    @staticmethod
    def zoomImage(image, zoomFactor):
        width, height = image.size
        cropWidth = int(width / zoomFactor)
        cropHeight = int(height / zoomFactor)
        left = (width - cropWidth) // 2
        top = (height - cropHeight) // 2
        right = left + cropWidth
        bottom = top + cropHeight
        croppedImage = image.crop((left, top, right, bottom))
        resizedImage = croppedImage.resize((width, height), Image.LANCZOS)
        return resizedImage

    @staticmethod
    def applyEaseFn(fn, r):
        if fn == PPRollEaseFn.LINEAR:
            return r
        if fn == PPRollEaseFn.EASE_IN:
            return 1 - math.sqrt(1 - r * r)
        if fn == PPRollEaseFn.EASE_IN_OUT:
            rr = r * 2
            if rr < 1:
                return 0.5 * (1 - math.sqrt(1 - rr * rr))
            else:
                rr -= 2
                return 0.5 * (math.sqrt(1 - rr * rr) + 1)

    @staticmethod
    def getLapseFrame(frames, ratio, reverse):
        if reverse:
            frames = frames[::-1]
        retFrameIdx = int(round(ratio * (len(frames) - 1)))
        return Image.open(frames[retFrameIdx])

    @staticmethod
    def getStillFrame(frames, phase):
        if phase == PPRollPhase.PRE:
            return Image.open(frames[0])
        else:
            return Image.open(frames[-1])
