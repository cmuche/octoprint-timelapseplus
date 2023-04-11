class EnhancementPreset:
    def __init__(self, d=None):
        self.NAME = 'Default Enhancement Preset'
        self.ENHANCE = False
        self.EQUALIZE = False
        self.BRIGHTNESS = 1
        self.CONTRAST = 1
        self.BLUR = False
        self.BLUR_RADIUS = 30
        self.RESIZE = False
        self.RESIZE_W = 1280
        self.RESIZE_H = 720

        if d is not None:
            self.setJSON(d)

    def setJSON(self, d):
        self.NAME = d['name']
        self.ENHANCE = d['enhance']
        self.EQUALIZE = d['equalize']
        self.BRIGHTNESS = float(d['brightness'])
        self.CONTRAST = float(d['contrast'])
        self.BLUR = d['blur']
        self.BLUR_RADIUS = int(d['blurRadius'])
        self.RESIZE = d['resize']
        self.RESIZE_W = int(d['resizeW'])
        self.RESIZE_H = int(d['resizeH'])

    def getJSON(self):
        return dict(
            name=self.NAME,
            enhance=self.ENHANCE,
            equalize=self.EQUALIZE,
            brightness=self.BRIGHTNESS,
            contrast=self.CONTRAST,
            blur=self.BLUR,
            blurRadius=self.BLUR_RADIUS,
            resize=self.RESIZE,
            resizeW=self.RESIZE_W,
            resizeH=self.RESIZE_H
        )
