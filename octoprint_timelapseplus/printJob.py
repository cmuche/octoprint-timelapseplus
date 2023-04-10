import os
import shutil
import zipfile
from datetime import datetime
from threading import Thread

import requests


class PrintJob:
    def __init__(self, baseName, parent, logger, settings, dataFolder):
        self.PARENT = parent
        self._settings = settings
        self._logger = logger

        self.BASE_NAME = baseName
        self.CURRENT_INDEX = 1
        self.FOLDER = ''
        self.FOLDER_NAME = ''
        self.FRAMES = []
        self.CAPTURE_THREADS = []
        self.RUNNING = False

        self.createFolder(dataFolder)

    def createFolder(self, dataFolder):
        self.FOLDER_NAME = self.PARENT.getRandomString(16)
        self.FOLDER = dataFolder + '/capture/' + self.FOLDER_NAME
        os.makedirs(self.FOLDER, exist_ok=True)

    def start(self):
        self.CURRENT_INDEX = 1
        self.FRAMES = []
        self.CAPTURE_THREADS = []
        self.RUNNING = True

    def finish(self):
        self._logger.info('Finished Print!')
        self.RUNNING = False

        # Wait for all Capture Threads to finish
        self._logger.info('Waiting for Capture Threads...')
        for x in self.CAPTURE_THREADS:
            x.join()

        finishedFiles = self.FRAMES.copy()
        self.FRAMES = []
        self.CAPTURE_THREADS = []

        if len(finishedFiles) < 1:
            return None

        self._logger.info('Zipping Frames...')
        self._logger.info(self.FRAMES)

        timePart = datetime.now().strftime("%d%m%Y%H%M%S")
        zipFileName = self._settings.getBaseFolder('timelapse') + '/' + self.BASE_NAME + '_' + timePart + '.zip'
        with zipfile.ZipFile(zipFileName, 'w') as zipMe:
            for file in finishedFiles:
                baseName = os.path.basename(file)
                zipMe.write(file, baseName, compress_type=zipfile.ZIP_STORED)

        shutil.rmtree(self.FOLDER)
        return zipFileName

    def doSnapshot(self):
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

        self.PARENT.doneSnapshot()
