import os
import subprocess

from PIL import Image

from .model.webcamType import WebcamType


class PrerequisitesController:
    @staticmethod
    def check(settings, webcamController, ffmpegPath=None, webcamType=None, webcamUrl=None):
        if ffmpegPath is None:
            ffmpegPath = settings.get(["ffmpegPath"])
        if webcamType is None:
            webcamType = WebcamType[settings.get(["webcamType"])]
        if webcamUrl is None:
            webcamUrl = settings.get(["webcamUrl"])

        if ffmpegPath is None or ffmpegPath.strip() == '':
            raise Exception('FFmpeg Path is not set')

        try:
            cmd = [ffmpegPath, '-version']
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=False)
        except Exception as e:
            raise Exception('Could not find or run FFmpeg :' + str(e))

        if result.returncode != 0:
            raise Exception('FFmpeg returned status code ' + result.returncode)

        ffprobePath = settings.get(["ffprobePath"])
        if ffprobePath is None or ffprobePath.strip() == '':
            raise Exception('FFprobe Path is not set')

        try:
            cmd = [ffprobePath, '-version']
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=False)
        except Exception as e:
            raise Exception('Could not find or run FFprobe: ' + str(e))

        if result.returncode != 0:
            raise Exception('FFprobe returned status code ' + result.returncode)

        if webcamUrl is None or webcamUrl.strip() == '':
            raise Exception('Webcam Snapshot URL is not set')

        try:
            snapshot = webcamController.getSnapshot(ffmpegPath, webcamType, webcamUrl)
        except Exception as e:
            raise Exception('Could not retrieve Webcam Snapshot: ' + str(e))

        try:
            img = Image.open(snapshot)
            imgFormat = img.format
            img.close()
        except:
            raise Exception('Webcam Snapshot URL did not return a valid Image')
        finally:
            if os.path.isfile(snapshot):
                os.remove(snapshot)

        if imgFormat != 'JPEG':
            raise Exception('Webcam Snapshot URL did not return a JPG/JPEG Image')
