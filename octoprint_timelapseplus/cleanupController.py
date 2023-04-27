import glob
import os
import shutil
import time

from .model.mask import Mask
from .model.enhancementPreset import EnhancementPreset
from octoprint.util import ResettableTimer


class CleanupController:
    def __init__(self, parent, dataFolder, settings):
        self.PARENT = parent
        self._data_folder = dataFolder
        self._settings = settings

        self.SECONDS_1_HOUR = 60 * 60
        self.SECONDS_5_MINUTES = 5 * 60
        self.SECONDS_1_DAY = 24 * 60 * 60

        self.CRON_TIMER_INTERVAL = self.SECONDS_5_MINUTES

    def init(self):
        self.cleanCapture()
        self.cleanRender()
        self.cleanUnusedMasks()

        self.CRON_TIMER = ResettableTimer(self.CRON_TIMER_INTERVAL, self.onCron)
        self.CRON_TIMER.start()

    def onCron(self):
        self.cleanUnusedMasks()

        self.CRON_TIMER.cancel()
        self.CRON_TIMER = ResettableTimer(self.CRON_TIMER_INTERVAL, self.onCron)
        self.CRON_TIMER.start()

    def fileIsOlderThan(self, filePath, seconds):
        modificationTime = os.path.getmtime(filePath)
        currentTime = time.time()
        timeDiff = currentTime - modificationTime
        return timeDiff > seconds

    def cleanCapture(self):
        folder = self._data_folder + '/capture'
        if not os.path.exists(folder):
            return

        shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)

    def cleanRender(self):
        folder = self._data_folder + '/render'
        if not os.path.exists(folder):
            return

        shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)

    def cleanWebcamTemp(self):
        folder = self._data_folder + '/webcam-tmp'
        if not os.path.exists(folder):
            return

        shutil.rmtree(folder)
        os.makedirs(folder, exist_ok=True)

    def cleanUnusedMasks(self):
        epRaw = self._settings.get(["enhancementPresets"])
        epList = list(map(lambda x: EnhancementPreset(self.PARENT, x), epRaw))

        maskFolder = Mask.getMaskFolder(self._data_folder)
        maskFiles = glob.glob(maskFolder + '/*')

        for mf in maskFiles:
            mfBase = os.path.basename(mf)
            isUsed = False
            for p in epList:
                if p.BLUR_MASK is not None and os.path.basename(p.BLUR_MASK.PATH) == mfBase:
                    isUsed = True
            if not isUsed and self.fileIsOlderThan(mf, self.SECONDS_1_DAY):
                os.remove(mf)
