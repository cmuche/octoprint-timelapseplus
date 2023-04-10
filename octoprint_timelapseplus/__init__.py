import base64
import glob
import io
import os
import random
import string
from threading import Thread
from time import sleep

from PIL import Image
from flask import make_response

import octoprint.plugin
from octoprint.plugins.timelapseplus.frameZip import FrameZip
from octoprint.plugins.timelapseplus.printJob import PrintJob
from octoprint.plugins.timelapseplus.renderJob import RenderJob
from octoprint.plugins.timelapseplus.renderJobState import RenderJobState
from octoprint.plugins.timelapseplus.video import Video


class TimelapsePlusPlugin(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.SimpleApiPlugin
):
    def __init__(self):
        super().__init__()
        self.CMD_SNAPSHOT = 'SNAPSHOT'
        self.PRINTJOB = None
        self.RENDERJOBS = []

    def get_api_commands(self):
        return dict(
            getData=[],
            render=['frameZipId'],
            thumbnail=['type', 'id'],
            delete=['type', 'id']
        )

    def on_api_command(self, command, data):
        if command == 'getData':
            self.sendClientData()
        if command == 'render':
            frameZipId = data['frameZipId']
            allFrameZips = self.listFrameZips()
            frameZip = next(x for x in allFrameZips if x.ID == frameZipId)
            self.render(frameZip)
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

    def on_api_get(self, req):
        command = req.args['command']
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
            'css': [],
        }

    def get_template_configs(self):
        return [
            {
                "type": "tab",
                "template": "timelapseplus_tab.jinja2",
                "div": "timelapseplus",
                "custom_bindings": True,
            }
        ]

    def get_settings_defaults(self):
        return {
            "fooBar": 42
        }

    def get_template_vars(self):
        return dict(foobar='NOTSET')

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
            snapshotCount=0,
            previewImage=None,
            frameCollections=list(map(lambda x: x.getJSON(), self.listFrameZips())),
            renderJobs=list(map(lambda x: x.getJSON(), self.RENDERJOBS)),
            videos=list(map(lambda x: x.getJSON(), self.listVideos()))
        )

        if self.PRINTJOB is not None:
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

        if state == RenderJobState.FINISHED:
            Thread(target=(lambda j: (
                sleep(5),
                self.RENDERJOBS.remove(j),
                self.sendClientData()
            )), args=(job,)).start()

    def renderJobProgressChanged(self, job, progress):
        self.sendClientData()

    def doneSnapshot(self):
        self.sendClientData()

    def atCommand(self, comm, phase, command, parameters, tags=None, *args, **kwargs):
        if command != self.CMD_SNAPSHOT:
            return

        self.PRINTJOB.doSnapshot()

    def render(self, frameZip):
        job = RenderJob(frameZip, self, self._logger, self._settings, self._data_folder)
        job.start()
        self.RENDERJOBS.append(job)

    def printStarted(self):
        if self.PRINTJOB is not None and self.PRINTJOB.RUNNING:
            pass

        printerFile = self._printer.get_current_job()['file']['path']
        baseName = os.path.splitext(os.path.basename(printerFile))[0]

        self.PRINTJOB = PrintJob(baseName, self, self._logger, self._settings, self._data_folder)
        self.PRINTJOB.start()
        self.sendClientData()

    def printFinished(self):
        if self.PRINTJOB is None or not self.PRINTJOB.RUNNING:
            pass

        zipFileName = self.PRINTJOB.finish()
        self.sendClientData()

        # TODO to settings
        if zipFileName != None:
            frameZip = FrameZip(zipFileName, self, self._logger)
            self.render(frameZip)

    def onScript(self, comm, script_type, script_name, *args, **kwargs):
        if script_name == 'beforePrintStarted':
            self.printStarted()
        if script_name == 'afterPrintCancelled':
            self.printFinished()
        if script_name == 'afterPrintDone':
            self.printFinished()
        if script_name == 'beforePrinterDisconnected':
            self.printFinished()


__plugin_name__ = "Timelapse+"
__plugin_author__ = "Christoph Muche"
__plugin_version__ = "1.0.0"
__plugin_description__ = "Better Timelapses"
__plugin_pythoncompat__ = ">=3.7,<4"


# better-ffmpeg-progress

def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = TimelapsePlusPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.comm.protocol.atcommand.sending": __plugin_implementation__.atCommand,
        "octoprint.comm.protocol.scripts": __plugin_implementation__.onScript
    }
