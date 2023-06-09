from math import ceil

from PIL import Image

from .combineMethod import CombineMethod
from .ppRollEaseFn import PPRollEaseFn
from .ppRollType import PPRollType
from ..helpers.colorHelper import ColorHelper
from ..helpers.listHelper import ListHelper


class RenderPreset:
    def __init__(self, d=None):
        self.NAME = 'Default Render Preset'

        self.FRAMERATE = 30

        self.RESIZE = False
        self.RESIZE_W = 1280
        self.RESIZE_H = 720

        self.INTERPOLATE = False
        self.INTERPOLATE_FRAMERATE = 60
        self.INTERPOLATE_MODE = 'blend'
        self.INTERPOLATE_ESTIMATION = 'bidir'
        self.INTERPOLATE_COMPENSATION = 'aobmc'
        self.INTERPOLATE_ALGORITHM = 'epzs'

        self.FADE = False
        self.FADE_IN_DURATION = 1000
        self.FADE_OUT_DURATION = 1000
        self.FADE_COLOR = 'Black'

        self.COMBINE = False
        self.COMBINE_SIZE = 2
        self.COMBINE_METHOD = CombineMethod.DROP

        self.PPROLL = False
        self.PPROLL_PRE_DURATION = 5000
        self.PPROLL_POST_DURATION = 2000
        self.PPROLL_PRE_TYPE = PPRollType.STILL
        self.PPROLL_POST_TYPE = PPRollType.STILL
        self.PPROLL_PRE_EASE_FN = PPRollEaseFn.EASE_IN_OUT
        self.PPROLL_POST_EASE_FN = PPRollEaseFn.EASE_IN
        self.PPROLL_PRE_BLUR = True
        self.PPROLL_POST_BLUR = False
        self.PPROLL_BLUR_RADIUS = 50
        self.PPROLL_PRE_ZOOM = True
        self.PPROLL_POST_ZOOM = True
        self.PPROLL_ZOOM_FACTOR = 1.25
        self.PPROLL_TEXT = True
        self.PPROLL_TEXT_SIZE = 10
        self.PPROLL_TEXT_FOREGROUND = '#FFFFFF'
        self.PPROLL_TEXT_BACKGROUND = '#000000'
        self.PPROLL_TEXT_REGEX = '(.*)'

        if d is not None:
            self.setJSON(d)

    def applyResize(self, img):
        if not self.RESIZE:
            return img

        img = img.resize((self.RESIZE_W, self.RESIZE_H), resample=Image.LANCZOS)
        return img

    def getFinalFramerate(self):
        if self.INTERPOLATE:
            return self.INTERPOLATE_FRAMERATE
        return self.FRAMERATE

    def getNumPPRollFramesPre(self):
        if not self.PPROLL:
            return 0
        return int(self.getFinalFramerate() * self.PPROLL_PRE_DURATION / 1000)

    def getNumPPRollFramesPost(self):
        if not self.PPROLL:
            return 0
        return int(self.getFinalFramerate() * self.PPROLL_POST_DURATION / 1000)

    def calculateVideoLength(self, frameZip):
        totalFrames = frameZip.FRAMES

        if self.COMBINE:
            totalFrames = len(ListHelper.chunkList(ListHelper.rangeList(totalFrames), self.COMBINE_SIZE))

        ret = int(totalFrames / self.FRAMERATE * 1000)

        if self.PPROLL:
            ret += self.PPROLL_PRE_DURATION
            ret += self.PPROLL_POST_DURATION

        return ret

    def calculateTotalFrames(self, frameZip, includePPRoll=True):
        totalFrames = frameZip.FRAMES

        if self.COMBINE:
            totalFrames = len(ListHelper.chunkList(ListHelper.rangeList(totalFrames), self.COMBINE_SIZE))

        if (self.INTERPOLATE):
            totalFrames *= (self.INTERPOLATE_FRAMERATE / self.FRAMERATE)
            totalFrames = ceil(totalFrames)

        if includePPRoll:
            totalFrames += self.getNumPPRollFramesPre()
            totalFrames += self.getNumPPRollFramesPost()

        return totalFrames

    def setJSON(self, d):
        if 'name' in d: self.NAME = d['name']
        if 'resize' in d: self.RESIZE = d['resize']
        if 'resizeW' in d: self.RESIZE_W = int(d['resizeW'])
        if 'resizeH' in d: self.RESIZE_H = int(d['resizeH'])
        if 'framerate' in d: self.FRAMERATE = int(d['framerate'])
        if 'interpolate' in d: self.INTERPOLATE = d['interpolate']
        if 'interpolateFramerate' in d: self.INTERPOLATE_FRAMERATE = int(d['interpolateFramerate'])
        if 'interpolateMode' in d:  self.INTERPOLATE_MODE = d['interpolateMode']
        if 'interpolateEstimation' in d:  self.INTERPOLATE_ESTIMATION = d['interpolateEstimation']
        if 'interpolateCompensation' in d: self.INTERPOLATE_COMPENSATION = d['interpolateCompensation']
        if 'interpolateAlgorithm' in d: self.INTERPOLATE_ALGORITHM = d['interpolateAlgorithm']
        if 'fade' in d: self.FADE = d['fade']
        if 'fadeInDuration' in d: self.FADE_IN_DURATION = int(d['fadeInDuration'])
        if 'fadeOutDuration' in d: self.FADE_OUT_DURATION = int(d['fadeOutDuration'])
        if 'fadeColor' in d:
            colStr = d['fadeColor']
            if ColorHelper.isHexColor(colStr):
                self.FADE_COLOR = colStr
            else:
                self.FADE_COLOR = ColorHelper.cssColorToHex(colStr)
        if 'combine' in d: self.COMBINE = d['combine']
        if 'combineSize' in d: self.COMBINE_SIZE = int(d['combineSize'])
        if 'combineMethod' in d: self.COMBINE_METHOD = CombineMethod[d['combineMethod']]
        if 'ppRoll' in d: self.PPROLL = d['ppRoll']
        if 'ppRollPreDuration' in d: self.PPROLL_PRE_DURATION = int(d['ppRollPreDuration'])
        if 'ppRollPostDuration' in d: self.PPROLL_POST_DURATION = int(d['ppRollPostDuration'])
        if 'ppRollPreType' in d: self.PPROLL_PRE_TYPE = PPRollType[d['ppRollPreType']]
        if 'ppRollPostType' in d: self.PPROLL_POST_TYPE = PPRollType[d['ppRollPostType']]
        if 'ppRollPreEaseFn' in d: self.PPROLL_PRE_EASE_FN = PPRollEaseFn[d['ppRollPreEaseFn']]
        if 'ppRollPostEaseFn' in d: self.PPROLL_POST_EASE_FN = PPRollEaseFn[d['ppRollPostEaseFn']]
        if 'ppRollPreBlur' in d: self.PPROLL_PRE_BLUR = d['ppRollPreBlur']
        if 'ppRollPostBlur' in d: self.PPROLL_POST_BLUR = d['ppRollPostBlur']
        if 'ppRollBlurRadius' in d: self.PPROLL_BLUR_RADIUS = int(d['ppRollBlurRadius'])
        if 'ppRollPreZoom' in d: self.PPROLL_PRE_ZOOM = d['ppRollPreZoom']
        if 'ppRollPostZoom' in d: self.PPROLL_POST_ZOOM = d['ppRollPostZoom']
        if 'ppRollZoomFactor' in d: self.PPROLL_ZOOM_FACTOR = float(d['ppRollZoomFactor'])
        if 'ppRollText' in d: self.PPROLL_TEXT = d['ppRollText']
        if 'ppRollTextSize' in d: self.PPROLL_TEXT_SIZE = int(d['ppRollTextSize'])
        if 'ppRollTextForeground' in d: self.PPROLL_TEXT_FOREGROUND = d['ppRollTextForeground']
        if 'ppRollTextBackground' in d: self.PPROLL_TEXT_BACKGROUND = d['ppRollTextBackground']
        if 'ppRollTextRegex' in d: self.PPROLL_TEXT_REGEX = d['ppRollTextRegex']

    def getJSON(self):
        return dict(
            name=self.NAME,
            resize=self.RESIZE,
            resizeW=self.RESIZE_W,
            resizeH=self.RESIZE_H,
            framerate=self.FRAMERATE,
            interpolate=self.INTERPOLATE,
            interpolateFramerate=self.INTERPOLATE_FRAMERATE,
            interpolateMode=self.INTERPOLATE_MODE,
            interpolateEstimation=self.INTERPOLATE_ESTIMATION,
            interpolateCompensation=self.INTERPOLATE_COMPENSATION,
            interpolateAlgorithm=self.INTERPOLATE_ALGORITHM,
            fade=self.FADE,
            fadeInDuration=self.FADE_IN_DURATION,
            fadeOutDuration=self.FADE_OUT_DURATION,
            fadeColor=self.FADE_COLOR,
            combine=self.COMBINE,
            combineSize=self.COMBINE_SIZE,
            combineMethod=self.COMBINE_METHOD.name,
            ppRoll=self.PPROLL,
            ppRollPreDuration=self.PPROLL_PRE_DURATION,
            ppRollPostDuration=self.PPROLL_POST_DURATION,
            ppRollPreType=self.PPROLL_PRE_TYPE.name,
            ppRollPostType=self.PPROLL_POST_TYPE.name,
            ppRollPreEaseFn=self.PPROLL_PRE_EASE_FN.name,
            ppRollPostEaseFn=self.PPROLL_POST_EASE_FN.name,
            ppRollPreBlur=self.PPROLL_PRE_BLUR,
            ppRollPostBlur=self.PPROLL_POST_BLUR,
            ppRollBlurRadius=self.PPROLL_BLUR_RADIUS,
            ppRollPreZoom=self.PPROLL_PRE_ZOOM,
            ppRollPostZoom=self.PPROLL_POST_ZOOM,
            ppRollZoomFactor=self.PPROLL_ZOOM_FACTOR,
            ppRollText=self.PPROLL_TEXT,
            ppRollTextSize=self.PPROLL_TEXT_SIZE,
            ppRollTextForeground=self.PPROLL_TEXT_FOREGROUND,
            ppRollTextBackground=self.PPROLL_TEXT_BACKGROUND,
            ppRollTextRegex=self.PPROLL_TEXT_REGEX
        )
