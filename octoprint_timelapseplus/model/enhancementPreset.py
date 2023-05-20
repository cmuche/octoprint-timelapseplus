from .borderSnap import BorderSnap
from .mask import Mask
from PIL import Image, ImageFilter, ImageOps, ImageEnhance

from .timecodeType import TimecodeType


class EnhancementPreset:
    def __init__(self, parent, d=None):
        self.NAME = 'Default Enhancement Preset'
        self.ENHANCE = False
        self.EQUALIZE = False
        self.BRIGHTNESS = 1
        self.CONTRAST = 1
        self.BLUR = False
        self.BLUR_RADIUS = 30
        self.BLUR_MASK = None
        self.RESIZE = False
        self.RESIZE_W = 1280
        self.RESIZE_H = 720
        self.TIMECODE = True
        self.TIMECODE_SNAP = BorderSnap.BOTTOM_LEFT
        self.TIMECODE_SIZE = 3
        self.TIMECODE_MARGIN = 5
        self.TIMECODE_TYPE = TimecodeType.BAR
        self.TIMECODE_COLOR_PRIMARY = '#FF0000'
        self.TIMECODE_COLOR_SECONDARY = '#0000FF'

        if d is not None:
            self.setJSON(parent, d)

    def applyBlur(self, img):
        if not self.BLUR:
            return img

        if self.BLUR_MASK is None:
            raise Exception('Blur Mask is not set')

        imgMask = Image.open(self.BLUR_MASK.PATH).convert('L')
        if img.width != imgMask.width or img.height != imgMask.height:
            imgMask = imgMask.resize((img.width, img.height), resample=Image.LANCZOS)

        imgBlurred = img.filter(ImageFilter.GaussianBlur(self.BLUR_RADIUS))
        imgOut = Image.composite(imgBlurred, img, imgMask)
        return imgOut

    def applyEnhance(self, img):
        if not self.ENHANCE:
            return img

        img = ImageEnhance.Brightness(img).enhance(self.BRIGHTNESS)
        img = ImageEnhance.Contrast(img).enhance(self.CONTRAST)
        if self.EQUALIZE:
            img = ImageOps.equalize(img)
        # img = ImageOps.autocontrast(img)
        return img

    def applyResize(self, img):
        if not self.RESIZE:
            return img

        img = img.resize((self.RESIZE_W, self.RESIZE_H), resample=Image.LANCZOS)
        return img

    def setJSON(self, parent, d):
        if 'name' in d: self.NAME = d['name']
        if 'enhance' in d: self.ENHANCE = d['enhance']
        if 'equalize' in d: self.EQUALIZE = d['equalize']
        if 'brightness' in d: self.BRIGHTNESS = float(d['brightness'])
        if 'contrast' in d: self.CONTRAST = float(d['contrast'])
        if 'blur' in d: self.BLUR = d['blur']
        if 'blurRadius' in d: self.BLUR_RADIUS = int(d['blurRadius'])

        if 'blurMask' in d:
            bmId = d['blurMask']

            if bmId is not None:
                self.BLUR_MASK = Mask(parent, parent._data_folder, bmId)

        if 'resize' in d: self.RESIZE = d['resize']
        if 'resizeW' in d: self.RESIZE_W = int(d['resizeW'])
        if 'resizeH' in d: self.RESIZE_H = int(d['resizeH'])

    def getJSON(self):
        d = dict(
            name=self.NAME,
            enhance=self.ENHANCE,
            equalize=self.EQUALIZE,
            brightness=self.BRIGHTNESS,
            contrast=self.CONTRAST,
            blur=self.BLUR,
            blurRadius=self.BLUR_RADIUS,
            blurMask=None,
            resize=self.RESIZE,
            resizeW=self.RESIZE_W,
            resizeH=self.RESIZE_H
        )

        if self.BLUR_MASK is not None:
            d['blurMask'] = self.BLUR_MASK.ID

        return d
