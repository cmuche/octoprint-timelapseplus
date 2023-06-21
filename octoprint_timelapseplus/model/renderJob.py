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

from PIL import Image, ImageEnhance

from .enhancementPreset import EnhancementPreset
from .frameTimecodeInfo import FrameTimecodeInfo
from .ppRollPhase import PPRollPhase
from .renderJobState import RenderJobState
from .renderPreset import RenderPreset
from ..helpers.colorHelper import ColorHelper
from ..helpers.fileHelper import FileHelper
from ..helpers.formatHelper import FormatHelper
from ..helpers.imageCombineHelper import ImageCombineHelper
from ..helpers.jobExecutor import JobExecutor
from ..helpers.listHelper import ListHelper
from ..helpers.ppRollRenderer import PPRollRenderer
from ..helpers.timecodeRenderer import TimecodeRenderer
from ..log import Log


class RenderJob:
    def __init__(self, baseFolder, frameZip, parent, settings, dataFolder, enhancementPreset=None, renderPreset=None, videoFormat=None):
        self.ID = parent.getRandomString(8)
        self.PARENT = parent
        self._settings = settings
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
        Log.debug('Render Job State changed to ' + state.name, {'id', self.ID})
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

        jobs = [(chunk, preset, i) for i, chunk in enumerate(chunks)]
        JobExecutor(self._settings, jobs, self.combineImagesInner, self.setProgress).start()

    def combineImagesInner(self, j):
        chunk, preset, i = j
        img = ImageCombineHelper.createCombinedImage(chunk, preset.COMBINE_METHOD)
        imgName = "C_{:05d}".format(i + 1) + ".jpg"
        imgPath = self.FOLDER + '/' + imgName
        img.save(imgPath, quality=100, subsampling=0)
        img.close()

        for f in chunk:
            os.remove(f)

        if self.METADATA is not None:
            self.METADATA['timestamps'][imgName] = self.METADATA['timestamps'][os.path.basename(chunk[-1])]

    def blurImages(self, preset):
        if not preset.BLUR:
            return

        self.setState(RenderJobState.BLURRING)

        frameFiles = sorted(glob.glob(self.FOLDER + '/*.jpg'))

        jobs = [(frame, preset) for frame in frameFiles]
        JobExecutor(self._settings, jobs, self.blurImagesInner, self.setProgress).start()

    def blurImagesInner(self, j):
        frame, preset = j
        img = Image.open(frame)
        imgRes = preset.applyBlur(img)
        imgRes.save(frame, quality=100, subsampling=0)
        imgRes.close()

    def enhanceImages(self, preset):
        if not preset.ENHANCE:
            return

        self.setState(RenderJobState.ENHANCING)
        frameFiles = sorted(glob.glob(self.FOLDER + '/*.jpg'))

        jobs = [(frame, preset) for frame in frameFiles]
        JobExecutor(self._settings, jobs, self.enhanceImagesInner, self.setProgress).start()

    def analyzeBrightnessAndContrast(self, image):
        grayscaleImage = image.convert('L')
        histogram = grayscaleImage.histogram()
        pixels = sum(histogram)
        brightness = sum(i * histogram[i] for i in range(256)) / pixels
        contrast = (sum((i - brightness) ** 2 * histogram[i] for i in range(256)) / pixels) ** 0.5
        grayscaleImage.close()
        return brightness, contrast

    def normalizeImages(self, preset):
        if not preset.NORMALIZE:
            return

        self.setState(RenderJobState.ANALYZING)
        frameFiles = sorted(glob.glob(self.FOLDER + '/*.jpg'))

        analyzedValues = {}
        jobs = [(frame, preset, analyzedValues) for frame in frameFiles]
        JobExecutor(jobs, self.analyzeImagesInner, self.setProgress).start()

        self.setState(RenderJobState.NORMALIZING)

        if len(analyzedValues.keys()) == 0:
            return

        targetBrightness = sum(analyzedValues[k][0] for k in analyzedValues.keys()) / len(analyzedValues.keys())
        targetContrast = sum(analyzedValues[k][1] for k in analyzedValues.keys()) / len(analyzedValues.keys())

        jobs = [(frame, preset, analyzedValues[frame], targetBrightness, targetContrast) for frame in frameFiles]
        JobExecutor(jobs, self.normalizeImagesInner, self.setProgress).start()

    def normalizeImagesInner(self, j):
        frame, preset, frameValues, targetBrightness, targetContrast = j

        img = Image.open(frame)

        frameBrightness = frameValues[0]

        factorBrightness = targetBrightness / frameBrightness
        enhancerBrightness = ImageEnhance.Brightness(img)
        imgRes1 = enhancerBrightness.enhance(factorBrightness)

        frameContrast = self.analyzeBrightnessAndContrast(imgRes1)[1]
        enhancerContrast = ImageEnhance.Contrast(imgRes1)
        factorContrast = targetContrast / frameContrast
        imgRes2 = enhancerContrast.enhance(factorContrast)

        imgRes2.save(frame, quality=100, subsampling=0)
        img.close()
        imgRes1.close()
        imgRes2.close()

    def analyzeImagesInner(self, j):
        frame, preset, analyzedValues = j
        img = Image.open(frame)

        brightness, contrast = self.analyzeBrightnessAndContrast(img)
        analyzedValues[frame] = (brightness, contrast)
        img.close()

    def enhanceImagesInner(self, j):
        frame, preset = j
        img = Image.open(frame)
        imgRes = preset.applyEnhance(img)
        imgRes.save(frame, quality=100, subsampling=0)
        imgRes.close()

    def resizeImages(self, preset):
        if not preset.RESIZE:
            return

        self.setState(RenderJobState.RESIZING)
        frameFiles = sorted(glob.glob(self.FOLDER + '/*.jpg'))

        jobs = [(frame, preset) for frame in frameFiles]
        JobExecutor(self._settings, jobs, self.resizeImagesInner, self.setProgress).start()

    def resizeImagesInner(self, j):
        frame, preset = j
        img = Image.open(frame)
        imgRes = preset.applyResize(img)
        imgRes.save(frame, quality=100, subsampling=0)
        imgRes.close()

    def addTimecodes(self, preset):
        if not preset.TIMECODE:
            return

        if self.METADATA is None:
            self.PARENT.sendClientPopup('warning', 'No Timecode Data', 'The Frame Collection doesn\'t contain any Metadata. Timecode Genreation will be skipped.')
            return

        self.setState(RenderJobState.ADDING_TIMECODES)
        timecodeRenderer = TimecodeRenderer(self._basefolder)

        frameFiles = sorted(glob.glob(self.FOLDER + '/[!PPROLL]*.jpg'))

        jobs = [(frame, timecodeRenderer, preset) for frame in frameFiles]
        JobExecutor(self._settings, jobs, self.addTimecodesInner, self.setProgress).start()

    def addTimecodesInner(self, j):
        frame, timecodeRenderer, preset = j
        frameInfo = FrameTimecodeInfo(self.METADATA['timestamps'][os.path.basename(frame)], self.METADATA['started'], self.METADATA['ended'])
        img = Image.open(frame)
        imgRes = timecodeRenderer.applyTimecode(img, preset, frameInfo)
        imgRes.save(frame, quality=100, subsampling=0)

        img.close()
        imgRes.close()

    def createPPRoll(self, preset):
        if not preset.PPROLL:
            return

        self.setState(RenderJobState.GENERATING_PPROLL)
        frameFiles = sorted(glob.glob(self.FOLDER + '/*.jpg'))
        numFramesPre = preset.getNumPPRollFramesPre()
        numFramesPost = preset.getNumPPRollFramesPost()

        jobs = []
        for i in ListHelper.rangeList(numFramesPre):
            thisRatio = i / numFramesPre
            thisOutFile = self.FOLDER + '/' + "PPROLL_PRE_{:05d}".format(i) + ".jpg"
            jobs.append((thisRatio, frameFiles, thisOutFile, preset, PPRollPhase.PRE))

        for i in ListHelper.rangeList(numFramesPost):
            thisRatio = i / numFramesPost
            thisOutFile = self.FOLDER + '/' + "PPROLL_POST_{:05d}".format(i) + ".jpg"
            jobs.append((thisRatio, frameFiles, thisOutFile, preset, PPRollPhase.POST))

        JobExecutor(self._settings, jobs, self.createPPRollInner, self.setProgress).start()

    def createPPRollInner(self, j):
        thisRatio, frameFiles, thisOutFile, preset, phase = j
        img = PPRollRenderer.renderFrame(thisRatio, frameFiles, preset, phase, self.METADATA, self._basefolder)
        img.save(thisOutFile, quality=100, subsampling=0)
        img.close()

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
                fadeJobs.append((r, element, preset.FADE_COLOR))

        if fadeOutFrameCount > 0:
            fadeOutElements = frameFiles[-fadeOutFrameCount:]
            for i, element in enumerate(fadeOutElements):
                r = (i + 1) / len(fadeOutElements)
                fadeJobs.append((r, element, preset.FADE_COLOR))

        JobExecutor(self._settings, fadeJobs, self.generateFadeInner, self.setProgress).start()

    def generateFadeInner(self, j):
        r, imgFile, fadeColor = j
        col = ColorHelper.hexToRgba(fadeColor, r)
        img = Image.open(imgFile).convert('RGBA')
        overlay = Image.new("RGBA", img.size, col)
        img = Image.alpha_composite(img, overlay).convert('RGB')
        img.save(imgFile, quality=100, subsampling=0)
        overlay.close()
        img.close()

    def createPalette(self, format):
        if not format.CREATE_PALETTE:
            return

        self.setState(RenderJobState.CREATE_PALETTE)

        cmd = ['-i', 'E_%05d.jpg', '-filter_complex', '[0:v]palettegen', 'palette.png']
        self.runFfmpegWithProgress(cmd)

    def interpolateOrMove(self, preset):
        if preset.INTERPOLATE:
            self.setState(RenderJobState.INTERPOLATING)

            framePattern = '%05d.jpg'
            if preset.COMBINE:
                framePattern = 'C_%05d.jpg'

            cmd = ['-framerate', str(preset.FRAMERATE), '-i', framePattern, '-r', str(self.RENDER_PRESET.getFinalFramerate())]
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
        else:
            self.setState(RenderJobState.MOVING_FRAMES)
            frames = sorted(glob.glob(self.FOLDER + '/[!PPROLL]*.jpg'))
            for i, f in enumerate(frames):
                fName = "F_{:05d}".format(i + 1) + ".jpg"
                shutil.move(f, self.FOLDER + '/' + fName)

    def getAllFinalFrames(self):
        framesPPPre = sorted(glob.glob(self.FOLDER + '/PPROLL_PRE_*.jpg'))
        framesPPPost = sorted(glob.glob(self.FOLDER + '/PPROLL_POST_*.jpg'))
        framesFinal = sorted(glob.glob(self.FOLDER + '/F_*.jpg'))
        framesAll = framesPPPre + framesFinal + framesPPPost
        return framesAll

    def moveEncodeFrames(self):
        self.setState(RenderJobState.MOVING_FRAMES)
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
        Log.debug('Executing FFmpeg', params)

        cmd = [self._settings.get(["ffmpegPath"]), '-y']
        cmd += params
        cmd += ['-hide_banner', '-loglevel', 'info', '-progress', 'pipe:1', '-nostats']
        process = subprocess.Popen(cmd, cwd=self.FOLDER, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        outLines = []
        while process.poll() is None:
            line = process.stdout.readline().decode()
            outLines += line.split('\n')

            m = re.search('^frame=([0-9]+)', line)
            if m and totalFrames > 0:
                frame = int(m.groups()[0])
                p = frame / totalFrames
                self.setProgress(p)

        outLines += process.stdout.read().decode().split('\n')
        outLines = [x.replace('\r', '').strip() for x in outLines]
        outLines = [x for x in outLines if x != '']

        if process.returncode != 0:
            for ol in outLines:
                Log.error(ol)

            raise Exception("Failed to run FFmpeg (Return Code " + str(process.returncode) + ")")

    def startPipeline(self):
        Log.info('Starting Rendering Pipeline', {'id': self.ID})
        Log.debug('Enhancement Preset', self.ENHANCEMENT_PRESET.getJSON())
        Log.debug('Render Preset', self.RENDER_PRESET.getJSON())
        Log.debug('Video Format', self.VIDEO_FORMAT.getJSON())

        try:
            self.extractZip()
            self.normalizeImages(self.ENHANCEMENT_PRESET)
            self.enhanceImages(self.ENHANCEMENT_PRESET)
            self.blurImages(self.ENHANCEMENT_PRESET)
            self.createPPRoll(self.RENDER_PRESET)
            self.resizeImages(self.RENDER_PRESET)
            self.combineImages(self.RENDER_PRESET)
            self.addTimecodes(self.ENHANCEMENT_PRESET)
            self.interpolateOrMove(self.RENDER_PRESET)
            self.generateFade(self.RENDER_PRESET)
            self.moveEncodeFrames()
            self.createPalette(self.VIDEO_FORMAT)
            self.encode(self.RENDER_PRESET)

            self.setState(RenderJobState.FINISHED)
        except Exception as e:
            Log.error('Render Job failed', e)
            self.ERROR = str(e)
            self.setState(RenderJobState.FAILED)
            raise e
        finally:
            self.RUNNING = False
            shutil.rmtree(self.FOLDER)
