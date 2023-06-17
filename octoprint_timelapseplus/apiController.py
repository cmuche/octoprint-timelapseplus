import base64
import io
import os
import re
import shutil
import time
from contextlib import closing
from zipfile import ZipFile

from PIL import Image, ImageDraw
from flask import make_response, send_file

from .log import Log
from .helpers.listHelper import ListHelper
from .helpers.stabilizationEaseCalculator import StabilizationEaseCalculator
from .model.captureMode import CaptureMode
from .helpers.fileHelper import FileHelper
from .helpers.timecodeRenderer import TimecodeRenderer
from .model.frameTimecodeInfo import FrameTimecodeInfo
from .model.stabilizationEaseFn import StabilizationEaseFn
from .prerequisitesController import PrerequisitesController
from .model.webcamType import WebcamType
from .helpers.formatHelper import FormatHelper
from .model.enhancementPreset import EnhancementPreset
from .model.renderPreset import RenderPreset
from .model.mask import Mask


class ApiController:
    def __init__(self, parent, dataFolder, baseFolder, settings, cacheController, webcamController):
        self.PARENT = parent
        self._data_folder = dataFolder
        self._basefolder = baseFolder
        self._settings = settings
        self.CACHE_CONTROLLER = cacheController
        self.WEBCAM_CONTROLLER = webcamController

    def emptyResponse(self):
        response = make_response(dict(success=True))
        response.mimetype = 'application/json'
        return response

    def createBlurMask(self):
        import flask
        imgBase64 = flask.request.get_json()['image']
        imgData = base64.b64decode(re.sub('^data:image/.+;base64,', '', imgBase64))
        image = Image.open(io.BytesIO(imgData)).convert('L')

        mask = Mask(self.PARENT, self._data_folder, None)
        image.save(mask.PATH)

        return dict(id=mask.ID)

    def thumbnail(self):
        import flask
        data = flask.request.args
        id = data['id']
        if data['type'] == 'video':
            cacheId = ['thumbnail', 'video', id]

            if not self.CACHE_CONTROLLER.isCached(cacheId):
                allVideos = self.PARENT.listVideos()
                video = next(x for x in allVideos if x.ID == id)

                if os.path.isfile(video.THUMBNAIL):
                    img = Image.open(video.THUMBNAIL)
                else:
                    img = Image.open(self._basefolder + '/static/assets/no-thumbnail.jpg')

                thumb = self.PARENT.makeThumbnail(img)
                self.CACHE_CONTROLLER.storeBytes(cacheId, thumb)

                img.close()

            thumb = self.CACHE_CONTROLLER.getBytes(cacheId)
            response = make_response(thumb)
            response.mimetype = 'image/jpeg'
            return response
        if data['type'] == 'frameZip':
            cacheId = ['thumbnail', 'framezip', id]

            if not self.CACHE_CONTROLLER.isCached(cacheId):
                try:
                    allFrameZips = self.PARENT.listFrameZips()
                    frameZip = next(x for x in allFrameZips if x.ID == id)
                    imgBytes = frameZip.getThumbnail()
                    img = Image.open(io.BytesIO(imgBytes))
                except Exception as e:
                    img = Image.open(self._basefolder + '/static/assets/no-thumbnail.jpg')

                thumb = self.PARENT.makeThumbnail(img)
                self.CACHE_CONTROLLER.storeBytes(cacheId, thumb)

                img.close()

            thumb = self.CACHE_CONTROLLER.getBytes(cacheId)
            response = make_response(thumb)
            response.mimetype = 'image/jpeg'

            return response

    def maskPreview(self):
        import flask
        data = flask.request.args
        mask = Mask(self.PARENT, self._data_folder, data['id'])

        img = Image.open(mask.PATH)
        thumb = self.PARENT.makeThumbnail(img)
        response = make_response(thumb)

        img.close()

        response.mimetype = 'image/jpeg'
        return response

    def download(self):
        import flask
        data = flask.request.args
        id = data['id']
        if data['type'] == 'video':
            allVideos = self.PARENT.listVideos()
            video = next(x for x in allVideos if x.ID == id)
            return send_file(video.PATH, as_attachment=True, download_name=os.path.basename(video.PATH))
        if data['type'] == 'frameZip':
            allFrameZips = self.PARENT.listFrameZips()
            frameZip = next(x for x in allFrameZips if x.ID == id)
            return send_file(frameZip.PATH, as_attachment=True, download_name=os.path.basename(frameZip.PATH))

    def enhancementPreview(self):
        import flask
        data = flask.request.args
        allFrameZips = self.PARENT.listFrameZips()
        frameZip = next(x for x in allFrameZips if x.ID == data['frameZipId'])
        frame = frameZip.getThumbnail()

        with Image.open(io.BytesIO(frame)) as img:
            epRaw = self._settings.get(["enhancementPresets"])
            epList = list(map(lambda x: EnhancementPreset(self.PARENT, x), epRaw))
            preset = epList[int(data['presetIndex'])]

            img = preset.applyEnhance(img)
            img = preset.applyBlur(img)

            timecodeRenderer = TimecodeRenderer(self._basefolder)
            with timecodeRenderer.applyTimecode(img, preset, FrameTimecodeInfo.getDummy()) as imgTimecode:
                res = self.PARENT.makeThumbnail(imgTimecode, (500, 500))
                response = make_response(res)

        response.mimetype = 'image/jpeg'
        return response

    def enhancementPreviewSettings(self):
        import flask
        data = flask.request.get_json()
        preset = EnhancementPreset(self.PARENT, data['preset'])

        snapshot = self.WEBCAM_CONTROLLER.getSnapshot()
        try:
            with Image.open(snapshot) as img:
                img = preset.applyEnhance(img)
                img = preset.applyBlur(img)

                timecodeRederer = TimecodeRenderer(self._basefolder)
                with timecodeRederer.applyTimecode(img, preset, FrameTimecodeInfo.getDummy()) as imgTimecode:
                    res = self.PARENT.makeThumbnail(imgTimecode, (500, 500))
                    resBase64 = base64.b64encode(res)
                    return dict(result=resBase64)
        finally:
            if snapshot is not None and os.path.isfile(snapshot):
                os.remove(snapshot)

    def render(self):
        import flask
        data = flask.request.get_json()
        frameZipId = data['frameZipId']
        allFrameZips = self.PARENT.listFrameZips()
        frameZip = next(x for x in allFrameZips if x.ID == frameZipId)

        enhancementPreset = EnhancementPreset(self.PARENT, data['presetEnhancement'])
        renderPreset = RenderPreset(data['presetRender'])
        videoFormat = FormatHelper.getVideoFormatById(data['formatId'])

        self.PARENT.render(frameZip, enhancementPreset, renderPreset, videoFormat)

    def listPresets(self):
        epRaw = self._settings.get(["enhancementPresets"])
        epList = list(map(lambda x: EnhancementPreset(self.PARENT, x), epRaw))
        epNew = list(map(lambda x: x.getJSON(), epList))

        rpRaw = self._settings.get(["renderPresets"])
        rpList = list(map(lambda x: RenderPreset(x), rpRaw))
        rpNew = list(map(lambda x: x.getJSON(), rpList))
        return dict(enhancementPresets=epNew, renderPresets=rpNew)

    def delete(self):
        import flask
        data = flask.request.get_json()
        id = data['id']
        if data['type'] == 'video':
            allVideos = self.PARENT.listVideos()
            video = next(x for x in allVideos if x.ID == id)
            video.delete()
        if data['type'] == 'frameZip':
            allFrameZips = self.PARENT.listFrameZips()
            frameZip = next(x for x in allFrameZips if x.ID == id)
            frameZip.delete()
        self.PARENT.sendClientData()

    def getRenderPresetVideoLength(self):
        import flask
        data = flask.request.get_json()
        preset = RenderPreset(data['preset'])

        allFrameZips = self.PARENT.listFrameZips()
        frameZip = next(x for x in allFrameZips if x.ID == data['frameZipId'])

        length = preset.calculateVideoLength(frameZip)
        return dict(length=length)

    def listVideoFormats(self):
        formats = list(map(lambda x: x.getJSON(), FormatHelper.getVideoFormats()))
        defaultId = self._settings.get(["defaultVideoFormat"])
        return dict(formats=formats, defaultId=defaultId)

    def reCheckPrerequisites(self):
        self.PARENT.checkPrerequisites()

    def webcamCapturePreview(self):
        import flask
        data = flask.request.get_json()

        ffmpegPath = data['ffmpegPath']
        ffprobePath = data['ffprobePath']
        webcamType = WebcamType[data['webcamType']]
        webcamUrl = data['webcamUrl']
        pluginId = data['pluginId']

        snapshot = None
        try:
            PrerequisitesController.check(self._settings, self.PARENT.WEBCAM_CONTROLLER, ffmpegPath, ffprobePath, webcamType, webcamUrl, pluginId)

            startTime = time.time()
            snapshot = self.PARENT.WEBCAM_CONTROLLER.getSnapshot(ffmpegPath, webcamType, webcamUrl, pluginId)
            elapsedTime = int((time.time() - startTime) * 1000)
            size = os.path.getsize(snapshot)

            with Image.open(snapshot) as img:
                width, height = img.size

                res = self.PARENT.makeThumbnail(img, (500, 500))
                resBase64 = base64.b64encode(res)
                return dict(time=elapsedTime, size=size, width=width, height=height, result=resBase64)
        except Exception as e:
            return dict(error=str(e))
        finally:
            if snapshot is not None and os.path.isfile(snapshot):
                os.remove(snapshot)

    def uploadFrameZip(self):
        import flask
        data = flask.request

        fileName = os.path.basename(data.form['file.name'])
        fileExt = os.path.splitext(fileName)[1][1:].lower()
        fileTemp = data.form['file.path']

        if fileExt != 'zip':
            raise Exception('Not a ZIP File')

        with closing(ZipFile(fileTemp)) as archive:
            testRes = archive.testzip()
            if testRes is not None:
                raise Exception('ZIP File is corrupt')

        newFileName = self._settings.getBaseFolder('timelapse') + '/' + fileName
        newFileName = FileHelper.getUniqueFileName(newFileName)

        shutil.move(fileTemp, newFileName)
        self.PARENT.sendClientData()

    def editQuickSettings(self):
        import flask
        data = flask.request.get_json()

        if 'enabled' in data:
            self._settings.set(["enabled"], bool(data['enabled']))

        if 'stabilization' in data:
            self._settings.set(["stabilization"], bool(data['stabilization']))

        if 'captureMode' in data:
            self._settings.set(["captureMode"], CaptureMode[data['captureMode']].name)

        self._settings.save(trigger_event=True)
        self.PARENT.sendClientData()

    def stabilizationEaseFnPreview(self):
        import flask
        data = flask.request.args

        fn = StabilizationEaseFn[data['fn']]
        cycles = int(data['cycles'])
        imgSizeOut = (200, 50)
        imgSize = (imgSizeOut[0] * 3, imgSizeOut[1] * 3)

        img = Image.new('RGBA', imgSize, (127, 127, 127, 25))
        draw = ImageDraw.Draw(img)

        pX = 0
        pY = StabilizationEaseCalculator.applyEaseFn(0, fn, cycles)
        for x in ListHelper.rangeList(imgSize[0] - 1):
            x += 1
            t = x / imgSize[0]
            y = StabilizationEaseCalculator.applyEaseFn(t, fn, cycles)
            y1 = pY * imgSize[1]
            y2 = y * imgSize[1]
            draw.line((pX, imgSize[1] - int(y1), x, imgSize[1] - int(y2)), fill=(127, 127, 127, 255), width=5)
            pX = x
            pY = y

        imgOut = img.resize(imgSizeOut)
        buf = io.BytesIO()
        imgOut.save(buf, format='PNG')

        img.close()
        imgOut.close()

        byteArr = buf.getvalue()
        response = make_response(byteArr)
        response.mimetype = 'image/png'
        return response

    def downloadLog(self):
        logFile = self._settings.get_plugin_logfile_path()
        return send_file(logFile, as_attachment=False, mimetype='text/plain')

    def findHomePosition(self):
        if self.PARENT.GCODE_RECEIVED_LISTENER is not None:
            Log.error('Finding Home Position failed: Already in progress')
            return dict(error=True, msg='Already in progress')

        class GcodeCallback:
            def __init__(self):
                self.X = 0
                self.Y = 0
                self.Z = 0
                self.HAS_POS = False

            def process(self, line):
                reStr = '.?X:([0-9.]+).?Y:([0-9.]+).?Z:([0-9.]+).*'
                match = re.search(reStr, line)
                if not match:
                    return
                self.X = float(match.group(1))
                self.Y = float(match.group(2))
                self.Z = float(match.group(3))
                self.HAS_POS = True

        try:
            callback = GcodeCallback()
            printer = self.PARENT.getPrinter()

            if not printer.is_ready():
                Log.error('Finding Home Position failed: Printer is not ready')
                return dict(error=True, msg='Printer is not ready')

            self.PARENT.GCODE_RECEIVED_LISTENER = callback
            printer.commands(['G28', 'M114 D E R'])

            timeTimeout = time.time() + 30
            while not callback.HAS_POS and time.time() < timeTimeout:
                time.sleep(0.1)

            if not callback.HAS_POS:
                Log.error('Finding Home Position timed out')
                return dict(error=True, msg='Timed out')

            posDict = dict(x=callback.X, y=callback.Y, z=callback.Z)
            Log.info('Home Position found', posDict)
            return dict(error=False, msg=None, pos=posDict)
        finally:
            self.PARENT.GCODE_RECEIVED_LISTENER = None
