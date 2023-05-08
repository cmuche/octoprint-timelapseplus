import base64
import io
import os
import re

from PIL import Image
from flask import make_response, send_file

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

            if self.CACHE_CONTROLLER.isCached(cacheId):
                thumb = self.CACHE_CONTROLLER.getBytes(cacheId)
            else:
                allVideos = self.PARENT.listVideos()
                video = next(x for x in allVideos if x.ID == id)

                if os.path.isfile(video.THUMBNAIL):
                    img = Image.open(video.THUMBNAIL)
                else:
                    img = Image.open(self._basefolder + '/static/assets/no-thumbnail.jpg')

                thumb = self.PARENT.makeThumbnail(img)
                self.CACHE_CONTROLLER.storeBytes(cacheId, thumb)

            response = make_response(thumb)
            response.mimetype = 'image/jpeg'
            return response
        if data['type'] == 'frameZip':
            cacheId = ['thumbnail', 'framezip', id]

            if self.CACHE_CONTROLLER.isCached(cacheId):
                thumb = self.CACHE_CONTROLLER.getBytes(cacheId)
            else:
                allFrameZips = self.PARENT.listFrameZips()
                frameZip = next(x for x in allFrameZips if x.ID == id)
                imgBytes = frameZip.getThumbnail()
                img = Image.open(io.BytesIO(imgBytes))
                thumb = self.PARENT.makeThumbnail(img)
                self.CACHE_CONTROLLER.storeBytes(cacheId, thumb)

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
        img = Image.open(io.BytesIO(frame))

        epRaw = self._settings.get(["enhancementPresets"])
        epList = list(map(lambda x: EnhancementPreset(self.PARENT, x), epRaw))
        preset = epList[int(data['presetIndex'])]

        img = preset.applyEnhance(img)
        img = preset.applyBlur(img)

        res = self.PARENT.makeThumbnail(img, (500, 500))
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

                res = self.PARENT.makeThumbnail(img, (500, 500))
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
