import base64
import glob
import io
import os
import re
import shutil
import subprocess
import zipfile
from datetime import datetime
from threading import Thread

from PIL import Image, ImageFilter, ImageOps, ImageEnhance

from .enhancementPreset import EnhancementPreset
from .renderPreset import RenderPreset
from .renderJobState import RenderJobState


class RenderJob:
    def __init__(self, frameZip, parent, logger, settings, dataFolder, enhancementPreset=None, renderPreset=None):
        self.ID = parent.getRandomString(8)
        self.PARENT = parent
        self._settings = settings
        self._logger = logger

        self.FRAMEZIP = frameZip

        self.BASE_NAME = os.path.splitext(os.path.basename(frameZip.PATH))[0]
        self.FOLDER = ''
        self.FOLDER_NAME = ''
        self.RUNNING = False
        self.THREAD = None
        self.PROGRESS = 0

        self.ENHANCEMENT_PRESET = enhancementPreset
        self.RENDER_PRESET = renderPreset

        if self.ENHANCEMENT_PRESET is None:
            epRaw = self._settings.get(["enhancementPresets"])
            epList = list(map(lambda x: EnhancementPreset(parent, x), epRaw))
            self.ENHANCEMENT_PRESET = epList[0]

        if self.RENDER_PRESET is None:
            rpRaw = self._settings.get(["renderPresets"])
            rpList = list(map(lambda x: RenderPreset(x), rpRaw))
            self.RENDER_PRESET = rpList[0]

        self.createFolder(dataFolder)

        self.STATE = None
        self.setState(RenderJobState.WAITING)

    def setState(self, state):
        self.STATE = state
        self.PROGRESS = 0
        self.PARENT.renderJobStateChanged(self, state)

    def setProgress(self, progress):
        self.PROGRESS = progress
        self.PARENT.renderJobProgressChanged(self, progress)

    def getJSON(self):
        return dict(
            id=self.ID,
            name=self.BASE_NAME,
            state=self.STATE.name,
            running=self.RUNNING,
            progress=self.PROGRESS * 100
        )

    def start(self):
        self.RUNNING = True
        self.THREAD = Thread(target=self.renderTimelapse)
        self.THREAD.start()

    def createFolder(self, dataFolder):
        self.FOLDER_NAME = self.PARENT.getRandomString(16)
        self.FOLDER = dataFolder + '/render/' + self.FOLDER_NAME
        os.makedirs(os.path.dirname(os.path.abspath(self.FOLDER)), exist_ok=True)

    def extractZip(self):
        self.setState(RenderJobState.EXTRACTING)
        with zipfile.ZipFile(self.FRAMEZIP.PATH, "r") as zip_ref:
            zip_ref.extractall(self.FOLDER)

    def blurImages(self, preset):
        if not preset.BLUR:
            return

        self.setState(RenderJobState.BLURRING)

        imgMask = Image.open(preset.BLUR_MASK.PATH).convert('L')
        frameFiles = glob.glob(self.FOLDER + '/*.jpg')
        for i, frame in enumerate(frameFiles):
            img = Image.open(frame)

            if img.width != imgMask.width or img.height != imgMask.height:
                imgMask = imgMask.resize((img.width, img.height), resample=Image.LANCZOS)

            imgBlurred = img.filter(ImageFilter.GaussianBlur(preset.BLUR_RADIUS))
            imgOut = Image.composite(imgBlurred, img, imgMask)
            imgOut.save(frame, quality=100, subsampling=0)
            self.setProgress((i + 1) / len(frameFiles))

    def enhanceImages(self, preset):
        if not preset.ENHANCE:
            return

        self.setState(RenderJobState.ENHANCING)
        frameFiles = glob.glob(self.FOLDER + '/*.jpg')
        for i, frame in enumerate(frameFiles):
            img = Image.open(frame)
            img = ImageEnhance.Brightness(img).enhance(preset.BRIGHTNESS)
            img = ImageEnhance.Contrast(img).enhance(preset.CONTRAST)
            if preset.EQUALIZE:
                img = ImageOps.equalize(img)
            # img = ImageOps.autocontrast(img)
            img.save(frame, quality=100, subsampling=0)
            self.setProgress((i + 1) / len(frameFiles))

    def resizeImages(self, preset):
        if not preset.RESIZE:
            return

        self.setState(RenderJobState.RESIZING)
        frameFiles = glob.glob(self.FOLDER + '/*.jpg')
        for i, frame in enumerate(frameFiles):
            img = Image.open(frame)
            img = img.resize((preset.RESIZE_W, preset.RESIZE_H), resample=Image.LANCZOS)
            img.save(frame, quality=100, subsampling=0)
            self.setProgress((i + 1) / len(frameFiles))

    def createVideo(self, preset):
        self.setState(RenderJobState.RENDERING)

        timePart = datetime.now().strftime("%d%m%Y%H%M%S")
        videoFile = self._settings.getBaseFolder('timelapse') + '/' + self.BASE_NAME + '_' + timePart + '.mp4'
        totalFrames = self.FRAMEZIP.FRAMES

        cmd = [self._settings.global_get(["webcam", "ffmpeg"]), '-y']
        cmd += ['-framerate', str(preset.FRAMERATE), '-i', '%05d.jpg']

        if preset.INTERPOLATE:
            cmd += ['-r', str(preset.INTERPOLATE_FRAMERATE)]
            miStr = 'minterpolate=fps=' + str(preset.INTERPOLATE_FRAMERATE) + \
                    ':mi_mode=' + preset.INTERPOLATE_MODE + \
                    ':me_mode=' + preset.INTERPOLATE_ESTIMATION + \
                    ':mc_mode=' + preset.INTERPOLATE_COMPENSATION + \
                    ':me=' + preset.INTERPOLATE_ALGORITHM
            cmd += ['-vf', miStr]
            totalFrames *= (preset.INTERPOLATE_FRAMERATE / preset.FRAMERATE)
        else:
            cmd += ['-r', str(preset.FRAMERATE)]

        cmd += ['-c:v', 'libx264', '-movflags', 'faststart', 'out.mp4']
        cmd += ["-hide_banner", "-loglevel", 'verbose', "-progress", "pipe:1", "-nostats"]
        process = subprocess.Popen(cmd, cwd=self.FOLDER, stdout=subprocess.PIPE)

        while process.poll() is None:
            line = process.stdout.readline().decode()
            m = re.search('^frame=([0-9]+)', line)
            if m:
                frame = int(m.groups()[0])
                p = frame / totalFrames
                self.setProgress(p)

        if process.returncode != 0:
            raise Exception("FFMPEG Return Code != 0")

        shutil.move(self.FOLDER + '/out.mp4', videoFile)

        frameFiles = glob.glob(self.FOLDER + '/*.jpg')
        thumbImg = Image.open(frameFiles[-1])
        thumbImg.save(videoFile + '.thumb.jpg', quality=50)

    def renderTimelapse(self):
        isSuccess = False
        try:
            self.extractZip()
            self.enhanceImages(self.ENHANCEMENT_PRESET)
            self.blurImages(self.ENHANCEMENT_PRESET)
            self.resizeImages(self.ENHANCEMENT_PRESET)
            self.createVideo(self.RENDER_PRESET)
            isSuccess = True
        finally:
            shutil.rmtree(self.FOLDER)
            self.RUNNING = False

            if isSuccess:
                self.setState(RenderJobState.FINISHED)
            else:
                self.setState(RenderJobState.FAILED)
