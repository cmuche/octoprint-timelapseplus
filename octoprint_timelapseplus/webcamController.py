import glob
import io
import os
import subprocess
import time
from io import BytesIO
import certifi

import requests
from PIL import Image

from .log import Log
from .model.webcamType import WebcamType


class WebcamController:
    def __init__(self, parent, dataFolder, settings, webcams):
        self.PARENT = parent
        self._settings = settings
        self.TMP_FOLDER = dataFolder + '/webcam-tmp'
        self.prepareFolder()
        self.WEBCAMS = webcams

        self.TIMEOUT = 2

    def prepareFolder(self):
        os.makedirs(self.TMP_FOLDER, exist_ok=True)
        files = glob.glob(self.TMP_FOLDER + '/*')
        for f in files:
            os.remove(f)

    def getWebcamByPluginId(self, id):
        return next((x for x in self.WEBCAMS.values() if x.config.name == id), None)

    def getWebcamIdsAndNames(self):
        ret = []
        for k in self.WEBCAMS:
            thisWebcam = dict(id=self.WEBCAMS[k].config.name, name=self.WEBCAMS[k].config.displayName)
            ret.append(thisWebcam)

        return ret

    def getSnapshotStreamMp4OrHls(self, path, ffmpegPath, webcamUrl, webcamPathToCertVerifyFile):
        Log.debug('Getting Snapshot from MP4/HLS Stream', {'stream': webcamUrl, 'SSL CA File': webcamPathToCertVerifyFile})

        cmd = [ffmpegPath, '-r', '1', '-i', webcamUrl, '-frames:v', '1', '-q:v', '1', '-f', 'image2', '-']
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        output, error = proc.communicate()
        if error:
            raise Exception('Could not capture Webcam: ' + str(error))
        if proc.returncode != 0:
            raise Exception('FFmpeg could not capture Webcam (Return Code ' + str(proc.returncode) + ')')
        image = Image.open(BytesIO(output))
        image.save(path, format='JPEG', quality=100, subsampling=0)

    def getSnapshotStreamMjpeg(self, path, webcamUrl, webcamPathToCertVerifyFile):
        Log.debug('Getting Snapshot from MJPEG Stream', {'stream': webcamUrl, 'SSL CA File': webcamPathToCertVerifyFile})

        response = requests.get(webcamUrl, stream=True, timeout=self.TIMEOUT, verify=webcamPathToCertVerifyFile)
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

    def getSnapshotJpeg(self, path, webcamUrl, webcamPathToCertVerifyFile):
        Log.debug('Getting Snapshot from JPEG', {'endpoint': webcamUrl, 'SSL CA File': webcamPathToCertVerifyFile})

        res = requests.get(webcamUrl, stream=True, timeout=self.TIMEOUT, verify=webcamPathToCertVerifyFile)

        if res.status_code != 200:
            Log.error('Could not load image')
            raise Exception('Webcam Snapshot URL returned HTTP status code ' + str(res.status_code))
        else:
            try:
                with open(path, 'wb') as f:
                    WebcamController.copyHttpResponseToFile(res, f, self.TIMEOUT)
            except TimeoutError:
                if os.path.isfile(path):
                    os.remove(path)
                raise Exception('Webcam Snapshot Endpoint took too long sending Data')

    def getSnapshotFromScript(self, scriptPath, fileName, webcamPathToCertVerifyFile):
        Log.debug('Getting Snapshot from Script', {'script': scriptPath, 'SSL CA File': webcamPathToCertVerifyFile})

        if not os.path.isfile(scriptPath):
            raise Exception('The Script File does not exist')

        scriptType = os.path.splitext(scriptPath)[1][1:].lower()
        argument = os.path.abspath(fileName)

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

    def getSnapshotFromPlugin(self, pluginId, fileName, webcamPathToCertVerifyFile):
        Log.debug('Getting Snapshot from Plugin', {'plugin': pluginId})

        if pluginId is None:
            raise Exception('Webcam Plugin is not set')

        webcam = self.getWebcamByPluginId(pluginId)

        if webcam is None:
            raise Exception('Couldn\'t find a Webcam Plugin with the ID \'' + str(pluginId) + '\'')

        webcamName = webcam.config.displayName

        if not webcam.config.canSnapshot:
            raise Exception('The Webcam Plugin \'' + webcamName + '\' doesn\'t support Snapshots')

        try:
            snapshot = webcam.providerPlugin.take_webcam_snapshot(webcam)
        except Exception as ex:
            raise Exception('The Webcam Plugin \'' + webcamName + '\' failed creating a Snapshot: ' + str(ex))

        try:
            with open(fileName, 'wb') as f:
                for chunk in snapshot:
                    if chunk:
                        f.write(chunk)
                        f.flush()
        except Exception as ex:
            raise Exception('The Webcam Plugin \'' + webcamName + '\' didn\'t return a valid Snapshot: ' + str(ex))

    def getSnapshot(self, ffmpegPath=None, webcamType=None, webcamUrl=None, webcamPathToCertVerifyFile=None, pluginId=None):
        if ffmpegPath is None:
            ffmpegPath = self._settings.get(["ffmpegPath"])
        if webcamType is None:
            webcamType = WebcamType[self._settings.get(["webcamType"])]
        if webcamUrl is None:
            webcamUrl = self._settings.get(["webcamUrl"])
        if webcamPathToCertVerifyFile is None:
            webcamPathToCertVerifyFile = self._settings.get(["webcamPathToCertVerifyFile"])
        if pluginId is None:
            pluginId = self._settings.get(["webcamPluginId"])

        fileName = self.TMP_FOLDER + '/' + self.PARENT.getRandomString(32) + ".jpg"

        try:
            if webcamType == WebcamType.IMAGE_JPEG:
                self.getSnapshotJpeg(fileName, webcamUrl, webcamPathToCertVerifyFile)
            if webcamType == WebcamType.STREAM_MJPEG:
                self.getSnapshotStreamMjpeg(fileName, webcamUrl, webcamPathToCertVerifyFile)
            if webcamType == WebcamType.STREAM_MP4 or webcamType == WebcamType.STREAM_HLS:
                self.getSnapshotStreamMp4OrHls(fileName, ffmpegPath, webcamUrl, webcamPathToCertVerifyFile)
            if webcamType == WebcamType.SCRIPT:
                self.getSnapshotFromScript(webcamUrl, fileName, webcamPathToCertVerifyFile)
            if webcamType == WebcamType.PLUGIN:
                self.getSnapshotFromPlugin(pluginId, fileName, webcamPathToCertVerifyFile)

            if not os.path.isfile(fileName):
                raise Exception('An Error occured during Snapshot Capturing')

            Log.info('Downloaded Snapshot', {'file': fileName})
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
