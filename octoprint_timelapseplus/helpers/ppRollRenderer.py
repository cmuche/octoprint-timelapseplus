import math
import re

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
        ppBlur = preset.PPROLL_PRE_BLUR
        ppType = preset.PPROLL_PRE_TYPE
        ppEaseFn = preset.PPROLL_PRE_EASE_FN
        ppZoom = preset.PPROLL_PRE_ZOOM
        if phase == PPRollPhase.POST:
            ppBlur = preset.PPROLL_POST_BLUR
            ppType = preset.PPROLL_POST_TYPE
            ppEaseFn = preset.PPROLL_POST_EASE_FN
            ppZoom = preset.PPROLL_POST_ZOOM

        if phase == PPRollPhase.PRE:
            ratio = PPRollRenderer.applyEaseFn(ppEaseFn, 1 - ratio)
        else:
            ratio = PPRollRenderer.applyEaseFn(ppEaseFn, ratio)

        img = None

        if ppType == PPRollType.STILL:
            img = PPRollRenderer.getStillFrame(frames, phase)
        elif ppType == PPRollType.STILL_FINAL:
            img = PPRollRenderer.getStillFrame(frames, PPRollPhase.POST)
        elif ppType == PPRollType.LAPSE:
            reverse = (phase == PPRollPhase.POST)
            img = PPRollRenderer.getLapseFrame(frames, ratio, reverse)

        if ppBlur:
            blurRadius = ratio * preset.PPROLL_BLUR_RADIUS
            img = img.filter(ImageFilter.GaussianBlur(blurRadius))

        zoomFactor = 1.0
        if ppZoom:
            zoomFactor = 1 + ratio * (preset.PPROLL_ZOOM_FACTOR - 1)
            img = PPRollRenderer.zoomImage(img, zoomFactor)

        if preset.PPROLL_TEXT and phase == PPRollPhase.PRE:
            if metadata is None:
                raise Exception('The Frame Collection doesn\'t contain any Metadata. Pre/Post Roll Text can\'t be added.')

            printName = metadata['baseName']
            match = re.search(preset.PPROLL_TEXT_REGEX, printName)
            gList = match.groups() if match else [printName]
            printName = '\n'.join(gList)

            imgW, imgH = img.size
            textSize = int(imgH * preset.PPROLL_TEXT_SIZE / 100)
            textSpacing = int(textSize / 4)
            textPadding = int(textSize / 3)
            fnt = ImageFont.truetype(baseFolder + '/static/assets/fonts/Inconsolata-Bold.ttf', textSize)

            colText = ColorHelper.hexToRgba(preset.PPROLL_TEXT_FOREGROUND, max(0, ratio - 0.2))
            colBg = ColorHelper.hexToRgba(preset.PPROLL_TEXT_BACKGROUND, max(0, ratio - 0.2) * 0.5)

            imgText = Image.new('RGBA', img.size)
            draw = ImageDraw.Draw(imgText, 'RGBA')

            textBbox = draw.multiline_textbbox((0, 0), printName, font=fnt, anchor='la', spacing=textSpacing)
            backgroundBbox = (0, 0, textBbox[2] + 2 * textPadding, textBbox[3] + 2 * textPadding)

            offsX = int(imgW / 2 - backgroundBbox[2] / 2)
            offsY = int(imgH / 2 - backgroundBbox[3] / 2)

            draw.rectangle((offsX, offsY, offsX + backgroundBbox[2], offsY + backgroundBbox[3]), fill=colBg)
            draw.multiline_text((offsX + textPadding, offsY + textPadding), printName, align='center', font=fnt, fill=colText, anchor='la', spacing=textSpacing)

            textZoom = 0.6 + zoomFactor * 0.4
            imgText = PPRollRenderer.zoomImage(imgText, textZoom)

            img.paste(imgText, (0, 0), imgText)
            imgText.close()

        return img

    @staticmethod
    def zoomImage(image, zoomFactor):
        if zoomFactor == 1:
            return image

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
