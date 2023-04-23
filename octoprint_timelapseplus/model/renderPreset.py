from math import ceil

from .combineMethod import CombineMethod
from ..helpers.listHelper import ListHelper


class RenderPreset:
    def __init__(self, d=None):
        self.NAME = 'Default Render Preset'
        self.FRAMERATE = 30
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

        if d is not None:
            self.setJSON(d)

    def calculateVideoLength(self, frameZip):
        totalFrames = frameZip.FRAMES

        if self.COMBINE:
            totalFrames = len(ListHelper.chunkList(ListHelper.rangeList(totalFrames), self.COMBINE_SIZE))

        return int(totalFrames / self.FRAMERATE * 1000)

    def calculateTotalFrames(self, frameZip):
        totalFrames = frameZip.FRAMES

        if self.COMBINE:
            totalFrames = len(ListHelper.chunkList(ListHelper.rangeList(totalFrames), self.COMBINE_SIZE))

        if (self.INTERPOLATE):
            totalFrames *= (self.INTERPOLATE_FRAMERATE / self.FRAMERATE)
            totalFrames = ceil(totalFrames)

        return totalFrames

    def setJSON(self, d):
        if 'name' in d: self.NAME = d['name']
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
        if 'fadeColor' in d: self.FADE_COLOR = d['fadeColor']
        if 'combine' in d: self.COMBINE = d['combine']
        if 'combineSize' in d: self.COMBINE_SIZE = int(d['combineSize'])
        if 'combineMethod' in d: self.COMBINE_METHOD = CombineMethod[d['combineMethod']]

    def getJSON(self):
        return dict(
            name=self.NAME,
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
            combineMethod=self.COMBINE_METHOD.name
        )
