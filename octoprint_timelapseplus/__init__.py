import base64
import glob
import io
import os
import random
import re
import string
from threading import Thread
from time import sleep

from PIL import Image
from flask import make_response, send_file

import octoprint.plugin
from .captureMode import CaptureMode
from .enhancementPreset import EnhancementPreset
from .frameZip import FrameZip
from .mask import Mask
from .printJob import PrintJob
from .renderJob import RenderJob
from .renderJobState import RenderJobState
from .renderPreset import RenderPreset
from .video import Video
from octoprint.events import Events


class TimelapsePlusPlugin(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.EventHandlerPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.SimpleApiPlugin,
    octoprint.plugin.BlueprintPlugin
):
    def __init__(self):
        super().__init__()
        self.PRINTJOB = None
        self.RENDERJOBS = []

    def get_api_commands(self):
        return dict(
            getData=[],
            render=['frameZipId', 'presetEnhancement', 'presetRender'],
            thumbnail=['type', 'id'],
            download=['type', 'id'],
            delete=['type', 'id'],
            defaultEnhancementPreset=[],
            defaultRenderPreset=[],
            listPresets=[]
        )

    def on_api_command(self, command, data):
        if command == 'getData':
            self.sendClientData()
        if command == 'render':
            frameZipId = data['frameZipId']
            allFrameZips = self.listFrameZips()
            frameZip = next(x for x in allFrameZips if x.ID == frameZipId)

            enhancementPreset = EnhancementPreset(self, data['presetEnhancement'])
            renderPreset = RenderPreset(data['presetRender'])

            self.render(frameZip, enhancementPreset, renderPreset)
        if command == 'listPresets':
            epRaw = self._settings.get(["enhancementPresets"])
            epList = list(map(lambda x: EnhancementPreset(self, x), epRaw))
            epNew = list(map(lambda x: x.getJSON(), epList))

            rpRaw = self._settings.get(["renderPresets"])
            rpList = list(map(lambda x: RenderPreset(x), rpRaw))
            rpNew = list(map(lambda x: x.getJSON(), rpList))
            return dict(enhancementPresets=epNew, renderPresets=rpNew)
        if command == 'defaultEnhancementPreset':
            ep = EnhancementPreset(self)
            return ep.getJSON()
        if command == 'defaultRenderPreset':
            ep = RenderPreset()
            return ep.getJSON()
        if command == 'delete':
            id = data['id']
            if data['type'] == 'video':
                allVideos = self.listVideos()
                video = next(x for x in allVideos if x.ID == id)
                video.delete()
            if data['type'] == 'frameZip':
                allFrameZips = self.listFrameZips()
                frameZip = next(x for x in allFrameZips if x.ID == id)
                frameZip.delete()
            self.sendClientData()

    @octoprint.plugin.BlueprintPlugin.route("/createBlurMask", methods=["POST"])
    def createBlurMask(self):
        import flask
        imgBase64 = flask.request.get_json()['image']
        imgData = base64.b64decode(re.sub('^data:image/.+;base64,', '', imgBase64))
        image = Image.open(io.BytesIO(imgData)).convert('L')

        mask = Mask(self, self._data_folder, None)
        image.save(mask.PATH)

        return dict(id=mask.ID)

    def on_api_get(self, req):
        command = req.args['command']
        if command == 'maskPreview':
            mask = Mask(self, self._data_folder, req.args['id'])
            img = Image.open(mask.PATH)
            thumb = self.makeThumbnail(img)
            response = make_response(thumb)
            response.mimetype = 'image/jpeg'
            return response
        if command == 'thumbnail':
            id = req.args['id']
            if req.args['type'] == 'video':
                allVideos = self.listVideos()
                video = next(x for x in allVideos if x.ID == id)

                img = Image.open(video.THUMBNAIL)
                thumb = self.makeThumbnail(img)

                response = make_response(thumb)
                response.mimetype = 'image/jpeg'
                return response
            if req.args['type'] == 'frameZip':
                allFrameZips = self.listFrameZips()
                frameZip = next(x for x in allFrameZips if x.ID == id)
                imgBytes = frameZip.getThumbnail()

                img = Image.open(io.BytesIO(imgBytes))
                thumb = self.makeThumbnail(img)

                response = make_response(thumb)
                response.mimetype = 'image/jpeg'
                return response
        if command == 'download':
            id = req.args['id']
            if req.args['type'] == 'video':
                allVideos = self.listVideos()
                video = next(x for x in allVideos if x.ID == id)
                return send_file(video.PATH, mimetype=video.MIMETYPE)
            if req.args['type'] == 'frameZip':
                allFrameZips = self.listFrameZips()
                frameZip = next(x for x in allFrameZips if x.ID == id)
                return send_file(frameZip.PATH, mimetype=frameZip.MIMETYPE)

    def makeThumbnail(self, img, size=(320, 180)):
        img.thumbnail(size)
        buf = io.BytesIO()
        img.save(buf, format='JPEG', quality=50)
        byteArr = buf.getvalue()
        return byteArr

    def get_assets(self):
        return {
            'js': ['js/timelapseplus.js'],
            'less': [],
            'css': ['css/timelapseplus.css'],
        }

    def get_template_configs(self):
        return [
            {
                "type": "tab",
                "template": "timelapseplus_tab.jinja2",
                "div": "timelapseplus",
                "custom_bindings": True,
            },
            {
                "type": "settings",
                "template": "timelapseplus_settings.jinja2",
                "custom_bindings": False
            }
        ]

    def get_settings_defaults(self):
        return dict(
            captureMode=CaptureMode.COMMAND.name,
            captureTimerInterval=10,
            snapshotCommand="SNAPSHOT",
            renderAfterPrint=True,
            enhancementPresets=[EnhancementPreset(self).getJSON()],
            renderPresets=[RenderPreset().getJSON()]
        )

    def get_template_vars(self):
        epRaw = self._settings.get(["enhancementPresets"])
        epList = list(map(lambda x: EnhancementPreset(self, x), epRaw))
        epNew = list(map(lambda x: x.getJSON(), epList))

        rpRaw = self._settings.get(["renderPresets"])
        rpList = list(map(lambda x: RenderPreset(x), rpRaw))
        rpNew = list(map(lambda x: x.getJSON(), rpList))

        return dict(
            captureMode=self._settings.get(["captureMode"]),
            captureTimerInterval=self._settings.get(["captureTimerInterval"]),
            snapshotCommand=self._settings.get(["snapshotCommand"]),
            renderAfterPrint=self._settings.get(["renderAfterPrint"]),
            enhancementPresets=epNew,
            renderPresets=rpNew
        )

    def listFrameZips(self):
        files = glob.glob(self._settings.getBaseFolder('timelapse') + '/*.zip')
        frameZips = list(map(lambda x: FrameZip(x, self, self._logger), files))
        frameZips.sort(key=lambda x: x.TIMESTAMP)
        frameZips.reverse()
        return frameZips

    def listVideos(self):
        files = glob.glob(self._settings.getBaseFolder('timelapse') + '/*.mp4')
        videos = list(map(lambda x: Video(x, self, self._logger), files))
        videos.sort(key=lambda x: x.TIMESTAMP)
        videos.reverse()
        return videos

    def sendClientData(self):
        data = dict(
            isRunning=False,
            currentFileSize=0,
            captureMode=None,
            captureTimerInterval=0,
            snapshotCommand=self._settings.get(["snapshotCommand"]),
            snapshotCount=0,
            previewImage=None,
            frameCollections=list(map(lambda x: x.getJSON(), self.listFrameZips())),
            renderJobs=list(map(lambda x: x.getJSON(), self.RENDERJOBS)),
            videos=list(map(lambda x: x.getJSON(), self.listVideos()))
        )

        if self.PRINTJOB is not None:
            data['currentFileSize'] = self.PRINTJOB.getTotalFileSize()
            data['captureMode'] = self.PRINTJOB.CAPTURE_MODE.name
            data['captureTimerInterval'] = self.PRINTJOB.CAPTURE_TIMER_INTERVAL

            if len(self.PRINTJOB.FRAMES) > 0:
                with open(self.PRINTJOB.FRAMES[-1], 'rb') as image_file:
                    imgBytes = image_file.read()
                    img = Image.open(io.BytesIO(imgBytes))
                    thumb = self.makeThumbnail(img, (640, 360))
                    data['previewImage'] = base64.b64encode(thumb)

            data['isRunning'] = self.PRINTJOB.RUNNING
            data['snapshotCount'] = len(self.PRINTJOB.FRAMES)

        self._plugin_manager.send_plugin_message(self._identifier, data)

    def getRandomString(self, length):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(length))

    def on_after_startup(self):
        self._logger.info("TIMELAPSE-PLUS")

    def renderJobStateChanged(self, job, state):
        self.sendClientData()

        if state == RenderJobState.FINISHED or state == RenderJobState.FAILED:
            Thread(target=(lambda j: (
                sleep(10),
                self.RENDERJOBS.remove(j),
                self.sendClientData()
            )), args=(job,)).start()

    def renderJobProgressChanged(self, job, progress):
        self.sendClientData()

    def doneSnapshot(self):
        self.sendClientData()

    def atCommand(self, comm, phase, command, parameters, tags=None, *args, **kwargs):
        if self.PRINTJOB is None or not self.PRINTJOB.RUNNING:
            return

        if command != self._settings.get(["snapshotCommand"]):
            return

        if self.PRINTJOB.CAPTURE_MODE != CaptureMode.COMMAND:
            return

        self.PRINTJOB.doSnapshot()

    def atAction(self, comm, line, action, *args, **kwargs):
        if self.PRINTJOB is None or not self.PRINTJOB.RUNNING:
            return

        if action != self._settings.get(["snapshotCommand"]):
            return

        if self.PRINTJOB.CAPTURE_MODE != CaptureMode.COMMAND:
            return

        self.PRINTJOB.doSnapshot()

    def render(self, frameZip, enhancementPreset=None, renderPreset=None):
        job = RenderJob(frameZip, self, self._logger, self._settings, self._data_folder, enhancementPreset, renderPreset)
        job.start()
        self.RENDERJOBS.append(job)

    def printStarted(self):
        if self.PRINTJOB is not None and self.PRINTJOB.RUNNING:
            return

        printerFile = self._printer.get_current_job()['file']['path']
        baseName = os.path.splitext(os.path.basename(printerFile))[0]

        self.PRINTJOB = PrintJob(baseName, self, self._logger, self._settings, self._data_folder)
        self.PRINTJOB.start()
        self.sendClientData()

    def printFinished(self, success):
        if self.PRINTJOB is None or not self.PRINTJOB.RUNNING:
            return

        zipFileName = self.PRINTJOB.finish()
        self.sendClientData()

        if self._settings.get(["renderAfterPrint"]):
            if zipFileName != None:
                frameZip = FrameZip(zipFileName, self, self._logger)
                self.render(frameZip)

    def printPaused(self):
        if self.PRINTJOB is None or not self.PRINTJOB.RUNNING:
            return

        self.PRINTJOB.PAUSED = True

    def printResumed(self):
        if self.PRINTJOB is None or not self.PRINTJOB.RUNNING:
            return

        self.PRINTJOB.PAUSED = False

    def on_event(self, event, payload):
        if event == Events.PRINT_STARTED:
            self.printFinished(False)
            self.printStarted()
        if event == Events.PRINT_DONE:
            self.printFinished(True)
        if event == Events.DISCONNECTING:
            self.printFinished(False)
        if event == Events.DISCONNECTED:
            self.printFinished(False)
        if event == Events.PRINT_PAUSED:
            self.printPaused()
        if event == Events.PRINT_RESUMED:
            self.printResumed()
        if event == Events.PRINT_FAILED:
            self.printFinished(False)
        if event == Events.PRINT_CANCELLING:
            self.printFinished(False)
        if event == Events.PRINT_CANCELLED:
            self.printFinished(False)
        if event == Events.PRINTER_RESET:
            self.printFinished(False)

    def increaseBodyUploadSize(self, current_max_body_sizes, *args, **kwargs):
        return [("POST", '/createBlurMask', 50 * 1024 * 1024)]


__plugin_pythoncompat__ = ">=3.7,<4"
__plugin_name__ = "Timelapse+"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = TimelapsePlusPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.server.http.bodysize": __plugin_implementation__.increaseBodyUploadSize,
        "octoprint.comm.protocol.atcommand.sending": __plugin_implementation__.atCommand,
        "octoprint.comm.protocol.action": __plugin_implementation__.atAction
    }
