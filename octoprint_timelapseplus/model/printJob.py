import base64
import io
import json
import os
import shutil
import zipfile
from datetime import datetime
from threading import Thread

from PIL import Image

from octoprint.util import ResettableTimer
from .captureMode import CaptureMode
from .stabilizatonSettings import StabilizationSettings
from ..helpers.positionTracker import PositionTracker
from ..helpers.fileHelper import FileHelper
from ..helpers.stabilizationHelper import StabilizationHelper
from ..helpers.timeHelper import TimeHelper


class PrintJob:
    def __init__(self, id, baseName, parent, logger, settings, dataFolder, webcamController, printer):
        self.PARENT = parent
        self.ID = id
        self.WEBCAM_CONTROLLER = webcamController

        self._settings = settings
        self._logger = logger
        self._printer = printer

        self.STABILIZE = True
        self.POSITION_TRACKER = PositionTracker()

        stabilizationSettings = StabilizationSettings(self._settings.get(["stabilizationSettings"]))
        self.STABILIZATION_HELPER = StabilizationHelper(settings, stabilizationSettings)

        self.METADATA = {'timestamps': {}, 'started': None, 'ended': None, 'success': False, 'baseName': baseName, 'pluginVersion': parent.PLUGIN_VERSION}
        self.BASE_NAME = baseName
        self.CURRENT_INDEX = 1
        self.FOLDER = ''
        self.FOLDER_NAME = ''
        self.FRAMES = []
        self.CAPTURE_THREADS = []
        self.RUNNING = False
        self.PAUSED = False
        self.HALTED = False
        self.CAPTURE_MODE = CaptureMode[self._settings.get(["captureMode"])]
        self.CAPTURE_TIMER_INTERVAL = int(self._settings.get(["captureTimerInterval"]))
        self.CAPTURE_TIMER = ResettableTimer(self.CAPTURE_TIMER_INTERVAL, self.captureTimerTriggered)

        self.PREVIEW_IMAGE = None

        self.createFolder(dataFolder)

    def processGcode(self, gcode, command):
        self.POSITION_TRACKER.consumeGcode(gcode, command)

    def isCapturing(self):
        return self.RUNNING and not self.PAUSED and not self.HALTED

    def createFolder(self, dataFolder):
        self.FOLDER_NAME = self.PARENT.getRandomString(16)
        self.FOLDER = dataFolder + '/capture/' + self.FOLDER_NAME
        os.makedirs(self.FOLDER, exist_ok=True)

    def captureTimerTriggered(self):
        self._logger.info('TIMER TRIGGERED')

        if not self.RUNNING:
            self.CAPTURE_TIMER.cancel()
            return

        self.doSnapshot()

        self.CAPTURE_TIMER.cancel()
        self.CAPTURE_TIMER = ResettableTimer(self.CAPTURE_TIMER_INTERVAL, self.captureTimerTriggered)
        self.CAPTURE_TIMER.start()

    def start(self):
        self.CURRENT_INDEX = 1
        self.FRAMES = []
        self.CAPTURE_THREADS = []
        self.METADATA['started'] = TimeHelper.getUnixTimestamp()
        self.RUNNING = True

        if self.CAPTURE_MODE == CaptureMode.TIMED:
            self.CAPTURE_TIMER.start()

    def getTotalFileSize(self):
        t = 0
        for file in self.FRAMES:
            t += os.path.getsize(file)
        return t

    def finish(self, success):
        self._logger.info('Finished Print!')

        self.METADATA['success'] = success

        if self.CAPTURE_MODE == CaptureMode.TIMED:
            self.CAPTURE_TIMER.cancel()
            self.doSnapshot()

        self.RUNNING = False

        # Wait for all Capture Threads to finish
        self._logger.info('Waiting for Capture Threads...')
        for x in self.CAPTURE_THREADS:
            x.join()

        self.PREVIEW_IMAGE = None
        finishedFiles = self.FRAMES.copy()
        self.FRAMES = []
        self.CAPTURE_THREADS = []

        self.METADATA['ended'] = TimeHelper.getUnixTimestamp()

        if len(finishedFiles) < 1:
            return None

        metadataFile = self.createMetadata()

        self._logger.info('Zipping Frames...')
        self._logger.info(self.FRAMES)

        timePart = datetime.now().strftime("%Y%m%d%H%M%S")
        zipFileName = self._settings.getBaseFolder('timelapse') + '/' + self.BASE_NAME + '_' + timePart + '.zip'
        tmpZipFile = self.FOLDER + '/out.zip'

        compressType = zipfile.ZIP_STORED
        if self._settings.get(["compressFrameZips"]):
            compressType = zipfile.ZIP_DEFLATED

        with zipfile.ZipFile(tmpZipFile, 'w') as zipMe:
            zipMe.write(metadataFile, os.path.basename(metadataFile), compress_type=zipfile.ZIP_STORED)
            for file in finishedFiles:
                baseName = os.path.basename(file)
                zipMe.write(file, baseName, compress_type=compressType)

        shutil.move(tmpZipFile, zipFileName)
        shutil.rmtree(self.FOLDER)
        return zipFileName

    def createMetadata(self):
        mdPath = self.FOLDER + '/' + FileHelper.METADATA_FILE_NAME
        json_object = json.dumps(self.METADATA)
        with open(mdPath, 'w') as mdFile:
            mdFile.write(json_object)
        return mdPath

    def doSnapshot(self):
        if self.STABILIZE:
            self.STABILIZATION_HELPER.stabilizeAndQueueSnapshotRaw(self._printer, self.POSITION_TRACKER)
        else:
            self.doSnapshotUnstable()

    def doSnapshotUnstable(self):
        if self.PAUSED or self.HALTED:
            return

        thread = Thread(target=self.doSnapshotInner, daemon=True)
        self.CAPTURE_THREADS.append(thread)
        thread.start()

    def doSnapshotInner(self):
        ssTime = TimeHelper.getUnixTimestamp()
        snapshotFile = self.WEBCAM_CONTROLLER.getSnapshot()

        fileBaseName = "{:05d}".format(self.CURRENT_INDEX) + ".jpg"
        fileName = self.FOLDER + '/' + fileBaseName

        shutil.move(snapshotFile, fileName)

        self.CURRENT_INDEX += 1
        self.METADATA['timestamps'][fileBaseName] = ssTime
        self.FRAMES.append(fileName)

        self.generatePreviewImage()
        self.PARENT.doneSnapshot()

    def generatePreviewImage(self):
        with open(self.FRAMES[-1], 'rb') as image_file:
            imgBytes = image_file.read()
            img = Image.open(io.BytesIO(imgBytes))
            thumb = self.PARENT.makeThumbnail(img, (640, 360))
            self.PREVIEW_IMAGE = base64.b64encode(thumb)
