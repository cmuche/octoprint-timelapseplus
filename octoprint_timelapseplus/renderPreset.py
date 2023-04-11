class RenderPreset:
    def __init__(self, d=None):
        self.NAME = 'Render Preset'
        self.FRAMERATE = 30
        self.INTERPOLATE = False
        self.INTERPOLATE_FRAMERATE = 60
        self.INTERPOLATE_MODE = 'mci'  # 'blend'
        self.INTERPOLATE_ESTIMATION = 'bidir'
        self.INTERPOLATE_COMPENSATION = 'aobmc'

        if d is not None:
            self.setJSON(d)

    def setJSON(self, d):
        self.NAME = d['name']
        self.FRAMERATE = int(d['framerate'])
        self.INTERPOLATE = d['interpolate']
        self.INTERPOLATE_FRAMERATE = int(d['interpolateFramerate'])
        self.INTERPOLATE_MODE = d['interpolateMode']
        self.INTERPOLATE_ESTIMATION = d['interpolateEstimation']
        self.INTERPOLATE_COMPENSATION = d['interpolateCompensation']

    def getJSON(self):
        return dict(
            name=self.NAME,
            framerate=self.FRAMERATE,
            interpolate=self.INTERPOLATE,
            interpolateFramerate=self.INTERPOLATE_FRAMERATE,
            interpolateMode=self.INTERPOLATE_MODE,
            interpolateEstimation=self.INTERPOLATE_ESTIMATION,
            interpolateCompensation=self.INTERPOLATE_COMPENSATION
        )
