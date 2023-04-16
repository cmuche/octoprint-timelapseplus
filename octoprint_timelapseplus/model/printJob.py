import base64
import io
import os
import shutil
import zipfile
from datetime import datetime
from threading import Thread

import requests
from PIL import Image

from .captureMode import CaptureMode
from octoprint.util import ResettableTimer


class PrintJob:
    def __init__(self, id, baseName, parent, logger, settings, dataFolder):
        self.PARENT = parent
        self.ID = id

        self._settings = settings
        self._logger = logger

        self.BASE_NAME = baseName
        self.CURRENT_INDEX = 1
        self.FOLDER = ''
        self.FOLDER_NAME = ''
        self.FRAMES = []
        self.CAPTURE_THREADS = []
        self.RUNNING = False
        self.PAUSED = False
        self.CAPTURE_MODE = CaptureMode[self._settings.get(["captureMode"])]
        self.CAPTURE_TIMER_INTERVAL = int(self._settings.get(["captureTimerInterval"]))
        self.CAPTURE_TIMER = ResettableTimer(self.CAPTURE_TIMER_INTERVAL, self.captureTimerTriggered)

        self.PREVIEW_IMAGE = None

        self.createFolder(dataFolder)

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
        self.RUNNING = True

        if self.CAPTURE_MODE == CaptureMode.TIMED:
            self.CAPTURE_TIMER.start()

    def getTotalFileSize(self):
        t = 0
        for file in self.FRAMES:
            t += os.path.getsize(file)
        return t

    def finish(self):
        self._logger.info('Finished Print!')

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

        if len(finishedFiles) < 1:
            return None

        self._logger.info('Zipping Frames...')
        self._logger.info(self.FRAMES)

        timePart = datetime.now().strftime("%Y%m%d%H%M%S")
        zipFileName = self._settings.getBaseFolder('timelapse') + '/' + self.BASE_NAME + '_' + timePart + '.zip'
        with zipfile.ZipFile(zipFileName, 'w') as zipMe:
            for file in finishedFiles:
                baseName = os.path.basename(file)
                zipMe.write(file, baseName, compress_type=zipfile.ZIP_STORED)

        shutil.rmtree(self.FOLDER)
        return zipFileName

    def doSnapshot(self):
        if self.PAUSED:
            return

        thread = Thread(target=self.doSnapshotInner)
        self.CAPTURE_THREADS.append(thread)
        thread.start()

    def doSnapshotInner(self):
        fileName = self.FOLDER + '/' + "{:05d}".format(self.CURRENT_INDEX) + ".jpg"
        self.CURRENT_INDEX += 1

        res = requests.get(self._settings.global_get(["webcam", "snapshot"]), stream=True)

        if res.status_code == 200:
            with open(fileName, 'wb') as f:
                shutil.copyfileobj(res.raw, f)
            self.FRAMES.append(fileName)
            self._logger.info(f'Downloaded Snapshot to {fileName}')
        else:
            self._logger.error('Could not load image')

        self.generatePreviewImage()
        self.PARENT.doneSnapshot()

    def generatePreviewImage(self):
        with open(self.FRAMES[-1], 'rb') as image_file:
            imgBytes = image_file.read()
            img = Image.open(io.BytesIO(imgBytes))
            thumb = self.PARENT.makeThumbnail(img, (640, 360))
            self.PREVIEW_IMAGE = base64.b64encode(thumb)
