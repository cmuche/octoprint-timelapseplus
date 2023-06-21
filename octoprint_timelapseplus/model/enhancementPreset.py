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

        self.TIMECODE = False
        self.TIMECODE_SNAP = BorderSnap.BOTTOM_RIGHT
        self.TIMECODE_SIZE = 15
        self.TIMECODE_MARGIN = 5
        self.TIMECODE_TYPE = TimecodeType.PRINTTIME_HMS
        self.TIMECODE_COLOR_PRIMARY = '#FFFFFF'
        self.TIMECODE_COLOR_SECONDARY = '#000000'

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

        imgBlurred.close()
        imgMask.close()

        return imgOut

    def applyEnhance(self, img):
        if not self.ENHANCE:
            return img

        if self.BRIGHTNESS != 1:
            img = ImageEnhance.Brightness(img).enhance(self.BRIGHTNESS)

        if self.CONTRAST != 1:
            img = ImageEnhance.Contrast(img).enhance(self.CONTRAST)

        if self.EQUALIZE:
            img = ImageOps.equalize(img)
                l_channel, a_channel, b_channel = imgLab.split()
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

        if 'timecode' in d: self.TIMECODE = d['timecode']
        if 'timecodeSnap' in d: self.TIMECODE_SNAP = BorderSnap[d['timecodeSnap']]
        if 'timecodeSize' in d: self.TIMECODE_SIZE = int(d['timecodeSize'])
        if 'timecodeMargin' in d: self.TIMECODE_MARGIN = int(d['timecodeMargin'])
        if 'timecodeType' in d: self.TIMECODE_TYPE = TimecodeType[d['timecodeType']]
        if 'timecodeColorPrimary' in d: self.TIMECODE_COLOR_PRIMARY = d['timecodeColorPrimary']
        if 'timecodeColorSecondary' in d: self.TIMECODE_COLOR_SECONDARY = d['timecodeColorSecondary']

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
            timecode=self.TIMECODE,
            timecodeSnap=self.TIMECODE_SNAP.name,
            timecodeSize=self.TIMECODE_SIZE,
            timecodeMargin=self.TIMECODE_MARGIN,
            timecodeType=self.TIMECODE_TYPE.name,
            timecodeColorPrimary=self.TIMECODE_COLOR_PRIMARY,
            timecodeColorSecondary=self.TIMECODE_COLOR_SECONDARY
        )

        if self.BLUR_MASK is not None:
            d['blurMask'] = self.BLUR_MASK.ID

        return d
