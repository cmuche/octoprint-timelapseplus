import glob
import json
import os
import re
import shutil
import subprocess
import time
import zipfile
from datetime import datetime
from threading import Thread

from PIL import Image

from .frameTimecodeInfo import FrameTimecodeInfo
from .enhancementPreset import EnhancementPreset
from .ppRollPhase import PPRollPhase
from .renderJobState import RenderJobState
from .renderPreset import RenderPreset
from ..helpers.colorHelper import ColorHelper
from ..helpers.fileHelper import FileHelper
from ..helpers.formatHelper import FormatHelper
from ..helpers.imageCombineHelper import ImageCombineHelper
from ..helpers.listHelper import ListHelper
from ..helpers.ppRollRenderer import PPRollRenderer
from ..helpers.timecodeRenderer import TimecodeRenderer


class RenderJob:
    def __init__(self, baseFolder, frameZip, parent, logger, settings, dataFolder, enhancementPreset=None, renderPreset=None, videoFormat=None):
        self.ID = parent.getRandomString(8)
        self.PARENT = parent
        self._settings = settings
        self._logger = logger
        self._basefolder = baseFolder

        self.FRAMEZIP = frameZip
        self.METADATA = None

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
        self.VIDEO_FORMAT = videoFormat

        if self.ENHANCEMENT_PRESET is None:
            epRaw = self._settings.get(["enhancementPresets"])
            epList = list(map(lambda x: EnhancementPreset(parent, x), epRaw))
            self.ENHANCEMENT_PRESET = epList[0]

        if self.RENDER_PRESET is None:
            rpRaw = self._settings.get(["renderPresets"])
            rpList = list(map(lambda x: RenderPreset(x), rpRaw))
            self.RENDER_PRESET = rpList[0]

        if self.VIDEO_FORMAT is None:
            defaultFormatId = self._settings.get(["defaultVideoFormat"])
            self.VIDEO_FORMAT = FormatHelper.getVideoFormatById(defaultFormatId)

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
        self.THREAD = Thread(target=self.startPipeline, daemon=True)
        self.THREAD.start()

    def createFolder(self, dataFolder):
        self.FOLDER_NAME = self.PARENT.getRandomString(16)
        self.FOLDER = dataFolder + '/render/' + self.FOLDER_NAME
        os.makedirs(os.path.dirname(os.path.abspath(self.FOLDER)), exist_ok=True)

    def extractZip(self):
        self.setState(RenderJobState.EXTRACTING)
        with zipfile.ZipFile(self.FRAMEZIP.PATH, "r") as zip_ref:
            zip_ref.extractall(self.FOLDER)

        metadataFile = self.FOLDER + '/' + FileHelper.METADATA_FILE_NAME
        if os.path.isfile(metadataFile):
            with open(metadataFile, 'r') as mdFile:
                self.METADATA = json.load(mdFile)

    def combineImages(self, preset):
        if not preset.COMBINE:
            return

        self.setState(RenderJobState.COMBINING)

        frameFiles = sorted(glob.glob(self.FOLDER + '/[!PPROLL]*.jpg'))
        chunks = ListHelper.chunkList(frameFiles, preset.COMBINE_SIZE)
        for i, chunk in enumerate(chunks):
            img = ImageCombineHelper.createCombinedImage(chunk, preset.COMBINE_METHOD)
            imgName = "C_{:05d}".format(i + 1) + ".jpg"
            imgPath = self.FOLDER + '/' + imgName
            img.save(imgPath, quality=100, subsampling=0)

            for f in chunk:
                os.remove(f)

            if self.METADATA is not None:
                self.METADATA['timestamps'][imgName] = self.METADATA['timestamps'][os.path.basename(chunk[-1])]

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

    def addTimecodes(self, preset):
        if not preset.TIMECODE:
            return

        if self.METADATA is None:
            self.PARENT.sendClientPopup('warning', 'No Timecode Data', 'The Frame Collection doesn\'t contain any Metadata. Timecode Genreation will be skipped.')
            return

        self.setState(RenderJobState.ADDING_TIMECODES)
        timecodeRenderer = TimecodeRenderer(self._basefolder)

        frameFiles = sorted(glob.glob(self.FOLDER + '/[!PPROLL]*.jpg'))
        for i, frame in enumerate(frameFiles):
            frameInfo = FrameTimecodeInfo(self.METADATA['timestamps'][os.path.basename(frame)], self.METADATA['started'], self.METADATA['ended'])
            img = Image.open(frame)
            imgRes = timecodeRenderer.applyTimecode(img, preset, frameInfo)
            imgRes.save(frame, quality=100, subsampling=0)
            self.setProgress((i + 1) / len(frameFiles))

    def createPPRoll(self, preset):
        if not preset.PPROLL:
            return

        self.setState(RenderJobState.GENERATING_PPROLL)
        frameFiles = sorted(glob.glob(self.FOLDER + '/*.jpg'))
        numFramesPre = preset.getNumPPRollFramesPre()
        numFramesPost = preset.getNumPPRollFramesPost()
        currentProgress = 0

        for i in ListHelper.rangeList(numFramesPre):
            thisRatio = i / numFramesPre
            thisOutFile = self.FOLDER + '/' + "PPROLL_PRE_{:05d}".format(i) + ".jpg"
            img = PPRollRenderer.renderFrame(thisRatio, frameFiles, preset, PPRollPhase.PRE, self.METADATA, self._basefolder)
            img.save(thisOutFile, quality=100, subsampling=0)

            currentProgress += 1
            self.setProgress(currentProgress / (numFramesPre + numFramesPost))

        for i in ListHelper.rangeList(numFramesPost):
            thisRatio = i / numFramesPost
            thisOutFile = self.FOLDER + '/' + "PPROLL_POST_{:05d}".format(i) + ".jpg"
            img = PPRollRenderer.renderFrame(thisRatio, frameFiles, preset, PPRollPhase.POST, self.METADATA, self._basefolder)
            img.save(thisOutFile, quality=100, subsampling=0)

            currentProgress += 1
            self.setProgress(currentProgress / (numFramesPre + numFramesPost))

    def generateFade(self, preset):
        if not preset.FADE:
            return

        self.setState(RenderJobState.APPLYING_FADE)
        frameFiles = self.getAllFinalFrames()

        fadeJobs = []
        fadeInFrameCount = int(preset.FADE_IN_DURATION / 1000 * preset.getFinalFramerate())
        fadeOutFrameCount = int(preset.FADE_OUT_DURATION / 1000 * preset.getFinalFramerate())

        if fadeInFrameCount > 0:
            fadeInElements = frameFiles[0:fadeInFrameCount]
            for i, element in enumerate(fadeInElements):
                r = 1 - i / len(fadeInElements)
                fadeJobs.append((r, element))

        if fadeOutFrameCount > 0:
            fadeOutElements = frameFiles[-fadeOutFrameCount:]
            for i, element in enumerate(fadeOutElements):
                r = (i + 1) / len(fadeOutElements)
                fadeJobs.append((r, element))

        for i, j in enumerate(fadeJobs):
            col = ColorHelper.hexToRgba(preset.FADE_COLOR, j[0])
            img = Image.open(j[1]).convert('RGBA')
            overlay = Image.new("RGBA", img.size, col)
            img = Image.alpha_composite(img, overlay).convert('RGB')
            img.save(j[1], quality=100, subsampling=0)
            overlay.close()
            self.setProgress((i + 1) / len(fadeJobs))

    def createPalette(self, format):
        if not format.CREATE_PALETTE:
            return

        self.setState(RenderJobState.CREATE_PALETTE)

        cmd = ['-i', 'E_%05d.jpg', '-filter_complex', '[0:v]palettegen', 'palette.png']
        self.runFfmpegWithProgress(cmd)

    def render(self, preset):
        framePattern = '%05d.jpg'
        if preset.COMBINE:
            framePattern = 'C_%05d.jpg'

        # TODO Skip Rendering if there is no interpolation or one step further: Introduce this as an Interpolation Phase

        self.setState(RenderJobState.RENDERING)

        cmd = ['-framerate', str(preset.FRAMERATE), '-i', framePattern]

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

        if len(videoFilters):
            cmd += ['-vf', ','.join(videoFilters)]

        cmd += ['-qscale:v', '1', 'F_%05d.jpg']
        self.runFfmpegWithProgress(cmd, preset.calculateTotalFrames(self.FRAMEZIP, False))

    def getAllFinalFrames(self):
        framesPPPre = sorted(glob.glob(self.FOLDER + '/PPROLL_PRE_*.jpg'))
        framesPPPost = sorted(glob.glob(self.FOLDER + '/PPROLL_POST_*.jpg'))
        framesFinal = sorted(glob.glob(self.FOLDER + '/F_*.jpg'))
        framesAll = framesPPPre + framesFinal + framesPPPost
        return framesAll

    def moveEncodeFrames(self):
        self.setState(RenderJobState.MERGING_FRAMES)
        framesAll = self.getAllFinalFrames()

        for i, f in enumerate(framesAll):
            eName = "E_{:05d}".format(i + 1) + ".jpg"
            shutil.move(f, self.FOLDER + '/' + eName)

    def encode(self, preset):
        self.setState(RenderJobState.ENCODING)

        timePart = datetime.now().strftime("%Y%m%d%H%M%S")
        videoFile = self._settings.getBaseFolder('timelapse') + '/' + self.BASE_NAME + '_' + timePart + '.' + self.VIDEO_FORMAT.EXTENSION
        outFileName = 'out.' + self.VIDEO_FORMAT.EXTENSION

        cmd = ['-framerate', str(self.RENDER_PRESET.getFinalFramerate()), '-i', 'E_%05d.jpg', '-r', str(self.RENDER_PRESET.getFinalFramerate())]
        cmd += self.VIDEO_FORMAT.getRenderArgs()
        cmd += [outFileName]

        self.runFfmpegWithProgress(cmd, preset.calculateTotalFrames(self.FRAMEZIP))

        shutil.move(self.FOLDER + '/' + outFileName, videoFile)
        frameFiles = glob.glob(self.FOLDER + '/E_*.jpg')
        thumbImg = Image.open(frameFiles[int(len(frameFiles) / 1.5)])
        thumbImg.save(videoFile + '.thumb.jpg', quality=75)

    def runFfmpegWithProgress(self, params, totalFrames=0):
        cmd = [self._settings.get(["ffmpegPath"]), '-y']
        cmd += params
        cmd += ['-hide_banner', '-loglevel', 'verbose', '-progress', 'pipe:1', '-nostats']
        process = subprocess.Popen(cmd, cwd=self.FOLDER, stdout=subprocess.PIPE)
        while process.poll() is None:
            line = process.stdout.readline().decode()
            m = re.search('^frame=([0-9]+)', line)
            if m and totalFrames > 0:
                frame = int(m.groups()[0])
                p = frame / totalFrames
                self.setProgress(p)

        if process.returncode != 0:
            raise Exception("Failed to run FFmpeg (Return Code " + str(process.returncode) + " )")

    def startPipeline(self):
        try:
            self.extractZip()
            self.enhanceImages(self.ENHANCEMENT_PRESET)
            self.blurImages(self.ENHANCEMENT_PRESET)
            self.createPPRoll(self.RENDER_PRESET)
            self.resizeImages(self.ENHANCEMENT_PRESET)
            self.combineImages(self.RENDER_PRESET)
            self.addTimecodes(self.ENHANCEMENT_PRESET)
            self.render(self.RENDER_PRESET)
            self.generateFade(self.RENDER_PRESET)
            self.moveEncodeFrames()
            self.createPalette(self.VIDEO_FORMAT)
            self.encode(self.RENDER_PRESET)

            self.setState(RenderJobState.FINISHED)
        except Exception as e:
            self.ERROR = str(e)
            self.setState(RenderJobState.FAILED)
            raise e
        finally:
            self.RUNNING = False
            shutil.rmtree(self.FOLDER)
