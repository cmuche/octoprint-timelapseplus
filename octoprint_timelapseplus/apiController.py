import base64
import io
import re

from PIL import Image
from flask import make_response, send_file

from .model.enhancementPreset import EnhancementPreset
from .model.renderPreset import RenderPreset
from .model.mask import Mask


class ApiController:
    def __init__(self, parent, dataFolder, settings):
        self.PARENT = parent
        self._data_folder = dataFolder
        self._settings = settings

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
            allVideos = self.PARENT.listVideos()
            video = next(x for x in allVideos if x.ID == id)

            img = Image.open(video.THUMBNAIL)
            thumb = self.PARENT.makeThumbnail(img)

            response = make_response(thumb)
            response.mimetype = 'image/jpeg'
            return response
        if data['type'] == 'frameZip':
            allFrameZips = self.PARENT.listFrameZips()
            frameZip = next(x for x in allFrameZips if x.ID == id)
            imgBytes = frameZip.getThumbnail()

            img = Image.open(io.BytesIO(imgBytes))
            thumb = self.PARENT.makeThumbnail(img)

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
            return send_file(video.PATH, mimetype=video.MIMETYPE)
        if data['type'] == 'frameZip':
            allFrameZips = self.PARENT.listFrameZips()
            frameZip = next(x for x in allFrameZips if x.ID == id)
            return send_file(frameZip.PATH, mimetype=frameZip.MIMETYPE)

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

    def render(self):
        import flask
        data = flask.request.get_json()
        frameZipId = data['frameZipId']
        allFrameZips = self.PARENT.listFrameZips()
        frameZip = next(x for x in allFrameZips if x.ID == frameZipId)

        enhancementPreset = EnhancementPreset(self.PARENT, data['presetEnhancement'])
        renderPreset = RenderPreset(data['presetRender'])

        self.PARENT.render(frameZip, enhancementPreset, renderPreset)

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
