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
from ..helpers.snapshotInfoRenderer import SnapshotInfoRenderer
from ..log import Log
from ..constants import Constants
from ..helpers.fileHelper import FileHelper
from ..helpers.infillFinder import InfillFinder
from ..helpers.listHelper import ListHelper
from ..helpers.stabilizationHelper import StabilizationHelper
from ..helpers.timeHelper import TimeHelper


class PrintJob:
    def __init__(self, id, baseName, parent, settings, dataFolder, webcamController, printer, positionTracker, gcodeFile):
        self.PARENT = parent
        self.ID = id
        self.WEBCAM_CONTROLLER = webcamController

        self._settings = settings
        self._printer = printer

        self.STABILIZE = self._settings.get(["stabilization"])
        self.POSITION_TRACKER = positionTracker
        self.SNAPSHOT_INFO_RENDERER = SnapshotInfoRenderer(settings)

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
        self.SNAPSHOT_INFO_IMAGE = None

        self.createFolder(dataFolder)

        self.GCODE_FILE = gcodeFile
        infillNotify = self.CAPTURE_MODE == CaptureMode.COMMAND and self.STABILIZE and stabilizationSettings.INFILL_LOOKAHEAD
        self.INFILL_FINDER = InfillFinder(parent, gcodeFile, settings)
        self.INFILL_FINDER.startScanFile(infillNotify)
        self.SNAPSHOT_QUEUED_POSITION = None
        self.LAST_QUEUED_FILEPOS = 0
        self.PRINTER_POS_AT_QUEUING = None
        self.PRINTER_POS_PARKING = None

    def getCurrentPrinterPosition(self):
        return (self.PARENT.POSITION_TRACKER.POS_X, self.PARENT.POSITION_TRACKER.POS_Y, self.PARENT.POSITION_TRACKER.POS_Z)

    def gcodeQueuing(self, gcode, command, tags, snapshotCommand):
        if self.SNAPSHOT_QUEUED_POSITION is None:
            return None

        filepos = ListHelper.extractFileposFromGcodeTag(tags)
        if filepos is None:
            return None

        self.LAST_QUEUED_FILEPOS = filepos

        if filepos < self.SNAPSHOT_QUEUED_POSITION:
            return None

        Log.debug('Executing queued Snapshot')

        self.SNAPSHOT_QUEUED_POSITION = None
        cmd = ['@' + snapshotCommand + '-' + Constants.SUFFIX_PRINT_QUEUED, command]
        return cmd

    def isCapturing(self):
        return self.RUNNING and not self.PAUSED and not self.HALTED

    def createFolder(self, dataFolder):
        self.FOLDER_NAME = self.PARENT.getRandomString(16)
        self.FOLDER = dataFolder + '/capture/' + self.FOLDER_NAME
        os.makedirs(self.FOLDER, exist_ok=True)

    def captureTimerTriggered(self):
        Log.debug('Capture Timer triggered')

        if not self.RUNNING:
            self.CAPTURE_TIMER.cancel()
            return

        self.doSnapshotUnstable()

        self.CAPTURE_TIMER.cancel()
        self.CAPTURE_TIMER = ResettableTimer(self.CAPTURE_TIMER_INTERVAL, self.captureTimerTriggered)
        self.CAPTURE_TIMER.start()

    def start(self):
        Log.info('Starting Print Job', {'id': self.ID})
        Log.debug('Stabilization Settings', self.STABILIZATION_HELPER.STAB.getJSON())

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
        Log.info('Finishing Print Job')

        self.METADATA['success'] = success

        if self.CAPTURE_MODE == CaptureMode.TIMED:
            self.CAPTURE_TIMER.cancel()
            self.doSnapshotUnstable()

        self.RUNNING = False

        # Wait for all Capture Threads to finish
        Log.debug('Waiting for Capture Threads')
        for x in self.CAPTURE_THREADS:
            x.join()

        self.PREVIEW_IMAGE = None
        self.SNAPSHOT_INFO_IMAGE = None

        finishedFiles = self.FRAMES.copy()
        self.FRAMES = []
        self.CAPTURE_THREADS = []

        self.INFILL_FINDER.destroy()
        self.METADATA['ended'] = TimeHelper.getUnixTimestamp()

        if len(finishedFiles) < 1:
            return None

        metadataFile = self.createMetadata()

        Log.info('Zipping Frames...')

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

        Log.info('Created FrameZip', {'file', zipFileName})

        return zipFileName

    def createMetadata(self):
        mdPath = self.FOLDER + '/' + FileHelper.METADATA_FILE_NAME
        json_object = json.dumps(self.METADATA)
        with open(mdPath, 'w') as mdFile:
            mdFile.write(json_object)
        return mdPath

    def doSnapshot(self, filepos=None, isQueued=False):
        if not self.isCapturing():
            return

        Log.info('Triggering Snapshot', {'queued': isQueued, 'filePos': filepos})

        if self.STABILIZE:
            fileposAlreadyQueuedToPrinter = filepos is not None and filepos <= self.LAST_QUEUED_FILEPOS
            canQueue = self.STABILIZATION_HELPER.STAB.INFILL_LOOKAHEAD and \
                       (not fileposAlreadyQueuedToPrinter) and \
                       (not isQueued) and \
                       self.INFILL_FINDER.canQueueSnapshotAt(filepos)

            Log.debug('Snapshot should be stabilized', {'canQueue': canQueue})

            if canQueue:
                self.PRINTER_POS_AT_QUEUING = self.getCurrentPrinterPosition()
                self.SNAPSHOT_QUEUED_POSITION = self.INFILL_FINDER.getNextInfillPosition(filepos)
            else:
                currentSnapshotProgress = 0
                if len(self.INFILL_FINDER.SNAPSHOTS) > 0:
                    currentSnapshotProgress = len(self.FRAMES) / len(self.INFILL_FINDER.SNAPSHOTS)
                try:
                    self.PRINTER_POS_PARKING = self.STABILIZATION_HELPER.stabilizeAndQueueSnapshotRaw(self._printer, self.POSITION_TRACKER, currentSnapshotProgress)
                except Exception as err:
                    Log.warning('Stabilization failed', err)
                    self.PARENT.sendClientPopup('error', 'Stabilization failed', str(err) + '\n\nAn unstable Snapshot will be taken instead.')
                    self.doSnapshotUnstable()
        else:
            self.doSnapshotUnstable()

    def doSnapshotUnstable(self):
        if not self.isCapturing():
            return

        Log.info('Performing unstable Snapshot')

        currentPos = self.getCurrentPrinterPosition()
        queuedPos = self.PRINTER_POS_AT_QUEUING
        parkingPos = self.PRINTER_POS_PARKING
        positionRecording = self.PARENT.POSITION_TRACKER.RECORDING
        self.PARENT.POSITION_TRACKER.resetRecording()
        self.PRINTER_POS_AT_QUEUING = None
        self.PRINTER_POS_PARKING = None

        thread = Thread(target=self.doSnapshotInner, args=(positionRecording, currentPos, queuedPos, parkingPos,), daemon=True)
        self.CAPTURE_THREADS.append(thread)
        thread.start()

    def doSnapshotInner(self, positionRecording, currentPos, queuedPos, parkingPos):
        ssTime = TimeHelper.getUnixTimestamp()
        snapshotFile = self.WEBCAM_CONTROLLER.getSnapshot()

        fileBaseName = "{:05d}".format(self.CURRENT_INDEX) + ".jpg"
        fileName = self.FOLDER + '/' + fileBaseName

        shutil.move(snapshotFile, fileName)

        self.CURRENT_INDEX += 1
        self.METADATA['timestamps'][fileBaseName] = ssTime
        self.FRAMES.append(fileName)

        snapshotInfoImg = self.SNAPSHOT_INFO_RENDERER.render(positionRecording, currentPos, queuedPos, parkingPos)
        self.generateSnapshotInfoImage(snapshotInfoImg)

        self.generatePreviewImage()
        self.PARENT.doneSnapshot()

    def generateSnapshotInfoImage(self, img):
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        img.close()
        byteArr = buf.getvalue()
        self.SNAPSHOT_INFO_IMAGE = base64.b64encode(byteArr)

    def generatePreviewImage(self):
        with open(self.FRAMES[-1], 'rb') as image_file:
            imgBytes = image_file.read()
            img = Image.open(io.BytesIO(imgBytes))
            thumb = self.PARENT.makeThumbnail(img, (640, 360))
            self.PREVIEW_IMAGE = base64.b64encode(thumb)
