import os
import re
import subprocess

from PIL import Image

from .helpers.formatHelper import FormatHelper
from .model.webcamType import WebcamType


class PrerequisitesController:
    ENCODERS_TEST_REGEX = '^[ ]*V[VASFXBD\\.]{5} ([a-zA-Z0-9-_]+) [ ]+.*'

    @staticmethod
    def check(settings, webcamController, ffmpegPath=None, ffprobePath=None, webcamType=None, webcamUrl=None):
        if ffmpegPath is None:
            ffmpegPath = settings.get(["ffmpegPath"])
        if ffprobePath is None:
            ffprobePath = settings.get(["ffprobePath"])
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

        PrerequisitesController.checkFfmpegEncoders(ffmpegPath)

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

    @staticmethod
    def checkFfmpegEncoders(ffmpegPath):
        cmd = [ffmpegPath, '-encoders']
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=False)
        outLines = result.stdout.decode().split('\n')
        outLines = [x.replace('\r', '').strip() for x in outLines]
        outLines = [x for x in outLines if x != '']

        encoders = []
        for ol in outLines:
            match = re.search(PrerequisitesController.ENCODERS_TEST_REGEX, ol)
            if not match:
                continue
            encoders += [match.group(1)]

        missingEncoders = []
        videoFormats = FormatHelper.getVideoFormats()
        for vf in videoFormats:
            for vc in vf.getCodecIdsList():
                if vc not in encoders and vc not in missingEncoders:
                    missingEncoders.append(vc)
        if len(missingEncoders) == 1:
            raise Exception('The Encoder \'' + missingEncoders[0] + '\' is not supported by your FFmpeg Version')
        elif len(missingEncoders) > 0:
            raise Exception('The Encoders ' + ', '.join(missingEncoders) + ' are not supported by your FFmpeg Version')
