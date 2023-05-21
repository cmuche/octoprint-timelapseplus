import math

from PIL import Image, ImageFilter

from ..model.ppRollPhase import PPRollPhase
from ..model.ppRollType import PPRollType


class PPRollRenderer:
    @staticmethod
    def renderFrame(ratio, frames, preset, phase):
        type = preset.PPROLL_TYPE

        ratioEase = PPRollRenderer.applyEaseFn(ratio)
        ratioEaseInv = PPRollRenderer.applyEaseFn(1 - ratio)

        img = None

        if type == PPRollType.STILL:
            img = PPRollRenderer.getStillFrame(frames, phase)
        elif type == PPRollType.STILL_FINAL:
            img = PPRollRenderer.getStillFrame(frames, PPRollPhase.POST)
        elif type == PPRollType.LAPSE:
            img = PPRollRenderer.getLapseFrame(frames, ratioEase)

        if preset.PPROLL_BLUR:
            blurRatio = ratioEase
            if phase == PPRollPhase.PRE:
                blurRatio = ratioEaseInv
            blurRadius = blurRatio * preset.PPROLL_BLUR_RADIUS
            img = img.filter(ImageFilter.GaussianBlur(blurRadius))

        if preset.PPROLL_ZOOM:
            zoomRatio = ratioEase
            if phase == PPRollPhase.PRE:
                zoomRatio = ratioEaseInv
            zoomFactor = 1 + zoomRatio * (preset.PPROLL_ZOOM_FACTOR - 1)
            img = PPRollRenderer.zoomImage(img, zoomFactor)

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
    def applyEaseFn(ratio):
        return 1 - math.sqrt(1 - ratio * ratio)

    @staticmethod
    def getLapseFrame(frames, ratio):
        retFrameIdx = int(round((1 - ratio) * len(frames) - 1))
        return Image.open(frames[retFrameIdx])

    @staticmethod
    def getStillFrame(frames, phase):
        if phase == PPRollPhase.PRE:
            return Image.open(frames[0])
        else:
            return Image.open(frames[-1])
