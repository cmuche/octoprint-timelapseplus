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

        if d is not None:
            self.setJSON(d)

    def calculateVideoLength(self, frameZip):
        return frameZip.FRAMES / self.FRAMERATE;

    def calculateTotalFrames(self, frameZip):
        totalFrames = frameZip.FRAMES
        if(self.INTERPOLATE):
            totalFrames *= (self.INTERPOLATE_FRAMERATE / self.FRAMERATE)
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

    def getJSON(self):
        return dict(
            name=self.NAME,
            framerate=self.FRAMERATE,
            interpolate=self.INTERPOLATE,
            interpolateFramerate=self.INTERPOLATE_FRAMERATE,
            interpolateMode=self.INTERPOLATE_MODE,
            interpolateEstimation=self.INTERPOLATE_ESTIMATION,
            interpolateCompensation=self.INTERPOLATE_COMPENSATION,
            interpolateAlgorithm=self.INTERPOLATE_ALGORITHM
        )
