import os
import subprocess

from PIL import Image


class PrerequisitesController:
    @staticmethod
    def check(settings, webcamController):
        ffmpegPath = settings.get(["ffmpegPath"])
        if ffmpegPath is None or ffmpegPath.strip() == '':
            raise Exception('FFmpeg Path is not set')

        try:
            cmd = [ffmpegPath, '-version']
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=False)
        except:
            raise Exception('Could not find or run FFmpeg')

        if result.returncode != 0:
            raise Exception('FFmpeg returned status code ' + result.returncode)


        ffprobePath = settings.get(["ffprobePath"])
        if ffprobePath is None or ffprobePath.strip() == '':
            raise Exception('FFprobe Path is not set')

        try:
            cmd = [ffprobePath, '-version']
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=False)
        except:
            raise Exception('Could not find or run FFprobe')

        if result.returncode != 0:
            raise Exception('FFprobe returned status code ' + result.returncode)


        webcamUrl = settings.get(["webcamUrl"])
        if webcamUrl is None or webcamUrl.strip() == '':
            raise Exception('Webcam Snapshot URL is not set')

        try:
            snapshot = webcamController.getSnapshot()
        except:
            raise Exception('Could not retrieve Webcam Snapshot')

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
