import glob
import os
import shutil

import requests


class WebcamController:
    def __init__(self, parent, logger, dataFolder, settings):
        self.PARENT = parent
        self._logger = logger
        self._settings = settings
        self.TMP_FOLDER = dataFolder + '/webcam-tmp'
        self.prepareFolder()

    def prepareFolder(self):
        os.makedirs(self.TMP_FOLDER, exist_ok=True)
        files = glob.glob(self.TMP_FOLDER + '/*')
        for f in files:
            os.remove(f)

    def getSnapshot(self):
        try:
            res = requests.get(self._settings.get(["webcamUrl"]), stream=True, timeout=1)

            if res.status_code == 200:
                fileName = self.TMP_FOLDER + '/' + self.PARENT.getRandomString(32) + ".jpg"

                with open(fileName, 'wb') as f:
                    shutil.copyfileobj(res.raw, f)

                self._logger.info(f'Downloaded Snapshot to {fileName}')
                return fileName
            else:
                self._logger.error('Could not load image')
                raise Exception('Webcam URL returned status code ' + str(res.status_code))
        except Exception as e:
            self.PARENT.errorSnapshot(e)
            raise e
