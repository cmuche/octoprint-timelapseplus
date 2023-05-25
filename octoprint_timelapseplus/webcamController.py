import glob
import io
import os
import subprocess
import time
from io import BytesIO

import requests
from PIL import Image

from .model.webcamType import WebcamType


class WebcamController:
    def __init__(self, parent, logger, dataFolder, settings):
        self.PARENT = parent
        self._logger = logger
        self._settings = settings
        self.TMP_FOLDER = dataFolder + '/webcam-tmp'
        self.prepareFolder()

        self.TIMEOUT = 2

    def prepareFolder(self):
        os.makedirs(self.TMP_FOLDER, exist_ok=True)
        files = glob.glob(self.TMP_FOLDER + '/*')
        for f in files:
            os.remove(f)

    def getSnapshotStreamMp4OrHls(self, path, ffmpegPath, webcamUrl):
        cmd = [ffmpegPath, '-r', '1', '-i', webcamUrl, '-frames:v', '1', '-q:v', '1', '-f', 'image2', '-']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        output, error = proc.communicate()
        if error:
            raise Exception('Could not capture Webcam: ' + str(error))
        if proc.returncode != 0:
            raise Exception('FFmpeg could not capture Webcam (Return Code ' + str(proc.returncode) + ')')
        image = Image.open(BytesIO(output))
        image.save(path, format='JPEG', quality=100, subsampling=0)

    def getSnapshotStreamMjpeg(self, path, webcamUrl):
        response = requests.get(webcamUrl, stream=True, timeout=self.TIMEOUT)
        if response.status_code != 200:
            raise Exception('Webcam Snapshot URL returned HTTP status code ' + str(response.status_code))

        startTime = time.time()
        try:
            while True:
                if time.time() - startTime >= self.TIMEOUT:
                    raise TimeoutError("Copy operation timed out")

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
        except TimeoutError:
            if os.path.isfile(path):
                os.remove(path)
            raise Exception('Webcam Stream took too long sending Data')

        imageBytes = io.BytesIO(imageData)
        image = Image.open(imageBytes)
        image.save(path, 'JPEG', quality=100, subsampling=0)

    def getSnapshotJpeg(self, path, webcamUrl):
        res = requests.get(webcamUrl, stream=True, timeout=self.TIMEOUT)

        if res.status_code != 200:
            self._logger.error('Could not load image')
            raise Exception('Webcam Snapshot URL returned HTTP status code ' + str(res.status_code))
        else:
            try:
                with open(path, 'wb') as f:
                    WebcamController.copyHttpResponseToFile(res, f, self.TIMEOUT)
            except TimeoutError:
                if os.path.isfile(path):
                    os.remove(path)
                raise Exception('Webcam Snapshot Endpoint took too long sending Data')

    def getSnapshotFromScript(self, scriptPath, fileName):
        if not os.path.isfile(scriptPath):
            raise Exception('The Script File does not exist')

        scriptType = os.path.splitext(scriptPath)[1][1:].lower()

        if scriptType == 'sh':
            proc = subprocess.run(['bash', scriptPath, argument], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        elif scriptType == 'bat':
            proc = subprocess.run([scriptPath, argument], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        elif scriptType == 'ps1':
            proc = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File', scriptPath, argument], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        else:
            raise Exception('Unsupported Webcam Script Type (*.' + scriptType + ')')

        if not os.path.isfile(fileName) or proc.returncode != 0:
            scriptOutput = proc.stdout.decode(errors='ignore')
            raise Exception('Webcam Script did not create the requested Output File.\n\nReturn Code: ' + str(proc.returncode) + '\n\nOutput: ' + str(scriptOutput))

    def getSnapshot(self, ffmpegPath=None, webcamType=None, webcamUrl=None):
        if ffmpegPath is None:
            ffmpegPath = self._settings.get(["ffmpegPath"])
        if webcamType is None:
            webcamType = WebcamType[self._settings.get(["webcamType"])]
        if webcamUrl is None:
            webcamUrl = self._settings.get(["webcamUrl"])

        fileName = self.TMP_FOLDER + '/' + self.PARENT.getRandomString(32) + ".jpg"

        try:
            if webcamType == WebcamType.IMAGE_JPEG:
                self.getSnapshotJpeg(fileName, webcamUrl)
            if webcamType == WebcamType.STREAM_MJPEG:
                self.getSnapshotStreamMjpeg(fileName, webcamUrl)
            if webcamType == WebcamType.STREAM_MP4 or webcamType == WebcamType.STREAM_HLS:
                self.getSnapshotStreamMp4OrHls(fileName, ffmpegPath, webcamUrl)
            if webcamType == WebcamType.SCRIPT:
                self.getSnapshotFromScript(webcamUrl, fileName)

            if not os.path.isfile(fileName):
                raise Exception('An Error occured during Snapshot Capturing')

            self._logger.info(f'Downloaded Snapshot to {fileName}')
            return fileName
        except Exception as e:
            self.PARENT.errorSnapshot(e)
            raise e

    @staticmethod
    def copyHttpResponseToFile(src, dst, timeout, chunkSize=1024):
        startTime = time.time()
        for chunk in src.iter_content(chunk_size=chunkSize):
            if time.time() - startTime >= timeout:
                raise TimeoutError("Copy operation timed out")
            if chunk:
                dst.write(chunk)
            else:
                break
