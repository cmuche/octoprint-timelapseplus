import glob
import io
import os
import random
import string
import sys
from threading import Thread
from time import sleep

import logging
import octoprint.plugin
from octoprint.events import Events
from .log import Log
from .apiController import ApiController
from .cacheController import CacheController
from .cleanupController import CleanupController
from .constants import Constants
from .helpers.formatHelper import FormatHelper
from .clientController import ClientController
from .helpers.listHelper import ListHelper
from .helpers.positionTracker import PositionTracker
from .model.captureMode import CaptureMode
from .model.enhancementPreset import EnhancementPreset
from .model.frameZip import FrameZip
from .model.mask import Mask
from .model.printJob import PrintJob
from .model.renderJob import RenderJob
from .model.renderJobState import RenderJobState
from .model.renderPreset import RenderPreset
from .model.snapshotInfoFrame import SnapshotInfoFrame
from .model.stabilizatonSettings import StabilizationSettings
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
        self.POSITION_TRACKER = None
        self.GCODE_RECEIVED_LISTENER = None

    def doApiRequest(self, fn):
        try:
            #Log.debug('API Request', {'name': fn.__name__})
            return fn()
        except Exception as err:
            Log.critical('API Request failed', err)
            return None

    @octoprint.plugin.BlueprintPlugin.route("/webcamCapturePreview", methods=["POST"])
    def apiWebcamCapturePreview(self):
        return self.doApiRequest(self.API_CONTROLLER.webcamCapturePreview)

    @octoprint.plugin.BlueprintPlugin.route("/reCheckPrerequisites", methods=["POST"])
    def apiReCheckPrerequisites(self):
        self.doApiRequest(self.API_CONTROLLER.reCheckPrerequisites)
        return self.API_CONTROLLER.emptyResponse()

    @octoprint.plugin.BlueprintPlugin.route("/createBlurMask", methods=["POST"])
    def apiCreateBlurMask(self):
        return self.doApiRequest(self.API_CONTROLLER.createBlurMask)

    @octoprint.plugin.BlueprintPlugin.route("/getData", methods=["POST"])
    def apiGetData(self):
        self.sendClientData(True)
        return self.API_CONTROLLER.emptyResponse()

    @octoprint.plugin.BlueprintPlugin.route("/defaultEnhancementPreset", methods=["POST"])
    def apiDefaultEnhancementPreset(self):
        return EnhancementPreset(self).getJSON()

    @octoprint.plugin.BlueprintPlugin.route("/getRenderPresetVideoLength", methods=["POST"])
    def apiGetRenderPresetVideoLength(self):
        return self.doApiRequest(self.API_CONTROLLER.getRenderPresetVideoLength)

    @octoprint.plugin.BlueprintPlugin.route("/defaultRenderPreset", methods=["POST"])
    def apiDefaultRenderPreset(self):
        return RenderPreset().getJSON()

    @octoprint.plugin.BlueprintPlugin.route("/delete", methods=["POST"])
    def apiDelete(self):
        self.doApiRequest(self.API_CONTROLLER.delete)
        return self.API_CONTROLLER.emptyResponse()

    @octoprint.plugin.BlueprintPlugin.route("/listPresets", methods=["POST"])
    def apiListPresets(self):
        return self.doApiRequest(self.API_CONTROLLER.listPresets)

    @octoprint.plugin.BlueprintPlugin.route("/render", methods=["POST"])
    def apiRender(self):
        self.doApiRequest(self.API_CONTROLLER.render)
        return self.API_CONTROLLER.emptyResponse()

    @octoprint.plugin.BlueprintPlugin.route("/thumbnail", methods=["GET"])
    def apiThumbnail(self):
        return self.doApiRequest(self.API_CONTROLLER.thumbnail)

    @octoprint.plugin.BlueprintPlugin.route("/maskPreview", methods=["GET"])
    def apiMaskPreview(self):
        return self.doApiRequest(self.API_CONTROLLER.maskPreview)

    @octoprint.plugin.BlueprintPlugin.route("/download", methods=["GET"])
    def apiDownload(self):
        return self.doApiRequest(self.API_CONTROLLER.download)

    @octoprint.plugin.BlueprintPlugin.route("/enhancementPreview", methods=["GET"])
    def apiEnhancementPreview(self):
        return self.doApiRequest(self.API_CONTROLLER.enhancementPreview)

    @octoprint.plugin.BlueprintPlugin.route("/enhancementPreviewSettings", methods=["POST"])
    def apiEnhancementPreviewSettings(self):
        return self.doApiRequest(self.API_CONTROLLER.enhancementPreviewSettings)

    @octoprint.plugin.BlueprintPlugin.route("/listVideoFormats", methods=["POST"])
    def apiListVideoFormats(self):
        return self.doApiRequest(self.API_CONTROLLER.listVideoFormats)

    @octoprint.plugin.BlueprintPlugin.route("/uploadFrameZip", methods=["POST"])
    def apiUploadFrameZip(self):
        self.doApiRequest(self.API_CONTROLLER.uploadFrameZip)
        return self.API_CONTROLLER.emptyResponse()

    @octoprint.plugin.BlueprintPlugin.route("/editQuickSettings", methods=["POST"])
    def apiEditQuickSettings(self):
        self.doApiRequest(self.API_CONTROLLER.editQuickSettings)
        return self.API_CONTROLLER.emptyResponse()

    @octoprint.plugin.BlueprintPlugin.route("/stabilizationEaseFnPreview", methods=["GET"])
    def apiStabilizationEaseFnPreview(self):
        return self.doApiRequest(self.API_CONTROLLER.stabilizationEaseFnPreview)

    @octoprint.plugin.BlueprintPlugin.route("/downloadLog", methods=["GET"])
    def apiDownloadLog(self):
        return self.doApiRequest(self.API_CONTROLLER.downloadLog)

    @octoprint.plugin.BlueprintPlugin.route("/findHomePosition", methods=["POST"])
    def apiFindHomePosition(self):
        return self.doApiRequest(self.API_CONTROLLER.findHomePosition)

    def getPrinter(self):
        return self._printer

    def makeThumbnail(self, img, size=(320, 180)):
        img.thumbnail(size)
        buf = io.BytesIO()
        img.convert('RGB').save(buf, format='JPEG', quality=85)
        img.close()
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
            pluginVersion=self.getPluginVersion(),
            enabled=True,
            ffmpegPath='',
            ffprobePath='',
            webcamType=WebcamType.IMAGE_JPEG.name,
            webcamUrl='',
            webcamPathToCertVerifyFile='',
            webcamPluginId=None,
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
            purgeVideosDays=90,
            stabilization=False,
            stabilizationSettings=StabilizationSettings().getJSON(),
            snapshotInfo=True,
            snapshotInfoFrame=SnapshotInfoFrame.ZOOM_ALL.name,
            renderMultithreading=True
        )

    def get_template_vars(self):
        epRaw = self._settings.get(["enhancementPresets"])
        epList = list(map(lambda x: EnhancementPreset(self, x), epRaw))
        epNew = list(map(lambda x: x.getJSON(), epList))

        rpRaw = self._settings.get(["renderPresets"])
        rpList = list(map(lambda x: RenderPreset(x), rpRaw))
        rpNew = list(map(lambda x: x.getJSON(), rpList))

        stabilizationSettings = StabilizationSettings(self._settings.get(["stabilizationSettings"])).getJSON()

        return dict(
            enabled=self._settings.get(["enabled"]),
            ffmpegPath=self._settings.get(["ffmpegPath"]),
            ffprobePath=self._settings.get(["ffprobePath"]),
            webcamType=self._settings.get(["webcamType"]),
            webcamUrl=self._settings.get(["webcamUrl"]),
            webcamPathToCertVerifyFile=self._settings.get(["webcamPathToCertVerifyFile"]),
            webcamPluginId=self._settings.get(["webcamPluginId"]),
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
            purgeVideosDays=self._settings.get(["purgeVideosDays"]),
            stabilization=self._settings.get(["stabilization"]),
            stabilizationSettings=stabilizationSettings,
            snapshotInfo=self._settings.get(["snapshotInfo"]),
            snapshotInfoFrame=self._settings.get(["snapshotInfoFrame"]),
            renderMultithreading=self._settings.get(["renderMultithreading"])
        )

    def listFrameZips(self):
        files = glob.glob(self._settings.getBaseFolder('timelapse') + '/*.zip')
        frameZips = list(map(lambda x: FrameZip(x, self), files))
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

        videos = list(map(lambda x: Video(x, self, self._settings), files))
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
        configData = dict(
            enabled=self._settings.get(["enabled"]),
            captureMode=CaptureMode[self._settings.get(["captureMode"])].name,
            captureTimerInterval=int(self._settings.get(["captureTimerInterval"])),
            snapshotCommand=self._settings.get(["snapshotCommand"]),
            stabilization=self._settings.get(["stabilization"])
        )
        data = dict(
            config=configData,
            allWebcams=self.WEBCAM_CONTROLLER.getWebcamIdsAndNames(),
            error=self.ERROR,
            isRunning=False,
            isCapturing=False,
            isStabilized=False,
            currentFileSize=0,
            captureMode=None,
            captureTimerInterval=0,
            snapshotCommand=self._settings.get(["snapshotCommand"]),
            snapshotCount=0,
            previewImage=None,
            snapshotInfoImage=None,
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
            data['snapshotInfoImage'] = self.PRINTJOB.SNAPSHOT_INFO_IMAGE
            data['isRunning'] = self.PRINTJOB.RUNNING
            data['isCapturing'] = self.PRINTJOB.isCapturing()
            data['snapshotCount'] = len(self.PRINTJOB.FRAMES)
            data['isStabilized'] = self.PRINTJOB.STABILIZE

        self.CLIENT_CONTROLLER.enqueueData(data, force)

    def getRandomString(self, length):
        return ''.join(random.choice(string.ascii_uppercase + string.digits) for i in range(length))

    def initLogger(self):
        logger = logging.getLogger(__name__)

        try:
            handlerFile = logging.handlers.RotatingFileHandler(self._settings.get_plugin_logfile_path(), maxBytes=8 * 1024 * 1024, backupCount=5)
            handlerFile.setFormatter(logging.Formatter('[%(asctime)s.%(msecs)03d] %(levelname)s: %(message)s', '%Y-%m-%d %H:%M:%S'))
            handlerFile.setLevel(logging.DEBUG)
            logger.addHandler(handlerFile)
        except:
            pass

        try:
            handlerConsole = logging.StreamHandler(sys.stdout)
            handlerConsole.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', '%H:%M:%S'))
            handlerConsole.setLevel(logging.WARNING)
            logger.addHandler(handlerConsole)
        except:
            pass

        logger.setLevel(logging.DEBUG)
        logger.propagate = False

        Log.LOGGER = logger

    def startupInner(self):
        allWebcams = []
        if hasattr(octoprint, 'webcams'):
            # Webcam support from 1.9.0
            allWebcams = octoprint.webcams.get_webcams()
            Log.info('Webcam Plugins are supported', allWebcams)

        self.CACHE_CONTROLLER = CacheController(self, self.get_plugin_data_folder(), self._settings)
        self.WEBCAM_CONTROLLER = WebcamController(self, self.get_plugin_data_folder(), self._settings, allWebcams)
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

        webcamPluginId = self._settings.get(["webcamPluginId"])
        if self.WEBCAM_CONTROLLER.getWebcamByPluginId(webcamPluginId) is None:
            self._settings.set(["webcamPluginId"], None)

        self.updateConstants()
        self.resetPositionTracker()
        self.checkPrerequisites()

    def getPluginVersion(self):
        v = self._plugin_version
        if v is None:
            return 'Unknown'
        return str(v)

    def on_after_startup(self):
        self.PLUGIN_VERSION = self.getPluginVersion()
        self.initLogger()

        Log.info('Timelapse+ is starting...')
        Log.info('Plugin Version: ' + self.PLUGIN_VERSION)

        try:
            self.startupInner()
            Log.info('Startup completed')
        except Exception as err:
            Log.critical('Startup failed', err)

    def updateConstants(self):
        stab = StabilizationSettings(self._settings.get(["stabilizationSettings"]))
        Constants.GCODE_G90_G91_EXTRUDER_OVERWRITE = stab.GCODE_G90_G91_EXTRUDER_OVERWRITE
        Constants.PRINTER_HOME_X = stab.PRINTER_HOME_X
        Constants.PRINTER_HOME_Y = stab.PRINTER_HOME_Y
        Constants.PRINTER_HOME_Z = stab.PRINTER_HOME_Z

    def resetPositionTracker(self):
        Log.debug('Reset Position Tracker')
        self.POSITION_TRACKER = PositionTracker()

    def on_settings_save(self, data):
        Log.debug('Settings were changed')
        ret = super().on_settings_save(data)
        self.updateConstants()
        self.checkPrerequisites()
        return ret

    def checkPrerequisites(self):
        try:
            Log.debug('Checking Prerequisites')
            PrerequisitesController.check(self._settings, self.WEBCAM_CONTROLLER)
            self.ERROR = None
        except Exception as err:
            Log.error('Prerequisites Check failed', err)
            self.ERROR = str(err)

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
        Log.error('Webcam Capture failed', err)
        self.sendClientPopup('error', 'Webcam Capture failed', str(err))

    def isSnapshotCommand(self, command, suffix=None):
        ssCommand = self._settings.get(["snapshotCommand"]).strip()

        if suffix is not None:
            ssCommand += '-' + suffix

        if command is None:
            return False
        if ssCommand is None:
            return False

        c1 = ssCommand.strip().lower()
        c2 = command.strip().lower()

        return c1 == c2

    def atCommand(self, comm, phase, command, parameters, tags=None, *args, **kwargs):
        self.processCommand(command, tags)

    def atAction(self, comm, line, action, *args, **kwargs):
        self.processCommand(action)

    def processCommand(self, cmd, tags=None):
        if self.PRINTJOB is None or not self.PRINTJOB.RUNNING:
            return

        filepos = None
        if tags is not None:
            filepos = ListHelper.extractFileposFromGcodeTag(tags)

        if self.isSnapshotCommand(cmd, Constants.SUFFIX_PRINT_UNSTABLE):
            self.PRINTJOB.doSnapshotUnstable()
        elif self.isSnapshotCommand(cmd, Constants.SUFFIX_PRINT_QUEUED) and self.PRINTJOB.CAPTURE_MODE == CaptureMode.COMMAND:
            self.PRINTJOB.doSnapshot(filepos, True)
        elif self.isSnapshotCommand(cmd) and self.PRINTJOB.CAPTURE_MODE == CaptureMode.COMMAND:
            self.PRINTJOB.doSnapshot(filepos)
        elif self.isSnapshotCommand(cmd, Constants.SUFFIX_PRINT_PAUSE):
            self.printHaltedTo(True)
        elif self.isSnapshotCommand(cmd, Constants.SUFFIX_PRINT_RESUME):
            self.printHaltedTo(False)

    def processGcodeSending(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
        if self.POSITION_TRACKER is not None:
            self.POSITION_TRACKER.consumeGcode(gcode, cmd, tags)

        if self.PRINTJOB is None or not self.PRINTJOB.RUNNING:
            return

    def processGcodeQueuing(self, comm_instance, phase, cmd, cmd_type, gcode, subcode=None, tags=None, *args, **kwargs):
        if self.PRINTJOB is None or not self.PRINTJOB.RUNNING:
            return

        snapshotCommand = self._settings.get(["snapshotCommand"])
        return self.PRINTJOB.gcodeQueuing(gcode, cmd, tags, snapshotCommand)

    def processGcodeReceived(self, comm, line, *args, **kwargs):
        try:
            if self.GCODE_RECEIVED_LISTENER is not None:
                self.GCODE_RECEIVED_LISTENER.process(line)
        finally:
            return line

    def render(self, frameZip, enhancementPreset=None, renderPreset=None, videoFormat=None):
        job = RenderJob(self._basefolder, frameZip, self, self._settings, self.get_plugin_data_folder(), enhancementPreset, renderPreset, videoFormat)
        job.start()
        self.RENDERJOBS.append(job)

    def printStarted(self):
        if not self._settings.get(["enabled"]):
            return

        if self.PRINTJOB is not None and self.PRINTJOB.RUNNING:
            return

        self.POSITION_TRACKER.setRecordingEnabled(True)

        self.checkPrerequisites()
        if self.ERROR is not None and not self._settings.get(["forceCapturing"]):
            self.POSITION_TRACKER.setRecordingEnabled(False)
            return

        Log.info('Starting Print')

        printerFile = self._printer.get_current_job()['file']['path']
        baseName = os.path.splitext(os.path.basename(printerFile))[0]

        gcodeFile = None
        origin = self._printer.get_current_job()['file']['origin']
        if origin == 'local':
            gcodeFile = self._settings.getBaseFolder('uploads') + '/' + printerFile
            if not os.path.isfile(gcodeFile):
                gcodeFile = None

        Log.debug('Gathered Print File Information', {'origin': origin, 'printerFile': printerFile, 'baseName': baseName, 'gcodeFile': gcodeFile})

        id = self.getRandomString(32)
        self.PRINTJOB = PrintJob(id, baseName, self, self._settings, self.get_plugin_data_folder(), self.WEBCAM_CONTROLLER, self._printer, self.POSITION_TRACKER, gcodeFile)
        self.PRINTJOB.start()
        self.sendClientData()

    def printFinished(self, success):
        if self.PRINTJOB is None or not self.PRINTJOB.RUNNING:
            return

        zipFileName = self.PRINTJOB.finish(success)
        self.POSITION_TRACKER.setRecordingEnabled(False)
        self.resetPositionTracker()
        self.sendClientData()

        if self._settings.get(["renderAfterPrint"]):
            if zipFileName != None:
                frameZip = FrameZip(zipFileName, self)
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

    def printHaltedTo(self, val):
        if val != self.PRINTJOB.HALTED:
            self.PRINTJOB.HALTED = val
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
        "octoprint.plugin.softwareupdate.check_config": __plugin_implementation__.getUpdateInformation,
        "octoprint.comm.protocol.gcode.sending": __plugin_implementation__.processGcodeSending,
        "octoprint.comm.protocol.gcode.queuing": __plugin_implementation__.processGcodeQueuing,
        "octoprint.comm.protocol.gcode.received": __plugin_implementation__.processGcodeReceived
    }
