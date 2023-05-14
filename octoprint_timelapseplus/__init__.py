import glob
import io
import os
import random
import string
from threading import Thread
from time import sleep

import octoprint.plugin
from octoprint.events import Events
from .apiController import ApiController
from .cacheController import CacheController
from .cleanupController import CleanupController
from .helpers.formatHelper import FormatHelper
from .clientController import ClientController
from .model.captureMode import CaptureMode
from .model.enhancementPreset import EnhancementPreset
from .model.frameZip import FrameZip
from .model.mask import Mask
from .model.printJob import PrintJob
from .model.renderJob import RenderJob
from .model.renderJobState import RenderJobState
from .model.renderPreset import RenderPreset
from .model.video import Video
from .model.webcamType import WebcamType
from .prerequisitesController import PrerequisitesController
from .webcamController import WebcamController


class TimelapsePlusPlugin(
    octoprint.plugin.SettingsPlugin,
    octoprint.plugin.StartupPlugin,
    octoprint.plugin.EventHandlerPlugin,
    octoprint.plugin.AssetPlugin,
    octoprint.plugin.TemplatePlugin,
    octoprint.plugin.BlueprintPlugin
):
    def __init__(self):
        super().__init__()
        self.PLUGIN_VERSION = None
        self.PRINTJOB = None
        self.RENDERJOBS = []
        self.ERROR = None

    @octoprint.plugin.BlueprintPlugin.route("/webcamCapturePreview", methods=["POST"])
    def apiWebcamCapturePreview(self):
        return self.API_CONTROLLER.webcamCapturePreview()

    @octoprint.plugin.BlueprintPlugin.route("/reCheckPrerequisites", methods=["POST"])
    def apiReCheckPrerequisites(self):
        self.API_CONTROLLER.reCheckPrerequisites()
        return self.API_CONTROLLER.emptyResponse()

    @octoprint.plugin.BlueprintPlugin.route("/createBlurMask", methods=["POST"])
    def apiCreateBlurMask(self):
        return self.API_CONTROLLER.createBlurMask()

    @octoprint.plugin.BlueprintPlugin.route("/getData", methods=["POST"])
    def apiGetData(self):
        self.sendClientData(True)
        return self.API_CONTROLLER.emptyResponse()

    @octoprint.plugin.BlueprintPlugin.route("/defaultEnhancementPreset", methods=["POST"])
    def apiDefaultEnhancementPreset(self):
        return EnhancementPreset(self).getJSON()

    @octoprint.plugin.BlueprintPlugin.route("/getRenderPresetVideoLength", methods=["POST"])
    def apiGetRenderPresetVideoLength(self):
        return self.API_CONTROLLER.getRenderPresetVideoLength()

    @octoprint.plugin.BlueprintPlugin.route("/defaultRenderPreset", methods=["POST"])
    def apiDefaultRenderPreset(self):
        return RenderPreset().getJSON()

    @octoprint.plugin.BlueprintPlugin.route("/delete", methods=["POST"])
    def apiDelete(self):
        self.API_CONTROLLER.delete()
        return self.API_CONTROLLER.emptyResponse()

    @octoprint.plugin.BlueprintPlugin.route("/listPresets", methods=["POST"])
    def apiListPresets(self):
        return self.API_CONTROLLER.listPresets()

    @octoprint.plugin.BlueprintPlugin.route("/render", methods=["POST"])
    def apiRender(self):
        self.API_CONTROLLER.render()
        return self.API_CONTROLLER.emptyResponse()

    @octoprint.plugin.BlueprintPlugin.route("/thumbnail", methods=["GET"])
    def apiThumbnail(self):
        return self.API_CONTROLLER.thumbnail()

    @octoprint.plugin.BlueprintPlugin.route("/maskPreview", methods=["GET"])
    def apiMaskPreview(self):
        return self.API_CONTROLLER.maskPreview()

    @octoprint.plugin.BlueprintPlugin.route("/download", methods=["GET"])
    def apiDownload(self):
        return self.API_CONTROLLER.download()

    @octoprint.plugin.BlueprintPlugin.route("/enhancementPreview", methods=["GET"])
    def apiEnhancementPreview(self):
        return self.API_CONTROLLER.enhancementPreview()

    @octoprint.plugin.BlueprintPlugin.route("/enhancementPreviewSettings", methods=["POST"])
    def apiEnhancementPreviewSettings(self):
        return self.API_CONTROLLER.enhancementPreviewSettings()

    @octoprint.plugin.BlueprintPlugin.route("/listVideoFormats", methods=["POST"])
    def apiListVideoFormats(self):
        return self.API_CONTROLLER.listVideoFormats()

    @octoprint.plugin.BlueprintPlugin.route("/uploadFrameZip", methods=["POST"])
    def apiUploadFrameZip(self):
        self.API_CONTROLLER.uploadFrameZip()
        return self.API_CONTROLLER.emptyResponse()

    def makeThumbnail(self, img, size=(320, 180)):
        img.thumbnail(size)
        buf = io.BytesIO()
        img.convert('RGB').save(buf, format='JPEG', quality=75)
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
            ffmpegPath='',
            ffprobePath='',
            webcamType=WebcamType.IMAGE_JPEG.name,
            webcamUrl='',
            captureMode=CaptureMode.COMMAND.name,
            captureTimerInterval=10,
            snapshotCommand="SNAPSHOT",
            renderAfterPrint=True,
            forceCapturing=False,
            compressFrameZips=False,
            enhancementPresets=[EnhancementPreset(self).getJSON()],
            renderPresets=[RenderPreset().getJSON()],
            defaultVideoFormat=FormatHelper.getDefaultVideoFormat().ID,
            purgeFrameCollections=False,
            purgeFrameCollectionsDays=90,
            purgeVideos=False,
            purgeVideosDays=90
        )

    def get_template_vars(self):
        epRaw = self._settings.get(["enhancementPresets"])
        epList = list(map(lambda x: EnhancementPreset(self, x), epRaw))
        epNew = list(map(lambda x: x.getJSON(), epList))

        rpRaw = self._settings.get(["renderPresets"])
        rpList = list(map(lambda x: RenderPreset(x), rpRaw))
        rpNew = list(map(lambda x: x.getJSON(), rpList))

        return dict(
            ffmpegPath=self._settings.get(["ffmpegPath"]),
            ffprobePath=self._settings.get(["ffprobePath"]),
            webcamType=self._settings.get(["webcamType"]),
            webcamUrl=self._settings.get(["webcamUrl"]),
            captureMode=self._settings.get(["captureMode"]),
            captureTimerInterval=self._settings.get(["captureTimerInterval"]),
            snapshotCommand=self._settings.get(["snapshotCommand"]),
            renderAfterPrint=self._settings.get(["renderAfterPrint"]),
            forceCapturing=self._settings.get(["forceCapturing"]),
            compressFrameZips=self._settings.get(["compressFrameZips"]),
            enhancementPresets=epNew,
            renderPresets=rpNew,
            defaultVideoFormat=self._settings.get(["defaultVideoFormat"]),
            purgeFrameCollections=self._settings.get(["purgeFrameCollections"]),
            purgeFrameCollectionsDays=self._settings.get(["purgeFrameCollectionsDays"]),
            purgeVideos=self._settings.get(["purgeVideos"]),
            purgeVideosDays=self._settings.get(["purgeVideosDays"])
        )

    def listFrameZips(self):
        files = glob.glob(self._settings.getBaseFolder('timelapse') + '/*.zip')
        frameZips = list(map(lambda x: FrameZip(x, self, self._logger), files))
        frameZips.sort(key=lambda x: x.TIMESTAMP)
        frameZips.reverse()
        return frameZips

    def listVideos(self):
        videoExtensions = FormatHelper.getVideoFormatExtensions()
        files = []
        allFiles = glob.glob(self._settings.getBaseFolder('timelapse') + '/*')
        for f in allFiles:
            ext = os.path.splitext(f)[1][1:].lower()
            if ext in videoExtensions:
                files.append(f)

        videos = list(map(lambda x: Video(x, self, self._logger, self._settings), files))
        videos.sort(key=lambda x: x.TIMESTAMP)
        videos.reverse()
        return videos

    def sendClientPopup(self, type, title, message):
        data = dict(
            type='popup',
            popup=type,
            title=title,
            message=message
        )
        self._plugin_manager.send_plugin_message(self._identifier, data)

    def sendClientData(self, force=False):
        Thread(target=self.sendClientDataInner, args=(force,), daemon=True).start()

    def sendClientDataInner(self, force):
        allFrameZips = self.listFrameZips()
        allVideos = self.listVideos()
        data = dict(
            error=self.ERROR,
            isRunning=False,
            isCapturing=False,
            currentFileSize=0,
            captureMode=None,
            captureTimerInterval=0,
            snapshotCommand=self._settings.get(["snapshotCommand"]),
            snapshotCount=0,
            previewImage=None,
            frameCollections=list(map(lambda x: x.getJSON(), allFrameZips)),
            renderJobs=list(map(lambda x: x.getJSON(), self.RENDERJOBS)),
            videos=list(map(lambda x: x.getJSON(), allVideos)),
            sizeFrameCollections=sum(c.SIZE for c in allFrameZips),
            sizeVideos=sum(c.SIZE for c in allVideos)
        )

        if self.PRINTJOB is not None:
            data['currentFileSize'] = self.PRINTJOB.getTotalFileSize()
            data['captureMode'] = self.PRINTJOB.CAPTURE_MODE.name
            data['captureTimerInterval'] = self.PRINTJOB.CAPTURE_TIMER_INTERVAL
            data['previewImage'] = self.PRINTJOB.PREVIEW_IMAGE
            data['isRunning'] = self.PRINTJOB.RUNNING
            data['isCapturing'] = self.PRINTJOB.isCapturing()
            data['snapshotCount'] = len(self.PRINTJOB.FRAMES)

        self.CLIENT_CONTROLLER.enqueueData(data, force)

    def getRandomString(self, length):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(length))

    def on_after_startup(self):
        self.PLUGIN_VERSION = self._plugin_version
        self.CACHE_CONTROLLER = CacheController(self, self.get_plugin_data_folder(), self._settings)
        self.WEBCAM_CONTROLLER = WebcamController(self, self._logger, self.get_plugin_data_folder(), self._settings)
        self.API_CONTROLLER = ApiController(self, self.get_plugin_data_folder(), self._basefolder, self._settings, self.CACHE_CONTROLLER, self.WEBCAM_CONTROLLER)
        self.CLEANUP_CONTROLLER = CleanupController(self, self.get_plugin_data_folder(), self._settings)
        self.CLIENT_CONTROLLER = ClientController(self, self._identifier, self._plugin_manager)

        self.CLEANUP_CONTROLLER.init()

        epRaw = self._settings.get(["enhancementPresets"])
        epList = list(map(lambda x: EnhancementPreset(self, x), epRaw))
        epNew = list(map(lambda x: x.getJSON(), epList))
        self._settings.set(["enhancementPresets"], epNew)

        rpRaw = self._settings.get(["renderPresets"])
        rpList = list(map(lambda x: RenderPreset(x), rpRaw))
        rpNew = list(map(lambda x: x.getJSON(), rpList))
        self._settings.set(["renderPresets"], rpNew)

        defaultVideoFormatId = self._settings.get(["defaultVideoFormat"])
        defaultVideoFormat = FormatHelper.getVideoFormatById(defaultVideoFormatId)
        self._settings.set(["defaultVideoFormat"], defaultVideoFormat.ID)

        self.checkPrerequisites()

    def on_settings_save(self, data):
        ret = super().on_settings_save(data)
        self.checkPrerequisites()
        return ret

    def checkPrerequisites(self):
        try:
            PrerequisitesController.check(self._settings, self.WEBCAM_CONTROLLER)
            self.ERROR = None
        except Exception as ex:
            self.ERROR = str(ex)

        self.sendClientData()

    def renderJobStateChanged(self, job, state):
        self.sendClientData()

        if state == RenderJobState.FINISHED or state == RenderJobState.FAILED:
            if state == RenderJobState.FINISHED:
                self.sendClientPopup('success', 'Render Job finished', job.BASE_NAME)

            if state == RenderJobState.FAILED:
                self.sendClientPopup('error', 'Render Job failed', job.BASE_NAME + "\n\n" + job.ERROR)

            Thread(target=(lambda j: (
                sleep(10),
                self.RENDERJOBS.remove(j),
                self.sendClientData()
            )), args=(job,), daemon=True).start()

    def renderJobProgressChanged(self, job, progress):
        self.sendClientData()

    def doneSnapshot(self):
        self.sendClientData()

    def errorSnapshot(self, err):
        self.sendClientPopup('error', 'Webcam Capture failed', str(err))

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

    def render(self, frameZip, enhancementPreset=None, renderPreset=None, videoFormat=None):
        job = RenderJob(frameZip, self, self._logger, self._settings, self.get_plugin_data_folder(), enhancementPreset, renderPreset, videoFormat)
        job.start()
        self.RENDERJOBS.append(job)

    def printStarted(self):
        if self.PRINTJOB is not None and self.PRINTJOB.RUNNING:
            return

        self.checkPrerequisites()
        if self.ERROR is not None and not self._settings.get(["forceCapturing"]):
            return

        printerFile = self._printer.get_current_job()['file']['path']
        baseName = os.path.splitext(os.path.basename(printerFile))[0]
        id = self.getRandomString(32)

        self.PRINTJOB = PrintJob(id, baseName, self, self._logger, self._settings, self.get_plugin_data_folder(), self.WEBCAM_CONTROLLER)
        self.PRINTJOB.start()
        self.sendClientData()

    def printFinished(self, success):
        if self.PRINTJOB is None or not self.PRINTJOB.RUNNING:
            return

        zipFileName = self.PRINTJOB.finish(success)
        self.sendClientData()

        if self._settings.get(["renderAfterPrint"]):
            if zipFileName != None:
                frameZip = FrameZip(zipFileName, self, self._logger)
                self.render(frameZip)

    def printPaused(self):
        if self.PRINTJOB is None or not self.PRINTJOB.RUNNING:
            return

        self.PRINTJOB.PAUSED = True
        self.sendClientData()

    def printResumed(self):
        if self.PRINTJOB is None or not self.PRINTJOB.RUNNING:
            return

        self.PRINTJOB.PAUSED = False
        self.sendClientData()

    def on_event(self, event, payload):
        if event == Events.PRINT_STARTED:
            self.printFinished(False)
            self.printStarted()
            return
        if event == Events.PRINT_DONE:
            self.printFinished(True)
            return
        if event == Events.DISCONNECTING:
            self.printFinished(False)
            return
        if event == Events.DISCONNECTED:
            self.printFinished(False)
            return
        if event == Events.PRINT_PAUSED:
            self.printPaused()
            return
        if event == Events.PRINT_RESUMED:
            self.printResumed()
            return
        if event == Events.PRINT_FAILED:
            self.printFinished(False)
            return
        if event == Events.PRINT_CANCELLING:
            self.printFinished(False)
            return
        if event == Events.PRINT_CANCELLED:
            self.printFinished(False)
            return
        if event == Events.PRINTER_RESET:
            self.printFinished(False)

    def increaseBodyUploadSize(self, current_max_body_sizes, *args, **kwargs):
        return [('POST', '/createBlurMask', 50 * 1024 * 1024), ('POST', '/uploadFrameZip', 5 * 1024 * 1024 * 1024)]

    def getUpdateInformation(self, *args, **kwargs):
        return dict(
            timelapseplus=dict(
                displayName=self._plugin_name,
                displayVersion=self._plugin_version,

                type="github_release",
                current=self._plugin_version,
                user="cmuche",
                repo="octoprint-timelapseplus",

                pip="https://github.com/cmuche/octoprint-timelapseplus/archive/{target}.zip"
            )
        )


__plugin_pythoncompat__ = ">=3.7,<4"
__plugin_name__ = "Timelapse+"
__plugin_identifier__ = "timelapseplus"


def __plugin_load__():
    global __plugin_implementation__
    __plugin_implementation__ = TimelapsePlusPlugin()

    global __plugin_hooks__
    __plugin_hooks__ = {
        "octoprint.server.http.bodysize": __plugin_implementation__.increaseBodyUploadSize,
        "octoprint.comm.protocol.atcommand.sending": __plugin_implementation__.atCommand,
        "octoprint.comm.protocol.action": __plugin_implementation__.atAction,
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.getUpdateInformation
    }
