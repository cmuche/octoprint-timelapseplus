import glob
import os
import re
import shutil
import subprocess
import time
import zipfile
from datetime import datetime
from threading import Thread

from PIL import Image

from .enhancementPreset import EnhancementPreset
from .renderJobState import RenderJobState
from .renderPreset import RenderPreset
from ..helpers.imageCombineHelper import ImageCombineHelper
from ..helpers.listHelper import ListHelper


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
        self.ERROR = None

        self.ETA = 0
        self._lastEtaStart = 0

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
        self.ETA = 0
        self._lastEtaStart = round(time.time() * 1000)
        self.PARENT.renderJobStateChanged(self, state)

    def setProgress(self, progress):
        self.PROGRESS = progress
        self.PARENT.renderJobProgressChanged(self, progress)

        if progress > 0:
            progressLeft = 1.0 - progress
            currentMillis = round(time.time() * 1000)
            elapsedMillis = currentMillis - self._lastEtaStart
            self.ETA = elapsedMillis / progress * progressLeft

    def getJSON(self):
        return dict(
            id=self.ID,
            name=self.BASE_NAME,
            state=self.STATE.name,
            running=self.RUNNING,
            progress=self.PROGRESS * 100,
            eta=self.ETA,
            enhancementPresetName=self.ENHANCEMENT_PRESET.NAME,
            renderPresetName=self.RENDER_PRESET.NAME
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

    def combineImages(self, preset):
        if not preset.COMBINE:
            return

        self.setState(RenderJobState.COMBINING)

        frameFiles = sorted(glob.glob(self.FOLDER + '/*.jpg'))
        chunks = ListHelper.chunkList(frameFiles, preset.COMBINE_SIZE)
        for i, chunk in enumerate(chunks):
            img = ImageCombineHelper.createCombinedImage(chunk, preset.COMBINE_METHOD)
            imgPath = self.FOLDER + '/' + "C_{:05d}".format(i + 1) + ".jpg"
            img.save(imgPath, quality=100, subsampling=0)

            for f in chunk:
                os.remove(f)

            self.setProgress((i + 1) / len(chunks))

    def blurImages(self, preset):
        if not preset.BLUR:
            return

        self.setState(RenderJobState.BLURRING)

        frameFiles = sorted(glob.glob(self.FOLDER + '/*.jpg'))
        for i, frame in enumerate(frameFiles):
            img = Image.open(frame)
            imgRes = preset.applyBlur(img)
            imgRes.save(frame, quality=100, subsampling=0)
            self.setProgress((i + 1) / len(frameFiles))

    def enhanceImages(self, preset):
        if not preset.ENHANCE:
            return

        self.setState(RenderJobState.ENHANCING)
        frameFiles = sorted(glob.glob(self.FOLDER + '/*.jpg'))
        for i, frame in enumerate(frameFiles):
            img = Image.open(frame)
            imgRes = preset.applyEnhance(img)
            imgRes.save(frame, quality=100, subsampling=0)
            self.setProgress((i + 1) / len(frameFiles))

    def resizeImages(self, preset):
        if not preset.RESIZE:
            return

        self.setState(RenderJobState.RESIZING)
        frameFiles = sorted(glob.glob(self.FOLDER + '/*.jpg'))
        for i, frame in enumerate(frameFiles):
            img = Image.open(frame)
            imgRes = preset.applyResize(img)
            imgRes.save(frame, quality=100, subsampling=0)
            self.setProgress((i + 1) / len(frameFiles))

    def createVideo(self, preset):
        self.setState(RenderJobState.RENDERING)

        timePart = datetime.now().strftime("%Y%m%d%H%M%S")
        videoFile = self._settings.getBaseFolder('timelapse') + '/' + self.BASE_NAME + '_' + timePart + '.mp4'
        totalFrames = preset.calculateTotalFrames(self.FRAMEZIP)

        framePattern = '%05d.jpg'
        if preset.COMBINE:
            framePattern = 'C_%05d.jpg'

        cmd = [self._settings.get(["ffmpegPath"]), '-y']
        cmd += ['-framerate', str(preset.FRAMERATE), '-i', framePattern]

        videoFilters = []

        if preset.INTERPOLATE:
            cmd += ['-r', str(preset.INTERPOLATE_FRAMERATE)]
            miStr = 'minterpolate=fps=' + str(preset.INTERPOLATE_FRAMERATE) + \
                    ':mi_mode=' + preset.INTERPOLATE_MODE + \
                    ':me_mode=' + preset.INTERPOLATE_ESTIMATION + \
                    ':mc_mode=' + preset.INTERPOLATE_COMPENSATION + \
                    ':me=' + preset.INTERPOLATE_ALGORITHM
            videoFilters += [miStr]
        else:
            cmd += ['-r', str(preset.FRAMERATE)]

        if preset.FADE:
            videoLength = preset.calculateVideoLength(self.FRAMEZIP)

            if preset.FADE_IN_DURATION > 0:
                fpInD = str(float(float(preset.FADE_IN_DURATION) / 1000))
                videoFilters += ['fade=t=in:st=0:d=' + fpInD + ':color=' + preset.FADE_COLOR]

            if preset.FADE_OUT_DURATION > 0:
                fpOutD = str(float(float(preset.FADE_OUT_DURATION) / 1000))
                fpOutSt = str(float(videoLength - preset.FADE_OUT_DURATION) / 1000)
                videoFilters += ['fade=t=out:st=' + fpOutSt + ':d=' + fpOutD + ':color=' + preset.FADE_COLOR]

        if len(videoFilters):
            cmd += ['-vf', ','.join(videoFilters)]

        cmd += ['-c:v', 'libx264', '-movflags', '+faststart', 'out.mp4']
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
        thumbImg.save(videoFile + '.thumb.jpg', quality=75)

    def renderTimelapse(self):
        try:
            self.extractZip()
            self.enhanceImages(self.ENHANCEMENT_PRESET)
            self.blurImages(self.ENHANCEMENT_PRESET)
            self.resizeImages(self.ENHANCEMENT_PRESET)
            self.combineImages(self.RENDER_PRESET)
            self.createVideo(self.RENDER_PRESET)

            self.setState(RenderJobState.FINISHED)
        except Exception as e:
            self.ERROR = str(e)
            self.setState(RenderJobState.FAILED)
            raise e
        finally:
            self.RUNNING = False
            shutil.rmtree(self.FOLDER)
