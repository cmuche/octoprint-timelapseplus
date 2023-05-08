import glob
import io
import os
import shutil
import subprocess
from io import BytesIO

from PIL import Image

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

    def getSnapshotStreamMp4OrHls(self, path, ffmpegPath, webcamUrl):
        cmd = [ffmpegPath, '-r', '1', '-i', webcamUrl, '-frames:v', '1', '-q:v', '1', '-f', 'image2', '-']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        output, error = proc.communicate()
        if error or proc.returncode != 0:
            raise Exception('Could not capture Webcam: ' + error)
        image = Image.open(BytesIO(output))
        image.save(path, quality=100, subsampling=0)

    def getSnapshotStreamMjpeg(self, path, webcamUrl):
        response = requests.get(webcamUrl, stream=True, timeout=1)
        if response.status_code != 200:
            raise Exception('Webcam Snapshot URL returned HTTP status code ' + str(response.status_code))

        while True:
            chunk = response.raw.read(1024)
            start = chunk.find(b'\xff\xd8')
            if start != -1:
                imageData = chunk[start:]
                while True:
                    chunk = response.raw.read(1024)
                    end = chunk.find(b'\xff\xd9')
                    if end != -1:
                        imageData += chunk[:end + 2]
                        break
                    else:
                        imageData += chunk
                break

        imageBytes = io.BytesIO(imageData)
        image = Image.open(imageBytes)
        image.save(path, 'JPEG', quality=100, subsampling=0)


    def getSnapshotJpeg(self, path, webcamUrl):
        res = requests.get(webcamUrl, stream=True, timeout=1)

        if res.status_code == 200:
            with open(path, 'wb') as f:
                shutil.copyfileobj(res.raw, f)
        else:
            self._logger.error('Could not load image')
            raise Exception('Webcam Snapshot URL returned HTTP status code ' + str(res.status_code))

    def getSnapshot(self):
        ffmpegPath = self._settings.get(["ffmpegPath"])
        webcamUrl = self._settings.get(["webcamUrl"])

        fileName = self.TMP_FOLDER + '/' + self.PARENT.getRandomString(32) + ".jpg"

        try:
            self.getSnapshotJpeg(fileName, webcamUrl)

            if not os.path.isfile(fileName):
                raise Exception('An Error occured during Snapshot Capturing')

            self._logger.info(f'Downloaded Snapshot to {fileName}')
            return fileName
        except Exception as e:
            self.PARENT.errorSnapshot(e)
            raise e
